"""Standalone CSE-optimized exact signed 9-bit ``a*b + c*d`` circuit."""
from __future__ import annotations

from multiplier.circuit import Circuit

WIDTH = 9
OUT_WIDTH = 19


def _and(a: int, b: int, circuit: Circuit) -> int:
    return circuit.add("AND", a, b)


def _or(a: int, b: int, circuit: Circuit) -> int:
    return circuit.add("OR", a, b)


def _xor(a: int, b: int, circuit: Circuit) -> int:
    return circuit.add("XOR", a, b)


def _not(a: int, circuit: Circuit) -> int:
    return circuit.add("NOT", a)


def _full_adder(a: int, b: int, cin: int, circuit: Circuit) -> tuple[int, int]:
    ab = _xor(a, b, circuit)
    carry_ab = _and(a, b, circuit)
    total = _xor(ab, cin, circuit)
    carry_in = _and(ab, cin, circuit)
    carry = _or(carry_ab, carry_in, circuit)
    return total, carry


def _bit_w(bits: list[int], index: int, zero: int) -> int:
    if index < 0:
        return zero
    if index >= len(bits):
        return bits[-1]
    return bits[index]


def _booth_control(bits: list[int], group: int, zero: int, circuit: Circuit):
    low = _bit_w(bits, 2 * group - 1, zero)
    middle = _bit_w(bits, 2 * group, zero)
    high = _bit_w(bits, 2 * group + 1, zero)
    one = _xor(middle, low, circuit)
    two = _and(_not(one, circuit), _xor(high, middle, circuit), circuit)
    return one, two, high


def _booth_control_sign(bits: list[int], group: int, zero: int, circuit: Circuit):
    low = _bit_w(bits, 2 * group - 1, zero)
    middle = _bit_w(bits, 2 * group, zero)
    return _xor(middle, low, circuit), middle


def _add_products(columns, products, zero, one_const, circuit) -> None:
    groups = (WIDTH + 1) // 2
    for group in range(groups):
        offset = 2 * group
        is_top = offset + WIDTH == OUT_WIDTH - 1
        for multiplicand, multiplier in products:
            if group == groups - 1:
                one, negative = _booth_control_sign(multiplier, group, zero, circuit)
                two = None
            else:
                one, two, negative = _booth_control(multiplier, group, zero, circuit)
            for source in range(WIDTH + 1):
                times_one = _and(_bit_w(multiplicand, source, zero), one, circuit)
                if two is None or source == 0:
                    magnitude = times_one
                else:
                    times_two = _and(
                        _bit_w(multiplicand, source - 1, zero), two, circuit
                    )
                    magnitude = _or(times_one, times_two, circuit)
                bit = _xor(magnitude, negative, circuit)
                if source == WIDTH and not is_top:
                    bit = _not(bit, circuit)
                columns[offset + source].append(bit)
            columns[offset].append(negative)

    compensation = -2 * sum(
        1 << (2 * group + WIDTH)
        for group in range(groups)
        if 2 * group + WIDTH < OUT_WIDTH - 1
    ) & ((1 << OUT_WIDTH) - 1)
    for col in range(OUT_WIDTH):
        if (compensation >> col) & 1:
            columns[col].append(one_const)


def build_circuit() -> Circuit:
    circuit = Circuit(output_width=OUT_WIDTH)
    zero = circuit.add("ZERO")
    one = circuit.add("ONE")
    a = [circuit.add("IN_A") for _ in range(WIDTH)]
    b = [circuit.add("IN_B") for _ in range(WIDTH)]
    c = [circuit.add("IN_C") for _ in range(WIDTH)]
    d = [circuit.add("IN_D") for _ in range(WIDTH)]
    circuit.input_ids = a + b + c + d

    columns = [[] for _ in range(OUT_WIDTH)]
    _add_products(columns, ((a, b), (c, d)), zero, one, circuit)
    for col in range(OUT_WIDTH):
        while len(columns[col]) >= 3:
            x = columns[col].pop()
            y = columns[col].pop()
            z = columns[col].pop()
            total, carry = _full_adder(x, y, z, circuit)
            columns[col].append(total)
            if col + 1 < OUT_WIDTH:
                columns[col + 1].append(carry)

    carry = None
    outputs = []
    for bucket in columns:
        bucket = bucket or [zero]
        if carry is None:
            outputs.append(bucket[0] if len(bucket) == 1 else _xor(bucket[0], bucket[1], circuit))
            if len(bucket) > 1:
                carry = _and(bucket[0], bucket[1], circuit)
        elif len(bucket) == 1:
            outputs.append(_xor(bucket[0], carry, circuit))
            carry = _and(bucket[0], carry, circuit)
        else:
            total, carry = _full_adder(bucket[0], bucket[1], carry, circuit)
            outputs.append(total)
    circuit.output_ids = outputs
    return circuit
