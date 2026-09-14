"""Standalone qgl-style approximate ``a*b + c*d`` circuit.

Gate-level crossover of ``candidate_g0001_0005`` (x) ``candidate_g0001_0004``.
Both parents share the same four-input adaptation of the supplied qgl
partial-product generator (special pp-column rewrites, constant-aware
compressor, merged compensation constant, redundant top-bit sharing), so the
child is assembled directly from inherited, mutually compatible subgraphs:

* From parent 0004 (``PROD_CUT_A = 0``): the exact ``a*b`` low-column
  region - the column-4/5 special pp rewrites and the shared top-bit carry
  recovery stay intact, so the ``a*b`` product injects no dropped mass and
  the circuit result remains on the fine 16-unit grid where the
  evaluator's round-to-nearest (``floor(raw/128 + 0.5)``) keeps working.
* From parent 0005 (``PROD_CUT_B = 7``): the aggressively truncated
  ``c*d`` product - the whole sub-quantum region below column 7 (one
  weight-16 ``total`` bit, four weight-32 bits, five weight-64 bits) is
  removed, including 0005's structural gene that skips the step-3 row LSB
  pair and raises the partial-product loop floor so removed bits are never
  built.  All low-column generation, compression and ripple-carry logic of
  that region disappears.
* Shared genes (identical in both parents): the modified-Booth row
  encoders, ``COMP_COLS = (10, 11, 13, 15, 18)`` sign-extension
  compensation, the constant-aware 3:2 compressor tree, the final
  ripple-carry adder, and the duplicated top output bit.

The compensation constant is a blend of the parents' ROUND_COLS genes:
0004 contributes its column-6 ONE, 0005's column-8 ONE is shifted down to
column 7 because only one product is now truncated, and 0005's column-4
ONE is not inherited (the exact ``a*b`` ``total`` bit occupies column 4).
Only the ``c*d`` product drops mass here: ``D_B = 16*n4 + 32*n5 + 64*n6``.
With K = 192 the measured raw bias was +9.3 units, so a free column-3 ONE
(columns 0-3 are empty buckets; the ONE simply hardwires output bit 3,
exactly like parent 0005's free column-4 ONE) raises K to 200 = 128 + 64 +
8, recentring the raw bias to +1.3 units (+0.010 real) at zero gate cost.
K sweeps over {192, 196, 200, 204} leave evm_db unchanged to 4 decimals
(the Q4.7 quantization absorbs sub-grid shifts), so the best-centred K
wins the tie.

The (cut_A, cut_B) = (0, 7) recombination is the missing corner of the
parents' {0, 6} x {6, 7} truncation design space, complementing parent
0004 (0, 6), parent 0005 (6, 7) and the both-cut-6 sibling (6, 6).

Verified with the stock eval.py / gate_cost.py procedures:
gate_cost=1054, evm_db=-50.062, max_abs_error=3.17, bias=+0.010.
Bitwise inheritance check: with c=d=0 the child matches parent 0004 plus
its compensation delta; with a=b=0 it matches parent 0005 plus its
compensation delta - both parental subgraphs are preserved intact.
"""
from __future__ import annotations

from multiplier.circuit import Circuit

WIDTH = 9
OUT_WIDTH = 18
OUT_TOTAL = 19
# Crossover configuration: a*b inherits parent 0004's exact low-column
# region (no truncation) while c*d inherits parent 0005's aggressive cut
# below column 7 (sub-quantum partial-product removal).
PROD_CUT_A = 0
PROD_CUT_B = 7
COMP_COLS = (10, 11, 13, 15, 18)
# Blended statistical compensation for the sub-quantum mass removed from
# c*d only: K = 200 = 128 + 64 + 8 raw units (ONE leaves at columns 3, 6
# and 7) ~= E[D_B] (~201 measured via the K=192 raw bias), recentring the
# residual error to ~zero mean while the exact a*b product keeps the
# result on the fine 16-unit grid.  The column-3 ONE lands in an empty
# bucket and hardwires output bit 3, so it costs no gates.
ROUND_COLS: tuple[int, ...] = (3, 6, 7)


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
