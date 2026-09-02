"""9-bit signed radix-4 Booth multiplier using AND/OR/NOT/XOR gates.

The multiplier is built as a directed acyclic graph (DAG) of logic nodes.
Each gate node references the ids of its input nodes; the operand bits and
constants are the leaves, and the accumulator bits are the roots. The same
DAG can be re-evaluated for any input pair via ``Netlist.evaluate``.
"""
from __future__ import annotations

from dataclasses import dataclass, field

WIDTH = 9
OUT_WIDTH = 18
GATE_COSTS = {"AND": 1, "OR": 1, "XOR": 3, "NOT": 0}


def AND(a: int, b: int) -> int: return a & b
def OR(a: int, b: int) -> int: return a | b
def XOR(a: int, b: int) -> int: return a ^ b
def NOT(a: int) -> int: return a ^ 1


@dataclass
class Node:
    kind: str
    inputs: tuple[int, ...] = ()
    value: int = 0


@dataclass
class Netlist:
    nodes: list[Node] = field(default_factory=list)
    a_ids: list[int] = field(default_factory=list)
    b_ids: list[int] = field(default_factory=list)
    output_ids: list[int] = field(default_factory=list)

    def _add(self, kind: str, inputs: tuple[int, ...], value: int) -> int:
        self.nodes.append(Node(kind, inputs, value))
        return len(self.nodes) - 1

    def add_leaf(self, kind: str, value: int) -> int:
        return self._add(kind, (), value)

    def gate_count(self) -> dict[str, int]:
        counts = {kind: 0 for kind in GATE_COSTS}
        for node in self.nodes:
            if node.kind in counts:
                counts[node.kind] += 1
        return counts

    def cost(self) -> int:
        counts = self.gate_count()
        return sum(counts[kind] * cost for kind, cost in GATE_COSTS.items())

    def evaluate(self, multiplicand: int, multiplier: int) -> int:
        """Re-simulate the existing DAG for a new input pair."""
        for i in range(WIDTH):
            self.nodes[self.a_ids[i]].value = (multiplicand >> i) & 1
            self.nodes[self.b_ids[i]].value = (multiplier >> i) & 1
        for node in self.nodes:
            if node.kind == "AND":
                node.value = AND(self.nodes[node.inputs[0]].value,
                                 self.nodes[node.inputs[1]].value)
            elif node.kind == "OR":
                node.value = OR(self.nodes[node.inputs[0]].value,
                                self.nodes[node.inputs[1]].value)
            elif node.kind == "XOR":
                node.value = XOR(self.nodes[node.inputs[0]].value,
                                 self.nodes[node.inputs[1]].value)
            elif node.kind == "NOT":
                node.value = NOT(self.nodes[node.inputs[0]].value)
        raw = sum(self.nodes[oid].value << i for i, oid in enumerate(self.output_ids))
        return raw - (1 << OUT_WIDTH) if raw & (1 << (OUT_WIDTH - 1)) else raw

    def to_dot(self) -> str:
        lines = ["digraph multiplier {", "  rankdir=BT;"]
        for nid, node in enumerate(self.nodes):
            lines.append(f'  n{nid} [label="{node.kind}"];')
        for nid, node in enumerate(self.nodes):
            for src in node.inputs:
                lines.append(f"  n{src} -> n{nid};")
        lines.append("}")
        return "\n".join(lines)


def _and(a: int, b: int, netlist: Netlist) -> int:
    value = AND(netlist.nodes[a].value, netlist.nodes[b].value)
    return netlist._add("AND", (a, b), value)


def _or(a: int, b: int, netlist: Netlist) -> int:
    value = OR(netlist.nodes[a].value, netlist.nodes[b].value)
    return netlist._add("OR", (a, b), value)


def _xor(a: int, b: int, netlist: Netlist) -> int:
    value = XOR(netlist.nodes[a].value, netlist.nodes[b].value)
    return netlist._add("XOR", (a, b), value)


def _not(a: int, netlist: Netlist) -> int:
    value = NOT(netlist.nodes[a].value)
    return netlist._add("NOT", (a,), value)


def _full_adder(a: int, b: int, cin: int, netlist: Netlist) -> tuple[int, int]:
    ab = _xor(a, b, netlist)
    carry_ab = _and(a, b, netlist)
    total = _xor(ab, cin, netlist)
    carry_in = _and(ab, cin, netlist)
    carry = _or(carry_ab, carry_in, netlist)
    return total, carry


def _bits(value: int, width: int) -> list[int]:
    value &= (1 << width) - 1
    return [(value >> index) & 1 for index in range(width)]


def _bit_w(bits: list[int], index: int, zero_const: int) -> int:
    if index < 0:
        return zero_const
    if index >= len(bits):
        return bits[-1]
    return bits[index]


def _booth_control(
    bits: list[int], group: int, zero_const: int, netlist: Netlist
) -> tuple[int, int, int]:
    low = _bit_w(bits, 2 * group - 1, zero_const)
    middle = _bit_w(bits, 2 * group, zero_const)
    high = _bit_w(bits, 2 * group + 1, zero_const)
    one = _xor(middle, low, netlist)
    two = _and(_not(one, netlist), _xor(high, middle, netlist), netlist)
    return one, two, high


def _booth_control_sign(
    bits: list[int], group: int, zero_const: int, netlist: Netlist
) -> tuple[int, int]:
    low = _bit_w(bits, 2 * group - 1, zero_const)
    middle = _bit_w(bits, 2 * group, zero_const)
    one = _xor(middle, low, netlist)
    return one, middle


def build_multiplier(multiplicand: int, multiplier: int) -> tuple[int, Netlist]:
    netlist = Netlist()
    zero_const = netlist.add_leaf("ZERO", 0)

    a_bits = [netlist.add_leaf("IN_A", bit) for bit in _bits(multiplicand, WIDTH)]
    b_bits = [netlist.add_leaf("IN_B", bit) for bit in _bits(multiplier, WIDTH)]
    netlist.a_ids = a_bits
    netlist.b_ids = b_bits

    columns: list[list[int]] = [[] for _ in range(OUT_WIDTH)]

    num_groups = (WIDTH + 1) // 2
    last_group = num_groups - 1
    degenerate_last = WIDTH % 2 == 1
    one_const = netlist.add_leaf("ONE", 1)

    # Phase 1: Booth partial products with sign-bit inversion (no sign extension).
    for group in range(num_groups):
        offset = 2 * group
        sign_col = offset + WIDTH
        is_top = sign_col == OUT_WIDTH - 1
        if degenerate_last and group == last_group:
            one, negative = _booth_control_sign(b_bits, group, zero_const, netlist)
            for source in range(WIDTH + 1):
                index = offset + source
                magnitude = _and(_bit_w(a_bits, source, zero_const), one, netlist)
                bit = _xor(magnitude, negative, netlist)
                if source == WIDTH and not is_top:
                    bit = _not(bit, netlist)
                columns[index].append(bit)
        else:
            one, two, negative = _booth_control(b_bits, group, zero_const, netlist)
            for source in range(WIDTH + 1):
                index = offset + source
                times_one = _and(_bit_w(a_bits, source, zero_const), one, netlist)
                if source > 0:
                    times_two = _and(_bit_w(a_bits, source - 1, zero_const), two, netlist)
                    magnitude = _or(times_one, times_two, netlist)
                else:
                    magnitude = times_one
                bit = _xor(magnitude, negative, netlist)
                if source == WIDTH and not is_top:
                    bit = _not(bit, netlist)
                columns[index].append(bit)
        columns[offset].append(negative)

    comp = 0
    for group in range(num_groups):
        sign_col = 2 * group + WIDTH
        if sign_col < OUT_WIDTH - 1:
            comp -= 1 << sign_col
    comp &= (1 << OUT_WIDTH) - 1
    for col in (c for c in range(OUT_WIDTH) if (comp >> c) & 1):
        columns[col].append(one_const)

    # Phase 2: Wallace CSA tree — compress each column to <= 2 bits.
    for col in range(OUT_WIDTH):
        bucket = columns[col]
        while len(bucket) >= 3:
            x = bucket.pop()
            y = bucket.pop()
            z = bucket.pop()
            s, c = _full_adder(x, y, z, netlist)
            bucket.append(s)
            if col + 1 < OUT_WIDTH:
                columns[col + 1].append(c)

    # Phase 3: final carry-propagate adder over the two surviving rows.
    carry: int | None = None
    output_ids: list[int] = []
    for col in range(OUT_WIDTH):
        bucket = columns[col]
        if not bucket:
            bucket = [zero_const]
        if carry is None:
            if len(bucket) == 1:
                output_ids.append(bucket[0])
            else:
                hi, lo = bucket[0], bucket[1]
                output_ids.append(_xor(hi, lo, netlist))
                carry = _and(hi, lo, netlist)
        else:
            if len(bucket) == 1:
                b = bucket[0]
                output_ids.append(_xor(b, carry, netlist))
                carry = _and(b, carry, netlist)
            else:
                hi, lo = bucket[0], bucket[1]
                s, c = _full_adder(hi, lo, carry, netlist)
                output_ids.append(s)
                carry = c

    netlist.output_ids = output_ids
    raw = sum(netlist.nodes[nid].value << i for i, nid in enumerate(output_ids))
    return raw, netlist


def multiply(multiplicand: int, multiplier: int) -> int:
    value, _ = build_multiplier(multiplicand, multiplier)
    return value - (1 << OUT_WIDTH) if value & (1 << (OUT_WIDTH - 1)) else value


if __name__ == "__main__":
    a = 3
    b = -5
    print(multiply(a, b))
