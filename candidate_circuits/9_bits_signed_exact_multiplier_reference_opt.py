"""Standalone exact ``a*b + c*d`` using optimized qgl Booth partial products."""
from __future__ import annotations

from multiplier.circuit import Circuit

WIDTH = 9
OUT_WIDTH = 19


def _and(c, a, b): return c.add("AND", a, b)
def _or(c, a, b): return c.add("OR", a, b)
def _xor(c, a, b): return c.add("XOR", a, b)
def _not(c, a): return c.add("NOT", a)


def _fa(c, a, b, cin):
    ab = _xor(c, a, b)
    return _xor(c, ab, cin), _or(c, _and(c, a, b), _and(c, ab, cin))


def _bit(bits, index, zero):
    if index < 0: return zero
    return bits[index] if index < WIDTH else bits[-1]


def _product_columns(circuit, q_bits, m_bits, zero, one_const):
    columns = [[] for _ in range(OUT_WIDTH)]
    groups = (WIDTH + 1) // 2
    for step in range(groups):
        low = _bit(q_bits, 2 * step - 1, zero)
        middle = _bit(q_bits, 2 * step, zero)
        high = _bit(q_bits, 2 * step + 1, zero)
        if step == 0:
            one = q_bits[0]
            two = _and(circuit, _not(circuit, one), q_bits[1])
            negative = q_bits[1]
        elif step == groups - 1:
            # The top digit is only 0, +1, or -1.  No two-times branch exists.
            one = _xor(circuit, middle, low)
            two = zero
            negative = middle
        else:
            one = _xor(circuit, middle, low)
            two = _and(circuit, _not(circuit, one), _xor(circuit, high, middle))
            negative = high
        offset = 2 * step
        top = offset + WIDTH == OUT_WIDTH - 1
        for k in range(WIDTH + 1):
            p1 = _and(circuit, _bit(m_bits, k, zero), one)
            if two == zero or k == 0:
                magnitude = p1
            else:
                magnitude = _or(
                    circuit,
                    p1,
                    _and(circuit, _bit(m_bits, k - 1, zero), two),
                )
            bit = _xor(circuit, magnitude, negative)
            if k == WIDTH and not top:
                bit = _not(circuit, bit)
            columns[offset + k].append(bit)
        columns[offset].append(negative)
    compensation = -sum(
        1 << (2 * step + WIDTH)
        for step in range(groups)
        if 2 * step + WIDTH < OUT_WIDTH - 1
    ) & ((1 << OUT_WIDTH) - 1)
    for col in range(OUT_WIDTH):
        if compensation >> col & 1: columns[col].append(one_const)
    return columns


def build_circuit() -> Circuit:
    circuit = Circuit(output_width=OUT_WIDTH)
    zero, one = circuit.add("ZERO"), circuit.add("ONE")
    a = [circuit.add("IN_A") for _ in range(WIDTH)]
    b = [circuit.add("IN_B") for _ in range(WIDTH)]
    c = [circuit.add("IN_C") for _ in range(WIDTH)]
    d = [circuit.add("IN_D") for _ in range(WIDTH)]
    circuit.input_ids = a + b + c + d
    columns = [[] for _ in range(OUT_WIDTH)]
    for x, y in ((a, b), (c, d)):
        product = _product_columns(circuit, y, x, zero, one)
        for col in range(OUT_WIDTH): columns[col].extend(product[col])
    for col in range(OUT_WIDTH):
        while len(columns[col]) >= 3:
            x, y, z = columns[col].pop(), columns[col].pop(), columns[col].pop()
            total, carry = _fa(circuit, x, y, z)
            columns[col].append(total)
            if col + 1 < OUT_WIDTH: columns[col + 1].append(carry)
    carry, outputs = None, []
    for bucket in columns:
        bucket = bucket or [zero]
        if carry is None:
            outputs.append(bucket[0] if len(bucket) == 1 else _xor(circuit, bucket[0], bucket[1]))
            if len(bucket) > 1: carry = _and(circuit, bucket[0], bucket[1])
        elif len(bucket) == 1:
            outputs.append(_xor(circuit, bucket[0], carry))
            carry = _and(circuit, bucket[0], carry)
        else:
            total, carry = _fa(circuit, bucket[0], bucket[1], carry)
            outputs.append(total)
    circuit.output_ids = outputs
    return circuit
