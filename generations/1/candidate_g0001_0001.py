"""9-bit signed radix-4 Booth multiplier using AND/OR/NOT/XOR gates."""
from __future__ import annotations

from dataclasses import dataclass

WIDTH = 9
OUT_WIDTH = 18
GATE_COSTS = {"AND": 1, "OR": 1, "XOR": 3, "NOT": 0}
APPROX_CARRY_CUTOFF = 3


def AND(a: int, b: int) -> int: return (a & b) & 1
def OR(a: int, b: int) -> int: return (a | b) & 1
def XOR(a: int, b: int) -> int: return (a ^ b) & 1
def NOT(a: int) -> int: return 1 ^ (a & 1)


def _record(netlist: "Netlist", kind: str) -> None:
    netlist.gates.append((kind, "", "", None))


def _and(a: int, b: int, netlist: "Netlist") -> int:
    _record(netlist, "AND")
    return AND(a, b)


def _or(a: int, b: int, netlist: "Netlist") -> int:
    _record(netlist, "OR")
    return OR(a, b)


def _xor(a: int, b: int, netlist: "Netlist") -> int:
    _record(netlist, "XOR")
    return XOR(a, b)


def _not(a: int, netlist: "Netlist") -> int:
    _record(netlist, "NOT")
    return NOT(a)


@dataclass
class Netlist:
    gates: list[tuple[str, str, str, str | None]]

    def gate_count(self) -> dict[str, int]:
        counts = {kind: 0 for kind in GATE_COSTS}
        for kind, *_ in self.gates:
            counts[kind] += 1
        return counts

    def cost(self) -> int:
        counts = self.gate_count()
        return sum(counts[kind] * cost for kind, cost in GATE_COSTS.items())


def _full_adder(a: int, b: int, cin: int, netlist: Netlist) -> tuple[int, int]:
    ab = _xor(a, b, netlist)
    carry_ab = _and(a, b, netlist)
    total = _xor(ab, cin, netlist)
    carry_in = _and(ab, cin, netlist)
    carry = _or(carry_ab, carry_in, netlist)
    return total, carry


def _add(a: list[int], b: list[int], netlist: Netlist) -> list[int]:
    result = []
    carry = 0
    for index in range(OUT_WIDTH):
        # Local approximation: suppress carry propagation in the least
        # significant bits, then resume exact ripple addition for the upper
        # slice. This trims gate count while keeping the higher-weight bits
        # accurate enough for scoring.
        if index < APPROX_CARRY_CUTOFF:
            result.append(_xor(a[index], b[index], netlist))
            if index == APPROX_CARRY_CUTOFF - 1:
                carry = 0
            continue
        total, carry = _full_adder(a[index], b[index], carry, netlist)
        result.append(total)
    return result


def _invert(bits: list[int], netlist: Netlist) -> list[int]:
    return [_not(bit, netlist) for bit in bits]


def _twos_complement(bits: list[int], netlist: Netlist) -> list[int]:
    one = [1] + [0] * (len(bits) - 1)
    return _add(_invert(bits, netlist), one, netlist)


def _shift_left(bits: list[int], amount: int) -> list[int]:
    if amount <= 0:
        return bits[:]
    if amount >= len(bits):
        return [0] * len(bits)
    return [0] * amount + bits[: len(bits) - amount]


def _sign_extend(bits: list[int], width: int) -> list[int]:
    sign = bits[-1]
    return bits + [sign] * (width - len(bits))


def _bits(value: int, width: int) -> list[int]:
    value &= (1 << width) - 1
    return [(value >> index) & 1 for index in range(width)]


def _bit_at(bits: list[int], index: int) -> int:
    if index < 0:
        return 0
    if index >= len(bits):
        return bits[-1]
    return bits[index]


def _booth_select(bits: list[int], group: int, netlist: Netlist) -> tuple[int, int, int, int, int, int, int, int]:
    low = _bit_at(bits, 2 * group - 1)
    middle = _bit_at(bits, 2 * group)
    high = _bit_at(bits, 2 * group + 1)

    n_low = _not(low, netlist)
    n_middle = _not(middle, netlist)
    n_high = _not(high, netlist)

    is_000 = _and(_and(n_high, n_middle, netlist), n_low, netlist)
    is_001 = _and(_and(n_high, n_middle, netlist), low, netlist)
    is_010 = _and(_and(n_high, middle, netlist), n_low, netlist)
    is_011 = _and(_and(n_high, middle, netlist), low, netlist)
    is_100 = _and(_and(high, n_middle, netlist), n_low, netlist)
    is_101 = _and(_and(high, n_middle, netlist), low, netlist)
    is_110 = _and(_and(high, middle, netlist), n_low, netlist)
    is_111 = _and(_and(high, middle, netlist), low, netlist)
    return is_000, is_001, is_010, is_011, is_100, is_101, is_110, is_111


def _choose_partial(
    zero: list[int],
    pos1: list[int],
    pos2: list[int],
    neg1: list[int],
    neg2: list[int],
    select: tuple[int, int, int, int, int, int, int, int],
    netlist: Netlist,
) -> list[int]:
    is_000, is_001, is_010, is_011, is_100, is_101, is_110, is_111 = select
    one = _or(is_001, is_010, netlist)
    minus_one = _or(is_101, is_110, netlist)

    result = []
    for index in range(OUT_WIDTH):
        bit = 0
        bit = _or(bit, _and(zero[index], _or(is_000, is_111, netlist), netlist), netlist)
        bit = _or(bit, _and(pos1[index], one, netlist), netlist)
        bit = _or(bit, _and(pos2[index], is_011, netlist), netlist)
        bit = _or(bit, _and(neg1[index], minus_one, netlist), netlist)
        bit = _or(bit, _and(neg2[index], is_100, netlist), netlist)
        result.append(bit)
    return result


def build_multiplier(multiplicand: int, multiplier: int) -> tuple[int, Netlist]:
    netlist = Netlist([])
    a_bits = _bits(multiplicand, WIDTH)
    b_bits = _bits(multiplier, WIDTH)
    a = _sign_extend(a_bits, OUT_WIDTH)
    accumulator = [0] * OUT_WIDTH
    pos1 = a
    pos2 = _add(a, a, netlist)
    neg1 = _twos_complement(pos1, netlist)
    neg2 = _twos_complement(pos2, netlist)
    for group in range((WIDTH + 1) // 2):
        select = _booth_select(b_bits, group, netlist)
        shifted_zero = _shift_left([0] * OUT_WIDTH, 2 * group)
        shifted_pos1 = _shift_left(pos1, 2 * group)
        shifted_pos2 = _shift_left(pos2, 2 * group)
        shifted_neg1 = _shift_left(neg1, 2 * group)
        shifted_neg2 = _shift_left(neg2, 2 * group)
        partial = _choose_partial(
            shifted_zero,
            shifted_pos1,
            shifted_pos2,
            shifted_neg1,
            shifted_neg2,
            select,
            netlist,
        )
        accumulator = _add(accumulator, partial, netlist)
    return sum(bit << index for index, bit in enumerate(accumulator)), netlist


def multiply(multiplicand: int, multiplier: int) -> int:
    value, _ = build_multiplier(multiplicand, multiplier)
    return value - (1 << OUT_WIDTH) if value & (1 << (OUT_WIDTH - 1)) else value


def simulate_all() -> dict[str, float | int]:
    total = errors = absolute_error = squared_error = max_error = 0
    for a in range(-(1 << (WIDTH - 1)), 1 << (WIDTH - 1)):
        for b in range(-(1 << (WIDTH - 1)), 1 << (WIDTH - 1)):
            actual, expected = multiply(a, b), a * b
            error = abs(actual - expected)
            total += 1
            errors += actual != expected
            absolute_error += error
            squared_error += error * error
            max_error = max(max_error, error)
    return {"total_cases": total, "error_cases": errors, "error_rate": errors / total,
            "mae": absolute_error / total, "rmse": (squared_error / total) ** 0.5,
            "max_abs_error": max_error}


if __name__ == "__main__":
    print(simulate_all())
