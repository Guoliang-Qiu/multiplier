"""Standalone qgl-style approximate ``a*b + c*d`` circuit.

This is the four-input adaptation of the supplied qgl partial-product
generator.  In particular it keeps the special pp-column rewrites, the
constant-aware compressor, the merged compensation constant, and the
redundant top-bit sharing.

Local mutation: carry-preserving low-column truncation.  The parent placed
one ``total`` bit at column 4 and four partial-product bits at column 5 for
each product; those ten low bits (worth at most 288 raw units) were reduced
by the general compressor all the way down to the outputs.  The mutation
removes every partial-product bit below column 6 and replaces them with a
small dedicated carry tree that recovers *exactly* the carry the dropped
region injects into column 6 (floor of the dropped value over 64).  The
residual below column 6 (at most 48 raw units, well under half of the Q4.7
quantum of 128) is discarded, so the Q4.7 ``evm_db`` is essentially unchanged
while the low-column compression logic and its ripple carries are eliminated.
"""
from __future__ import annotations

from multiplier.circuit import Circuit

WIDTH = 9
OUT_WIDTH = 18
OUT_TOTAL = 19
TRUNC_COL = 6
COMP_COLS = (10, 11, 13, 15, 18)
ROUND_COLS: tuple[int, ...] = ()


def _and(c, a, b): return c.add("AND", a, b)
def _or(c, a, b): return c.add("OR", a, b)
def _xor(c, a, b): return c.add("XOR", a, b)
def _not(c, a): return c.add("NOT", a)


def _fa(c, a, b, cin):
    ab = _xor(c, a, b)
    return _xor(c, ab, cin), _or(c, _and(c, a, b), _and(c, ab, cin))


def _add3(c, x, y, z, zero, one):
    consts = [n for n in (x, y, z) if n in (zero, one)]
    reals = [n for n in (x, y, z) if n not in (zero, one)]
    if not consts: return _fa(c, x, y, z)
    if len(consts) == 1:
        a, b = reals
        if one in consts: return _not(c, _xor(c, a, b)), _or(c, a, b)
        return _xor(c, a, b), _and(c, a, b)
    if len(consts) == 2:
        a = reals[0]
        if zero in consts and one in consts: return _not(c, a), a
        if one in consts: return a, one
        return a, zero
    n = consts.count(one)
    return (one if n == 1 else zero), (one if n > 1 else zero)


def _bit(bits, index, zero):
    if index < 0: return zero
    return bits[index] if index < len(bits) else bits[-1]


def _qsub(q, step, zero):
    if step == 0: return q[1], q[0], zero
    if step == 1: return q[3], q[2], q[1]
    if step == 2: return q[5], q[4], q[3]
    if step == 3: return q[7], q[6], q[5]
    return q[8], q[8], q[7]


def _product_columns(c, q, m, zero, one_const, cut):
    columns = [[] for _ in range(OUT_WIDTH)]
    pp_0_4 = pp_1_2 = common = pp_2_and = None

    def place(col, node):
        if col >= cut: columns[col].append(node)

    for step in range((WIDTH + 1) // 2):
        h, middle, low = _qsub(q, step, zero)
        if step == 0:
            one = q[0]
            two = _and(c, _not(c, one), q[1])
            negative = q[1]
        elif step == 4:
            one = _and(c, _not(c, middle), low)
            two = zero
            negative = _and(c, middle, _not(c, low))
        else:
            one = _xor(c, middle, low)
            two = _and(c, _not(c, one), _xor(c, h, middle))
            negative = _and(c, h, _not(c, _and(c, middle, low)))

        q_width = 9 if step == 4 else 10
        xors = []
        if two != zero:
            xors = [_xor(c, q[2 * step + 1], _bit(m, k, zero)) for k in range(9)]

        def get_xor(k): return xors[min(k, len(xors) - 1)]

        if step >= 3:
            if two == zero:
                m0 = _bit(m, 0, zero)
                value = _or(c, _and(c, one, m0), _and(c, negative, _not(c, m0)))
            else:
                value = _or(c, _and(c, one, get_xor(0)), _and(c, two, q[2 * step + 1]))
            place(2 * step, value)
            place(2 * step, negative)

        if step == 0:
            pp_0_4 = _or(c, q[1], q[0])
            place(5, _or(c, _and(c, one, get_xor(5)), _and(c, two, _not(c, m[4]))))
        elif step == 1:
            pp_1_2 = _or(c, one, two)
            place(5, _or(c, _and(c, one, get_xor(3)), _and(c, two, get_xor(2))))
        elif step == 2:
            place(5, _or(c, _and(c, one, get_xor(1)),
                         _and(c, two, _or(c, q[5], m[0]))))
            common = _and(c, _or(c, one, two), _and(c, q[5], _not(c, m[0])))
            pp_2_and = _and(c, one, m[0])

        for k in range(max(1, 6 - step * 2), q_width):
            if two == zero:
                mk = _bit(m, k, zero)
                value = _or(c, _and(c, one, mk), _and(c, negative, _not(c, mk)))
            else:
                value = _or(c, _and(c, one, get_xor(k)), _and(c, two, get_xor(k - 1)))
            if k == q_width - 1: value = _not(c, value)
            place(2 * step + k, value)

    ab = _and(c, pp_0_4, pp_1_2)
    carry = _or(c, common, ab)
    total = _and(c, _or(c, common, _or(c, _not(c, ab), pp_2_and)),
                 _or(c, pp_0_4, pp_1_2))
    place(4, total)
    place(5, carry)
    return columns


def _carry_into_trunc_col(c, col4, col5):
    """Recover the exact carry the dropped low columns inject into TRUNC_COL.

    ``col4`` holds the two weight-16 bits and ``col5`` the eight weight-32
    bits removed from both products.  Their total is ``16*n4 + 32*n5``; the
    value crossing into column 6 is ``floor((n4 + 2*n5) / 4)``, i.e. the
    carry-out of the weight-32 pile after folding the weight-16 pair into it.
    The parity bits remaining below column 6 are discarded on purpose.
    Returns the list of carry bits, each of column-6 weight.
    """
    pair = _and(c, col4[0], col4[1])          # both weight-16 bits set -> one weight-32 carry
    pile = list(col5) + [pair]                # nine bits of weight 32
    sums = []
    carries = []
    for i in range(0, len(pile), 3):
        total, carry = _fa(c, pile[i], pile[i + 1], pile[i + 2])
        sums.append(total)
        carries.append(carry)
    # Final 3:2 stage: only the carry is needed; the weight-32 parity bit
    # (the dropped region's value modulo 64) is intentionally not computed.
    s01 = _xor(c, sums[0], sums[1])
    carries.append(_or(c, _and(c, sums[0], sums[1]), _and(c, s01, sums[2])))
    return carries


def build_circuit():
    c = Circuit(output_width=OUT_TOTAL)
    zero, one = c.add("ZERO"), c.add("ONE")
    a = [c.add("IN_A") for _ in range(WIDTH)]
    b = [c.add("IN_B") for _ in range(WIDTH)]
    x = [c.add("IN_C") for _ in range(WIDTH)]
    d = [c.add("IN_D") for _ in range(WIDTH)]
    c.input_ids = a + b + x + d
    columns = [[] for _ in range(OUT_TOTAL)]
    col4, col5 = [], []
    for left, right in ((a, b), (x, d)):
        product = _product_columns(c, right, left, zero, one, 0)
        for col in range(OUT_WIDTH):
            if col >= TRUNC_COL:
                columns[col].extend(product[col])
            elif col == 4:
                col4.extend(product[col])
            elif col == 5:
                col5.extend(product[col])
    # Local approximation: drop the low partial-product columns and inject
    # only their exact carry into the truncation boundary column.
    columns[TRUNC_COL].extend(_carry_into_trunc_col(c, col4, col5))
    for col in COMP_COLS + ROUND_COLS: columns[col].append(one)

    for col in range(OUT_TOTAL):
        while len(columns[col]) >= 3:
            total, carry = _add3(c, columns[col].pop(), columns[col].pop(), columns[col].pop(), zero, one)
            columns[col].append(total)
            if col + 1 < OUT_TOTAL: columns[col + 1].append(carry)

    carry = None
    outputs = []
    for bucket in columns:
        bucket = bucket or [zero]
        if carry is None:
            outputs.append(bucket[0] if len(bucket) == 1 else _xor(c, bucket[0], bucket[1]))
            if len(bucket) > 1: carry = _and(c, bucket[0], bucket[1])
        elif len(bucket) == 1 and bucket[0] == zero:
            outputs.append(carry); carry = zero
        elif len(bucket) == 1 and bucket[0] == one:
            outputs.append(_not(c, carry))
        elif len(bucket) == 1:
            outputs.append(_xor(c, bucket[0], carry)); carry = _and(c, bucket[0], carry)
        else:
            total, carry = _add3(c, bucket[0], bucket[1], carry, zero, one)
            outputs.append(total)
    c.output_ids = outputs[:18] + [outputs[17]]
    return c
