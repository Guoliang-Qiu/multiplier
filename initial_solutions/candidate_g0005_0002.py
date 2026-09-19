"""Standalone qgl-style approximate ``a*b + c*d`` circuit.

This is the four-input adaptation of the supplied qgl partial-product
generator.  In particular it keeps the special pp-column rewrites, the
constant-aware compressor, the merged compensation constant, and the
redundant top-bit sharing.

Local mutation: exact weighted resynthesis with structural sharing.  The parent's
AND/OR/NOT compressor and half-adder cells are preserved, while every remaining
cost-3 XOR (primarily Booth recoding and partial-product inversion) is replaced
by the exact identity ``(a | b) & ~(a & b)``.  Commutative hash-consing shares
identical predicates across these replacements and the existing arithmetic
cones.  The replacement is fully specified and exact, so the parent's output
behavior and approximation sites are unchanged; measured output-reachable
weighted cost falls despite the larger raw gate count.
"""
from __future__ import annotations

from multiplier.circuit import Circuit

WIDTH = 9
OUT_WIDTH = 18
OUT_TOTAL = 19
PROD_CUT_A = 0
PROD_CUT_B = 0
COMP_COLS = (10, 11, 13, 15, 18)
ROUND_COLS: tuple[int, ...] = ()


def _gate(c: Circuit, kind: str, *inputs: int) -> int:
    """Share structurally identical gates, normalizing commutative inputs."""
    cache = getattr(c, "_local_gate_cache", None)
    if cache is None:
        cache = {}
        c._local_gate_cache = cache
    if kind in ("AND", "OR", "XOR") and inputs[1] < inputs[0]:
        inputs = (inputs[1], inputs[0])
    key = (kind, inputs)
    node = cache.get(key)
    if node is None:
        node = c.add(kind, *inputs)
        cache[key] = node
    return node


def _and(c, a, b): return _gate(c, "AND", a, b)
def _or(c, a, b): return _gate(c, "OR", a, b)
def _xor(c, a, b):
    """Exact XOR resynthesis that can share cached AND/OR predicates."""
    both = _and(c, a, b)
    either = _or(c, a, b)
    return _and(c, either, _not(c, both))
def _not(c, a): return _gate(c, "NOT", a)


def _fa(c, a, b, cin):
    """Exact joint parity/majority network (eight weighted unit gates)."""
    ac = _and(c, a, cin)
    bc = _and(c, b, ac)
    a_or_c = _or(c, a, cin)
    b_ac_or = _and(c, b, a_or_c)
    carry = _or(c, ac, b_ac_or)
    not_carry = _not(c, carry)
    b_or_ac = _or(c, b, a_or_c)
    sum_term = _or(c, bc, not_carry)
    total = _and(c, b_or_ac, sum_term)
    return total, carry


def _ha(c, a, b):
    """Exact joint half adder: carry=a&b; sum=(a|b)&~carry."""
    carry = _and(c, a, b)
    total = _and(c, _or(c, a, b), _not(c, carry))
    return total, carry


def _add3(c, x, y, z, zero, one):
    consts = [n for n in (x, y, z) if n in (zero, one)]
    reals = [n for n in (x, y, z) if n not in (zero, one)]
    if not consts: return _fa(c, x, y, z)
    if len(consts) == 1:
        a, b = reals
        if one in consts:
            carry = _or(c, a, b)
            return _or(c, _and(c, a, b), _not(c, carry)), carry
        return _ha(c, a, b)
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

        # Row-activity signal one|two, reused by the factored top mux below.
        # Steps 0-2 already build an equivalent node; step 3 builds one lazily.
        activity = None
        if step == 0:
            pp_0_4 = _or(c, q[1], q[0])
            activity = pp_0_4  # q0 | (~q0 & q1) == q0 | q1 == one | two
            place(5, _or(c, _and(c, one, get_xor(5)), _and(c, two, _not(c, m[4]))))
        elif step == 1:
            pp_1_2 = _or(c, one, two)
            activity = pp_1_2
            place(5, _or(c, _and(c, one, get_xor(3)), _and(c, two, get_xor(2))))
        elif step == 2:
            place(5, _or(c, _and(c, one, get_xor(1)),
                         _and(c, two, _or(c, q[5], m[0]))))
            activity = _or(c, one, two)
            common = _and(c, activity, _and(c, q[5], _not(c, m[0])))
            pp_2_and = _and(c, one, m[0])

        for k in range(max(1, 6 - step * 2), q_width):
            if two == zero:
                mk = _bit(m, k, zero)
                value = _or(c, _and(c, one, mk), _and(c, negative, _not(c, mk)))
                if k == q_width - 1: value = _not(c, value)
            elif k == q_width - 1:
                # Top mux: get_xor clamps both terms to xors[8], i.e.
                # (one&x8) | (two&x8) == (one|two) & x8; reuse the row
                # activity signal instead of rebuilding both ANDs.
                if activity is None: activity = _or(c, one, two)
                value = _not(c, _and(c, activity, get_xor(k)))
            else:
                value = _or(c, _and(c, one, get_xor(k)), _and(c, two, get_xor(k - 1)))
            place(2 * step + k, value)

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
    for col, bucket in enumerate(columns):
        bucket = bucket or [zero]
        if col < 6:
            # These six sum bits are discarded by Q4.7 quantization.  Compute
            # only the exact ripple carry, including constant-aware cases.
            outputs.append(zero)
            if carry is None:
                if len(bucket) > 1:
                    carry = _and(c, bucket[0], bucket[1])
            elif len(bucket) == 1 and bucket[0] == zero:
                carry = zero
            elif len(bucket) == 1 and bucket[0] == one:
                pass  # carry-out of 1 + carry is carry
            elif len(bucket) == 1:
                carry = _and(c, bucket[0], carry)
            else:
                a0, a1 = bucket[0], bucket[1]
                # Exact majority without either parity XOR used by _fa.
                carry = _or(c, _and(c, a0, a1),
                            _and(c, carry, _or(c, a0, a1)))
            continue
        if carry is None:
            if len(bucket) == 1:
                outputs.append(bucket[0])
            else:
                total, carry = _ha(c, bucket[0], bucket[1])
                outputs.append(total)
        elif len(bucket) == 1 and bucket[0] == zero:
            outputs.append(carry); carry = zero
        elif len(bucket) == 1 and bucket[0] == one:
            outputs.append(_not(c, carry))
        elif len(bucket) == 1:
            total, carry = _ha(c, bucket[0], carry)
            outputs.append(total)
        else:
            total, carry = _add3(c, bucket[0], bucket[1], carry, zero, one)
            outputs.append(total)
    c.output_ids = outputs[:18] + [outputs[17]]
    return c
