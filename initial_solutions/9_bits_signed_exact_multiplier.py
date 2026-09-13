"""Exact signed 9-bit radix-4 Booth multiplier circuit generator."""
from __future__ import annotations

from multiplier.circuit import Circuit

WIDTH = 9
OUT_WIDTH = 18


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


def _booth_control(
    bits: list[int], group: int, zero: int, circuit: Circuit
) -> tuple[int, int, int]:
    low = _bit_w(bits, 2 * group - 1, zero)
    middle = _bit_w(bits, 2 * group, zero)
    high = _bit_w(bits, 2 * group + 1, zero)
    one = _xor(middle, low, circuit)
    two = _and(_not(one, circuit), _xor(high, middle, circuit), circuit)
    return one, two, high


def _booth_control_sign(
    bits: list[int], group: int, zero: int, circuit: Circuit
) -> tuple[int, int]:
    low = _bit_w(bits, 2 * group - 1, zero)
    middle = _bit_w(bits, 2 * group, zero)
    return _xor(middle, low, circuit), middle


def build_circuit() -> Circuit:
    circuit = Circuit()
    zero = circuit.add("ZERO")
    one_const = circuit.add("ONE")
    a_bits = [circuit.add("IN_A") for _ in range(WIDTH)]
    b_bits = [circuit.add("IN_B") for _ in range(WIDTH)]
    circuit.input_ids = a_bits + b_bits

    columns: list[list[int]] = [[] for _ in range(OUT_WIDTH)]
    num_groups = (WIDTH + 1) // 2
    last_group = num_groups - 1

    # Booth partial products with sign-bit inversion instead of sign extension.
    for group in range(num_groups):
        offset = 2 * group
        sign_col = offset + WIDTH
        is_top = sign_col == OUT_WIDTH - 1
        if group == last_group:
            one, negative = _booth_control_sign(b_bits, group, zero, circuit)
            for source in range(WIDTH + 1):
                bit = _xor(
                    _and(_bit_w(a_bits, source, zero), one, circuit),
                    negative,
                    circuit,
                )
                if source == WIDTH and not is_top:
                    bit = _not(bit, circuit)
                columns[offset + source].append(bit)
        else:
            one, two, negative = _booth_control(b_bits, group, zero, circuit)
            for source in range(WIDTH + 1):
                times_one = _and(_bit_w(a_bits, source, zero), one, circuit)
                if source > 0:
                    times_two = _and(_bit_w(a_bits, source - 1, zero), two, circuit)
                    magnitude = _or(times_one, times_two, circuit)
                else:
                    magnitude = times_one
                bit = _xor(magnitude, negative, circuit)
                if source == WIDTH and not is_top:
                    bit = _not(bit, circuit)
                columns[offset + source].append(bit)
        columns[offset].append(negative)

    compensation = -sum(
        1 << (2 * group + WIDTH)
        for group in range(num_groups)
        if 2 * group + WIDTH < OUT_WIDTH - 1
    ) & ((1 << OUT_WIDTH) - 1)
    for col in range(OUT_WIDTH):
        if (compensation >> col) & 1:
            columns[col].append(one_const)

    # Wallace carry-save compression.
    for col in range(OUT_WIDTH):
        while len(columns[col]) >= 3:
            x = columns[col].pop()
            y = columns[col].pop()
            z = columns[col].pop()
            total, carry = _full_adder(x, y, z, circuit)
            columns[col].append(total)
            if col + 1 < OUT_WIDTH:
                columns[col + 1].append(carry)

    # Final carry-propagate addition of the two surviving rows.
    carry: int | None = None
    output_ids: list[int] = []
    for bucket in columns:
        if not bucket:
            bucket = [zero]
        if carry is None:
            if len(bucket) == 1:
                output_ids.append(bucket[0])
            else:
                output_ids.append(_xor(bucket[0], bucket[1], circuit))
                carry = _and(bucket[0], bucket[1], circuit)
        elif len(bucket) == 1:
            output_ids.append(_xor(bucket[0], carry, circuit))
            carry = _and(bucket[0], carry, circuit)
        else:
            total, carry = _full_adder(bucket[0], bucket[1], carry, circuit)
            output_ids.append(total)

    circuit.output_ids = output_ids
    return circuit
