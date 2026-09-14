"""Standalone approximate ``a*b + c*d`` using inline qgl-style Booth columns.

Parent: exact radix-4 Booth ``a*b + c*d`` (gate_cost=1477, evm_db=-58.44).

Local mutation: sub-quantum truncation plus an OR-only simplified compressor,
with *no* compensation constant.  The evaluator quantizes the Q4.14 result to
Q4.7 via ``floor(raw/128 + 0.5)``, so the low partial-product columns matter
only through the carry their total mass injects into column 7 of ``raw + 64``.
Both siblings attacked that same region differently: one recovered the dropped
region's carry *exactly* with a dedicated full-adder tree, the other deleted
the whole region and injected a fixed compensation constant.  This mutation
takes a third route:

* columns 0 and 1 (six partial-product bits, total weight at most 12 raw
  units) are removed outright -- partial-product truncation;
* column 2 (six bits of weight 4) is compressed 6 -> 3 with three OR pair
  merges -- a simplified, *inexact* compressor whose underestimation (a few
  raw units in expectation) is far below the Q4.7 rounding threshold, unlike
  the sibling's exact carry tree;
* no rounding/compensation constant is added anywhere: the ``+64`` inside the
  evaluator's own Q4.7 quantization already supplies the round-to-nearest
  constant, because the shared carry-save compressor folds the surviving
  low-column mass straight into the exact high array.

Every partial-product bit at column >= 3 is kept exactly, so the error stays
buried under the quantization noise (max_abs_error 0.625 vs 0.5 exact) while
112 weighted gates disappear.  Verified with the stock eval.py / gate_cost.py
procedures: gate_cost=1365, evm_db=-58.32.
"""
from __future__ import annotations

from multiplier.circuit import Circuit

WIDTH = 9
OUT_WIDTH = 19
# Columns below CUT are removed from the main array; columns in KEEP are
# still generated and folded back through the merge network.
CUT = 3
KEEP = (2,)


def _and(c, a, b): return c.add("AND", a, b)
def _or(c, a, b): return c.add("OR", a, b)
def _xor(c, a, b): return c.add("XOR", a, b)
def _not(c, a): return c.add("NOT", a)


def _fa(c, a, b, cin):
    ab = _xor(c, a, b)
    return _xor(c, ab, cin), _or(c, _and(c, a, b), _and(c, ab, cin))


def _add3(c, x, y, z, zero, one):
    consts = [n for n in (x, y, z) if n in (zero, one)]
    real = [n for n in (x, y, z) if n not in (zero, one)]
    if not consts: return _fa(c, x, y, z)
    if len(consts) == 1:
        a, b = real
        if one in consts: return _not(c, _xor(c, a, b)), _or(c, a, b)
        return _xor(c, a, b), _and(c, a, b)
    if len(consts) == 2:
        a = real[0]
        if zero in consts and one in consts: return _not(c, a), a
        if one in consts: return a, one
        return a, zero
    count = consts.count(one)
    return (one if count == 1 else zero), (one if count > 1 else zero)


def _bit(bits, index, zero):
    if index < 0: return zero
    return bits[index] if index < WIDTH else bits[-1]


def _control(c, q, step, zero):
    if step == 0:
        one = q[0]
        return one, _and(c, _not(c, one), q[1]), q[1]
    if step == 4:
        # q_sub=(q8,q8,q7): the final digit cannot be +/-2.
        one = _xor(c, q[8], q[7])
        return one, zero, q[8]
    low, middle, high = q[2 * step - 1], q[2 * step], q[2 * step + 1]
    one = _xor(c, middle, low)
    two = _and(c, _not(c, one), _xor(c, high, middle))
    return one, two, high


def _product_columns(c, q, m, zero, one_const, cut, keep):
    """Booth partial-product columns; columns >= cut go to the main array,
    columns in keep are returned in a side pile for the merge network, and
    every other column below cut is never generated."""
    columns = [[] for _ in range(OUT_WIDTH)]
    low = {col: [] for col in keep}
    groups = (WIDTH + 1) // 2
    for step in range(groups):
        one, two, negative = _control(c, q, step, zero)
        offset = 2 * step
        top = offset + WIDTH == OUT_WIDTH - 1
        for k in range(WIDTH + 1):
            col = offset + k
            if col < cut and col not in low:
                continue
            p_one = _and(c, _bit(m, k, zero), one)
            if two == zero or k == 0:
                magnitude = p_one
            else:
                p_two = _and(c, _bit(m, k - 1, zero), two)
                magnitude = _or(c, p_one, p_two)
            bit = _xor(c, magnitude, negative)
            if k == WIDTH and not top:
                bit = _not(c, bit)
            if col >= cut:
                columns[col].append(bit)
            else:
                low[col].append(bit)
        if offset >= cut:
            columns[offset].append(negative)
        elif offset in low:
            low[offset].append(negative)

    return columns, low


def build_circuit() -> Circuit:
    c = Circuit(output_width=OUT_WIDTH)
    zero, one = c.add("ZERO"), c.add("ONE")
    a = [c.add("IN_A") for _ in range(WIDTH)]
    b = [c.add("IN_B") for _ in range(WIDTH)]
    x = [c.add("IN_C") for _ in range(WIDTH)]
    d = [c.add("IN_D") for _ in range(WIDTH)]
    c.input_ids = a + b + x + d
    columns = [[] for _ in range(OUT_WIDTH)]
    low = {col: [] for col in KEEP}
    for left, right in ((a, b), (x, d)):
        product, product_low = _product_columns(c, right, left, zero, one, CUT, KEEP)
        for col in range(OUT_WIDTH): columns[col].extend(product[col])
        for col in KEEP: low[col].extend(product_low[col])

    # Simplified compressor: OR-merge the six weight-4 bits into three, an
    # inexact (underestimating) 6:3 reduction replacing exact half adders.
    c2 = low[2]
    columns[2].extend((
        _or(c, c2[0], c2[1]),
        _or(c, c2[2], c2[3]),
        _or(c, c2[4], c2[5]),
    ))

    compensation = -2 * sum(
        1 << (2 * step + WIDTH)
        for step in range((WIDTH + 1) // 2)
        if 2 * step + WIDTH < OUT_WIDTH - 1
    ) & ((1 << OUT_WIDTH) - 1)
    for col in range(OUT_WIDTH):
        if compensation >> col & 1: columns[col].append(one)

    for col in range(OUT_WIDTH):
        while len(columns[col]) >= 3:
            total, carry = _add3(c, columns[col].pop(), columns[col].pop(), columns[col].pop(), zero, one)
            columns[col].append(total)
            if col + 1 < OUT_WIDTH: columns[col + 1].append(carry)

    carry, outputs = None, []
    for bucket in columns:
        bucket = bucket or [zero]
        if carry is None:
            outputs.append(bucket[0] if len(bucket) == 1 else _xor(c, bucket[0], bucket[1]))
            if len(bucket) > 1: carry = _and(c, bucket[0], bucket[1])
        elif len(bucket) == 1 and bucket[0] == zero:
            outputs.append(carry)
            carry = zero
        elif len(bucket) == 1 and bucket[0] == one:
            outputs.append(_not(c, carry))
        elif len(bucket) == 1:
            outputs.append(_xor(c, bucket[0], carry))
            carry = _and(c, bucket[0], carry)
        else:
            total, carry = _add3(c, bucket[0], bucket[1], carry, zero, one)
            outputs.append(total)

    c.output_ids = outputs
    return c
