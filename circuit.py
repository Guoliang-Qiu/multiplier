"""Shared circuit schema, validation, simulation, and structural analysis."""
from __future__ import annotations

from dataclasses import dataclass, field

INPUT_WIDTH = 9
OUTPUT_WIDTH = 18
GATE_ARITY = {"AND": 2, "OR": 2, "XOR": 2, "NOT": 1}
LEAF_KINDS = {"IN_A", "IN_B", "ZERO", "ONE"}


@dataclass(frozen=True)
class Node:
    kind: str
    inputs: tuple[int, ...] = ()


@dataclass
class Circuit:
    nodes: list[Node] = field(default_factory=list)
    a_ids: list[int] = field(default_factory=list)
    b_ids: list[int] = field(default_factory=list)
    output_ids: list[int] = field(default_factory=list)

    def add(self, kind: str, *inputs: int) -> int:
        self.nodes.append(Node(kind, tuple(inputs)))
        return len(self.nodes) - 1


def validate_circuit(circuit: Circuit) -> None:
    if not isinstance(circuit, Circuit):
        raise TypeError("build_circuit() must return multiplier.circuit.Circuit")
    if len(circuit.a_ids) != INPUT_WIDTH or len(circuit.b_ids) != INPUT_WIDTH:
        raise ValueError(f"circuit must have two {INPUT_WIDTH}-bit input buses")
    if len(circuit.output_ids) != OUTPUT_WIDTH:
        raise ValueError(f"circuit must have {OUTPUT_WIDTH} output bits")

    for index, node in enumerate(circuit.nodes):
        if node.kind in LEAF_KINDS:
            if node.inputs:
                raise ValueError(f"leaf node {index} must not have inputs")
        elif node.kind in GATE_ARITY:
            if len(node.inputs) != GATE_ARITY[node.kind]:
                raise ValueError(
                    f"{node.kind} node {index} requires {GATE_ARITY[node.kind]} inputs"
                )
        else:
            raise ValueError(f"unsupported node kind {node.kind!r} at node {index}")
        if any(source < 0 or source >= index for source in node.inputs):
            raise ValueError(f"node {index} must reference earlier valid nodes")

    if len(set(circuit.a_ids + circuit.b_ids)) != 2 * INPUT_WIDTH:
        raise ValueError("input buses must contain distinct nodes")
    for node_id in circuit.a_ids:
        if not 0 <= node_id < len(circuit.nodes) or circuit.nodes[node_id].kind != "IN_A":
            raise ValueError("a_ids must reference IN_A leaves")
    for node_id in circuit.b_ids:
        if not 0 <= node_id < len(circuit.nodes) or circuit.nodes[node_id].kind != "IN_B":
            raise ValueError("b_ids must reference IN_B leaves")
    if any(node_id < 0 or node_id >= len(circuit.nodes) for node_id in circuit.output_ids):
        raise ValueError("output_ids contains an invalid node")


def simulate(circuit: Circuit, a: int, b: int) -> int:
    """Evaluate a validated circuit and return its signed 18-bit raw result."""
    values = [0] * len(circuit.nodes)
    for index, node_id in enumerate(circuit.a_ids):
        values[node_id] = (a >> index) & 1
    for index, node_id in enumerate(circuit.b_ids):
        values[node_id] = (b >> index) & 1

    for node_id, node in enumerate(circuit.nodes):
        if node.kind == "ONE":
            values[node_id] = 1
        elif node.kind == "AND":
            values[node_id] = values[node.inputs[0]] & values[node.inputs[1]]
        elif node.kind == "OR":
            values[node_id] = values[node.inputs[0]] | values[node.inputs[1]]
        elif node.kind == "XOR":
            values[node_id] = values[node.inputs[0]] ^ values[node.inputs[1]]
        elif node.kind == "NOT":
            values[node_id] = values[node.inputs[0]] ^ 1

    raw = sum(values[node_id] << index for index, node_id in enumerate(circuit.output_ids))
    return raw - (1 << OUTPUT_WIDTH) if raw & (1 << (OUTPUT_WIDTH - 1)) else raw


def simulate_many(
    circuit: Circuit, inputs: list[tuple[int, int]], chunk_size: int = 64
) -> list[int]:
    """Evaluate inputs in small bit-parallel chunks."""
    results: list[int] = []
    for start in range(0, len(inputs), chunk_size):
        chunk = inputs[start:start + chunk_size]
        mask = (1 << len(chunk)) - 1
        values = [0] * len(circuit.nodes)
        for bit, node_id in enumerate(circuit.a_ids):
            values[node_id] = sum(
                ((a >> bit) & 1) << index for index, (a, _) in enumerate(chunk)
            )
        for bit, node_id in enumerate(circuit.b_ids):
            values[node_id] = sum(
                ((b >> bit) & 1) << index for index, (_, b) in enumerate(chunk)
            )

        for node_id, node in enumerate(circuit.nodes):
            if node.kind == "ONE":
                values[node_id] = mask
            elif node.kind == "AND":
                values[node_id] = values[node.inputs[0]] & values[node.inputs[1]]
            elif node.kind == "OR":
                values[node_id] = values[node.inputs[0]] | values[node.inputs[1]]
            elif node.kind == "XOR":
                values[node_id] = values[node.inputs[0]] ^ values[node.inputs[1]]
            elif node.kind == "NOT":
                values[node_id] = values[node.inputs[0]] ^ mask

        for index in range(len(chunk)):
            results.append(sum(
                ((values[node_id] >> index) & 1) << bit
                for bit, node_id in enumerate(circuit.output_ids)
            ))

    sign_bit = 1 << (OUTPUT_WIDTH - 1)
    modulus = 1 << OUTPUT_WIDTH
    return [raw - modulus if raw & sign_bit else raw for raw in results]


def reachable_node_ids(circuit: Circuit) -> set[int]:
    reachable = set(circuit.output_ids)
    pending = list(circuit.output_ids)
    while pending:
        node_id = pending.pop()
        for source in circuit.nodes[node_id].inputs:
            if source not in reachable:
                reachable.add(source)
                pending.append(source)
    return reachable
