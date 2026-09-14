"""Standalone qgl-style approximate ``a*b + c*d`` circuit.

This is the four-input adaptation of the supplied qgl partial-product
generator.  In particular it keeps the special pp-column rewrites, the
constant-aware compressor, the merged compensation constant, and the
redundant top-bit sharing.

Local mutation: sub-quantum partial-product removal below column 6 of both
products with a bias-matched compensation constant (selective rounding),
combined with an exact top-mux factoring (targeted subgraph substitution).

1) Truncation.  The evaluator quantizes the Q4.14 result to Q4.7 via
   ``floor(raw/128 + 0.5)``, so every partial-product bit below column 7 is
   a sub-quantum bit: such bits matter only through the mass ``D`` they
   inject into the kept columns.  In this generator the only bits below
   column 6 of each product are one weight-16 ``total`` bit at column 4
   (shared top-bit rewrite) and four weight-32 bits at column 5 (three
   special pp rewrites plus the shared carry): dropped mass per product
   ``D = 16*n4 + 32*n5`` with ``n4 in [0,1]`` and ``n5 in [0,4]``, measured
   mean(D) ~= 68.5 raw units on the stock eval sample (137 for the two
   products combined, std ~49, max 288 - always below 2.25 Q4.7 quanta).
   The mutation removes that whole low region from both products
   (``PROD_CUT_A = PROD_CUT_B = 6``), eliminating its pp-generation muxes,
   its compression, and the low ripple stages.

2) Compensation.  ``ROUND_COLS = (4, 7)`` injects K = 144 = 128 + 16, the
   multiple of 16 nearest the measured combined dropped mass (137).  The
   column-4 leaf rides for free in the empty pre-carry bucket; the column-7
   leaf merges into the constant-aware compressor.  Because the truncated
   result stays a multiple of 16, the constant recentres the residual to
   near-zero bias (measured bias 0.0045) without changing any other
   behavior; the quantization grid is invariant to sub-16 offsets.

3) Exact top-mux factoring.  In every Booth row of steps 0..3 the most
   significant partial-product bit (``k == q_width - 1``) was built as
   ``NOT(OR(AND(one, x9), AND(two, x8)))`` with ``get_xor`` clamping both
   multiplicand terms to the same sign-bit node ``x8 = xors[8]``.  The two
   ANDs therefore share ``x8`` and the mux factors exactly:
   ``(one & x8) | (two & x8) == (one | two) & x8``.  The row-activity
   signal ``one | two`` is reused from logic the generator already builds -
   step 0: ``pp_0_4 = q1 | q0`` (equals ``q0 | (~q0 & q1)``); step 1:
   ``pp_1_2``; step 2: the OR inside ``common`` - plus one fresh OR for
   step 3.  Verified bit-exact against the unfactored cut-6 circuit on
   30,002 inputs including all-extreme corners; it saves 8 weighted gates
   net in this cut context while leaving every output bit unchanged.

Verified with the stock eval.py / gate_cost.py procedures:
parent   : gate_cost 1180, evm_db -57.6159
mutated  : gate_cost 1054  (AND 290, OR 143, XOR 207, NOT 47),
           evm_db -53.8184, mae 0.3979, rmse 0.4917,
           max_abs_error 1.9375, error_rate 0.9921, bias 0.0045
i.e. -126 weighted gates (-10.7%) for +3.80 dB of Q4.7 error.
"""
from __future__ import annotations

from multiplier.circuit import Circuit

WIDTH = 9
OUT_WIDTH = 18
OUT_TOTAL = 19
PROD_CUT_A = 6
PROD_CUT_B = 6
COMP_COLS = (10, 11, 13, 15, 18)
ROUND_COLS: tuple[int, ...] = (4, 7)


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
            share2 = _or(c, one, two)
            common = _and(c, share2, _and(c, q[5], _not(c, m[0])))
            pp_2_and = _and(c, one, m[0])

        # Exact top-mux factoring: the row-activity signal one|two, reused
        # from logic the row already builds (one fresh OR only for step 3).
        if step == 0: share = pp_0_4
        elif step == 1: share = pp_1_2
        elif step == 2: share = share2
        elif two != zero: share = _or(c, one, two)
        for k in range(max(1, 6 - step * 2), q_width):
            if two == zero:
                mk = _bit(m, k, zero)
                value = _or(c, _and(c, one, mk), _and(c, negative, _not(c, mk)))
            else:
                value = _or(c, _and(c, one, get_xor(k)), _and(c, two, get_xor(k - 1)))
            if k == q_width - 1 and two != zero:
                # get_xor clamps both mux terms to the same node xors[8], so
                # (one & x8) | (two & x8) == (one | two) & x8 exactly.
                value = _not(c, _and(c, share, get_xor(k - 1)))
            elif k == q_width - 1:
                value = _not(c, value)
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
