"""Standalone exact signed 9-bit radix-4 Booth ``a*b + c*d`` circuit."""
from __future__ import annotations

from multiplier.circuit import Circuit

WIDTH = 9
OUT_WIDTH = 19


def _and(a, b, c): return c.add("AND", a, b)
def _or(a, b, c): return c.add("OR", a, b)
def _xor(a, b, c): return c.add("XOR", a, b)
def _not(a, c): return c.add("NOT", a)


def _fa(a, b, cin, c):
    ab = _xor(a, b, c)
    return _xor(ab, cin, c), _or(_and(a, b, c), _and(ab, cin, c), c)


def _bit(bits, index, zero):
    if index < 0: return zero
    return bits[index] if index < WIDTH else bits[-1]


def _regular(columns, x, y, group, zero, circuit):
    low = _bit(y, 2 * group - 1, zero)
    middle = _bit(y, 2 * group, zero)
    high = _bit(y, 2 * group + 1, zero)
    one = _xor(middle, low, circuit)
    two = _and(_not(one, circuit), _xor(high, middle, circuit), circuit)
    offset = 2 * group
    for source in range(WIDTH + 1):
        p = _and(_bit(x, source, zero), one, circuit)
        if source:
            p = _or(p, _and(_bit(x, source - 1, zero), two, circuit), circuit)
        p = _xor(p, high, circuit)
        if source == WIDTH and offset + WIDTH != OUT_WIDTH - 1:
            p = _not(p, circuit)
        columns[offset + source].append(p)
    columns[offset].append(high)


def _top(columns, x, y, circuit):
    one = _xor(y[8], y[7], circuit)
    for source in range(WIDTH):
        p = _xor(_and(x[source], one, circuit), y[8], circuit)
        columns[8 + source].append(p)
    sign = _xor(_and(x[8], one, circuit), y[8], circuit)
    columns[17].append(_not(sign, circuit))
    columns[8].append(y[8])


def build_circuit():
    circuit = Circuit(output_width=OUT_WIDTH)
    zero, one = circuit.add("ZERO"), circuit.add("ONE")
    a = [circuit.add("IN_A") for _ in range(WIDTH)]
    b = [circuit.add("IN_B") for _ in range(WIDTH)]
    c = [circuit.add("IN_C") for _ in range(WIDTH)]
    d = [circuit.add("IN_D") for _ in range(WIDTH)]
    circuit.input_ids = a + b + c + d
    columns = [[] for _ in range(OUT_WIDTH)]
    for x, y in ((a, b), (c, d)):
        for group in range(4): _regular(columns, x, y, group, zero, circuit)
        _top(columns, x, y, circuit)
    compensation = -2 * sum(1 << (2 * group + WIDTH) for group in range(5)
                             if 2 * group + WIDTH < OUT_WIDTH - 1) & ((1 << OUT_WIDTH) - 1)
    for col in range(OUT_WIDTH):
        if compensation >> col & 1: columns[col].append(one)
    for col in range(OUT_WIDTH):
        while len(columns[col]) >= 3:
            x, y, z = columns[col].pop(), columns[col].pop(), columns[col].pop()
            total, carry = _fa(x, y, z, circuit)
            columns[col].append(total)
            if col + 1 < OUT_WIDTH: columns[col + 1].append(carry)
    carry, outputs = None, []
    for bucket in columns:
        bucket = bucket or [zero]
        if carry is None:
            outputs.append(bucket[0] if len(bucket) == 1 else _xor(bucket[0], bucket[1], circuit))
            if len(bucket) > 1: carry = _and(bucket[0], bucket[1], circuit)
        elif len(bucket) == 1:
            outputs.append(_xor(bucket[0], carry, circuit)); carry = _and(bucket[0], carry, circuit)
        else:
            total, carry = _fa(bucket[0], bucket[1], carry, circuit); outputs.append(total)
    circuit.output_ids = outputs
    return circuit
