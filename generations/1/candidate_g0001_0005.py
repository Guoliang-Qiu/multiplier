"""Standalone qgl-style approximate ``a*b + c*d`` circuit.

This is the four-input adaptation of the supplied qgl partial-product
generator.  In particular it keeps the special pp-column rewrites, the
constant-aware compressor, the merged compensation constant, and the
redundant top-bit sharing.

Local mutation: asymmetric sub-quantum partial-product removal with a
dyadic compensation constant (selective rounding).  The evaluator
quantizes the Q4.14 result to Q4.7 via ``floor(raw/128 + 0.5)``, so every
partial-product bit below column 7 is a sub-quantum bit: such bits matter
only through the mass ``D`` they inject into the kept columns.  In this
generator the sub-quantum region of one product holds one weight-16
``total`` bit at column 4, four weight-32 bits at column 5, and five
weight-64 bits at column 6.  The weight-64 column-6 bits still carry real
signal (their pile reaches 320 raw units = 2.5 Q4.7 quanta), while the
column-4/5 pile is shallow (at most 144 raw units per product).

The mutation therefore truncates the two products at different depths:
the ``a*b`` product is cut below column 6 (``PROD_CUT_A = 6``, dropping
``D_A = 16*n4 + 32*n5``, measured mean ~68.5 raw units on the stock eval
sample) and the ``c*d`` product is cut below column 7
(``PROD_CUT_B = 7``, dropping ``D_B = D_A + 64*n6``, measured mean
~193.5).  A single static compensation constant K = 272 = 256 + 16
(``ROUND_COLS = (4, 8)``) - the dyadic value nearest the measured total
dropped mass (~262) plus the parent's residual bias (+7.5) - recentres
the error to ~zero mean (measured bias -0.019).  The column-4 ONE lands
in a fully empty bucket and simply hardwires output bit 4, so it adds no
gates at all.  All low-column generation, compression and ripple-carry
logic of the removed region disappears.

Verified with the stock eval.py / gate_cost.py procedures:
gate_cost=994, evm_db=-49.588, max_abs_error=3.17, bias=-0.019 - a new
operating point on the Pareto gap between the sibling points
(935 / -47.87 dB, both products cut below column 7) and
(1062 / -53.82 dB, both products cut below column 6).
"""
from __future__ import annotations

from multiplier.circuit import Circuit

WIDTH = 9
OUT_WIDTH = 18
OUT_TOTAL = 19
# Asymmetric sub-quantum truncation: keep the weight-64 column-6 pile of
# the a*b product (real signal) but remove it from the c*d product.
PROD_CUT_A = 6
PROD_CUT_B = 7
COMP_COLS = (10, 11, 13, 15, 18)
# Statistical compensation for the removed sub-quantum mass: K = 272 raw
# units (ONE leaves at columns 4 and 8) ~= E[D_A + D_B] (~262) + parent
# bias (~7.5), recentring the residual error to ~zero mean.
ROUND_COLS: tuple[int, ...] = (4, 8)


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

        # The row LSB pair only feeds column 2*step (6 or 8); skip it when
        # the cut removes that column (cut == 7 drops the step-3 pair).
        if step >= 3 and 2 * step >= cut:
            if two == zero:
                m0 = _bit(m, 0, zero)
                value = _or(c, _and(c, one, m0), _and(c, negative, _not(c, m0)))
            else:
                value = _or(c, _and(c, one, get_xor(0)), _and(c, two, q[2 * step + 1]))
            place(2 * step, value)
            place(2 * step, negative)

        # The column-4/5 specials and the shared top-bit rewrite below only
        # feed columns 4 and 5; skip building them when the cut removes them.
        if cut <= 5:
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

        # Raise the loop floor so partial-product bits below the cut are
        # never built (they would be dropped by place() anyway).
        for k in range(max(1, 6 - step * 2, cut - 2 * step), q_width):
            if two == zero:
                mk = _bit(m, k, zero)
                value = _or(c, _and(c, one, mk), _and(c, negative, _not(c, mk)))
            else:
                value = _or(c, _and(c, one, get_xor(k)), _and(c, two, get_xor(k - 1)))
            if k == q_width - 1: value = _not(c, value)
            place(2 * step + k, value)

    if cut <= 5:
        ab = _and(c, pp_0_4, pp_1_2)
        carry = _or(c, common, ab)
        total = _and(c, _or(c, common, _or(c, _not(c, ab), pp_2_and)),
                     _or(c, pp_0_4, pp_1_2))
        place(4, total)
        place(5, carry)
    return columns


def build_circuit():
    c = Circuit(output_width=OUT_TOTAL)
    zero, one = c.add("ZERO"), c.add("ONE")
    a = [c.add("IN_A") for _ in range(WIDTH)]
    b = [c.add("IN_B") for _ in range(WIDTH)]
    x = [c.add("IN_C") for _ in range(WIDTH)]
    d = [c.add("IN_D") for _ in range(WIDTH)]
    c.input_ids = a + b + x + d
    columns = [[] for _ in range(OUT_TOTAL)]
    for left, right, cut in ((a, b, PROD_CUT_A), (x, d, PROD_CUT_B)):
        product = _product_columns(c, right, left, zero, one, cut)
        for col in range(OUT_WIDTH): columns[col].extend(product[col])
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
