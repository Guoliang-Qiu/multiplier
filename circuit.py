"""Shared circuit schema, validation, simulation, and structural analysis."""
from __future__ import annotations

from collections.abc import Iterable, Sequence
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


@dataclass(frozen=True)
class Subcircuit:
    """A selected region and its interface in the parent circuit."""

    node_ids: tuple[int, ...]
    input_ids: tuple[int, ...]
    output_ids: tuple[int, ...]


@dataclass(frozen=True)
class SubcircuitObservation:
    """The exact local constraint induced by one real parent input."""

    global_input: tuple[int, int]
    input_values: tuple[int, ...]
    output_values: tuple[int, ...]
    allowed_outputs: tuple[tuple[int, ...], ...]


@dataclass(frozen=True)
class SubcircuitTruthRow:
    """Constraints shared by all occurrences of one reachable local input."""

    input_values: tuple[int, ...]
    allowed_outputs: tuple[tuple[int, ...], ...]
    occurrences: int


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
    values = _simulate_values(circuit, a, b)

    raw = sum(values[node_id] << index for index, node_id in enumerate(circuit.output_ids))
    return raw - (1 << OUTPUT_WIDTH) if raw & (1 << (OUTPUT_WIDTH - 1)) else raw


def _simulate_values(
    circuit: Circuit, a: int, b: int, overrides: dict[int, int] | None = None
) -> list[int]:
    """Evaluate every node, optionally overriding selected node values."""
    values = [0] * len(circuit.nodes)
    for index, node_id in enumerate(circuit.a_ids):
        values[node_id] = (a >> index) & 1
    for index, node_id in enumerate(circuit.b_ids):
        values[node_id] = (b >> index) & 1

    for node_id, node in enumerate(circuit.nodes):
        if overrides is not None and node_id in overrides:
            values[node_id] = overrides[node_id]
            continue
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

    return values


def simulate_many(
    circuit: Circuit, inputs: list[tuple[int, int]], chunk_size: int = 64
) -> list[int]:
    """Evaluate inputs in small bit-parallel chunks."""
    results: list[int] = []
    for start in range(0, len(inputs), chunk_size):
        chunk = inputs[start:start + chunk_size]
        values = _simulate_packed_values(circuit, chunk)

        for index in range(len(chunk)):
            results.append(sum(
                ((values[node_id] >> index) & 1) << bit
                for bit, node_id in enumerate(circuit.output_ids)
            ))

    sign_bit = 1 << (OUTPUT_WIDTH - 1)
    modulus = 1 << OUTPUT_WIDTH
    return [raw - modulus if raw & sign_bit else raw for raw in results]


def _simulate_packed_values(
    circuit: Circuit,
    inputs: Sequence[tuple[int, int]],
    overrides: dict[int, int] | None = None,
) -> list[int]:
    """Evaluate every node with one bit position per parent input."""
    mask = (1 << len(inputs)) - 1
    values = [0] * len(circuit.nodes)
    for bit, node_id in enumerate(circuit.a_ids):
        values[node_id] = sum(
            ((a >> bit) & 1) << index for index, (a, _) in enumerate(inputs)
        )
    for bit, node_id in enumerate(circuit.b_ids):
        values[node_id] = sum(
            ((b >> bit) & 1) << index for index, (_, b) in enumerate(inputs)
        )

    for node_id, node in enumerate(circuit.nodes):
        if overrides is not None and node_id in overrides:
            values[node_id] = overrides[node_id] & mask
        elif node.kind == "ONE":
            values[node_id] = mask
        elif node.kind == "AND":
            values[node_id] = values[node.inputs[0]] & values[node.inputs[1]]
        elif node.kind == "OR":
            values[node_id] = values[node.inputs[0]] | values[node.inputs[1]]
        elif node.kind == "XOR":
            values[node_id] = values[node.inputs[0]] ^ values[node.inputs[1]]
        elif node.kind == "NOT":
            values[node_id] = values[node.inputs[0]] ^ mask
    return values


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


def consumer_ids(circuit: Circuit) -> tuple[tuple[int, ...], ...]:
    """Return the node IDs that consume each node, in node order."""
    consumers = [[] for _ in circuit.nodes]
    for node_id, node in enumerate(circuit.nodes):
        for source in node.inputs:
            consumers[source].append(node_id)
    return tuple(tuple(ids) for ids in consumers)


def extract_subcircuit(
    circuit: Circuit, node_ids: Iterable[int]
) -> Subcircuit:
    """Extract a node region and derive its external interface.

    ``node_ids`` may be non-contiguous. Inputs are outside nodes referenced by
    the region. Outputs are region nodes consumed outside the region or used
    as parent outputs. Ordering is deterministic and follows node order.
    """
    validate_circuit(circuit)
    selected = frozenset(node_ids)
    if not selected:
        raise ValueError("subcircuit must contain at least one node")
    if any(node_id < 0 or node_id >= len(circuit.nodes) for node_id in selected):
        raise ValueError("subcircuit contains an invalid node ID")

    input_ids = []
    for node_id in sorted(selected):
        for source in circuit.nodes[node_id].inputs:
            if source not in selected and source not in input_ids:
                input_ids.append(source)

    consumers = consumer_ids(circuit)
    parent_outputs = set(circuit.output_ids)
    output_ids = [
        node_id for node_id in sorted(selected)
        if node_id in parent_outputs or any(consumer not in selected for consumer in consumers[node_id])
    ]
    return Subcircuit(tuple(sorted(selected)), tuple(input_ids), tuple(output_ids))


def collect_subcircuit_observations(
    circuit: Circuit,
    subcircuit: Subcircuit,
    inputs: Sequence[tuple[int, int]],
    chunk_size: int = 64,
    max_output_bits: int = 8,
) -> list[SubcircuitObservation]:
    """Collect exact local constraints induced by real parent inputs.

    Rows are not synthesized independently: each row comes from an actual
    parent input. For each row, ``allowed_outputs`` contains every complete
    subcircuit output vector that leaves all parent outputs unchanged. This
    captures observability don't-cares without assuming output bits can be
    changed independently.
    """
    validate_circuit(circuit)
    if any(node_id < 0 or node_id >= len(circuit.nodes)
           for node_id in subcircuit.output_ids):
        raise ValueError("subcircuit interface contains an invalid output")
    selected = set(subcircuit.node_ids)
    if any(node_id < 0 or node_id >= len(circuit.nodes) for node_id in selected):
        raise ValueError("subcircuit contains an invalid node ID")
    if not set(subcircuit.input_ids).isdisjoint(selected):
        raise ValueError("subcircuit inputs must be outside the selected region")
    if not set(subcircuit.output_ids).issubset(selected):
        raise ValueError("subcircuit outputs must be inside the selected region")
    if len(subcircuit.output_ids) > max_output_bits:
        raise ValueError(
            "exact observability requires enumerating every output vector; "
            f"got {len(subcircuit.output_ids)} outputs, limit is {max_output_bits}"
        )
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")

    observations = []
    output_vectors = [
        tuple((raw >> bit) & 1 for bit in range(len(subcircuit.output_ids)))
        for raw in range(1 << len(subcircuit.output_ids))
    ]
    for start in range(0, len(inputs), chunk_size):
        chunk = inputs[start:start + chunk_size]
        mask = (1 << len(chunk)) - 1
        values = _simulate_packed_values(circuit, chunk)
        valid_masks = []
        for candidate in output_vectors:
            overrides = {
                node_id: mask if value else 0
                for node_id, value in zip(subcircuit.output_ids, candidate)
            }
            changed = _simulate_packed_values(circuit, chunk, overrides)
            differences = 0
            for node_id in circuit.output_ids:
                differences |= values[node_id] ^ changed[node_id]
            valid_masks.append(mask ^ differences)

        for index, global_input in enumerate(chunk):
            local_inputs = tuple(
                (values[node_id] >> index) & 1 for node_id in subcircuit.input_ids
            )
            local_outputs = tuple(
                (values[node_id] >> index) & 1 for node_id in subcircuit.output_ids
            )
            allowed_outputs = tuple(
                candidate for candidate, valid in zip(output_vectors, valid_masks)
                if (valid >> index) & 1
            )
            observations.append(SubcircuitObservation(
                global_input, local_inputs, local_outputs, allowed_outputs
            ))
    return observations


def build_subcircuit_truth_table(
    observations: Iterable[SubcircuitObservation],
) -> list[SubcircuitTruthRow]:
    """Merge real-input observations into a reachable partial truth table.

    If one local input occurs in several global contexts, a replacement must
    satisfy all of them, so their allowed output sets are intersected. Local
    input patterns absent from the result are unreachable and therefore full
    don't-cares for MCSP.
    """
    allowed_by_input: dict[tuple[int, ...], set[tuple[int, ...]]] = {}
    occurrences: dict[tuple[int, ...], int] = {}
    for observation in observations:
        input_values = observation.input_values
        allowed = set(observation.allowed_outputs)
        if input_values in allowed_by_input:
            allowed_by_input[input_values].intersection_update(allowed)
        else:
            allowed_by_input[input_values] = allowed
        occurrences[input_values] = occurrences.get(input_values, 0) + 1

    rows = []
    for input_values in sorted(allowed_by_input):
        allowed_outputs = tuple(sorted(allowed_by_input[input_values]))
        if not allowed_outputs:
            raise ValueError(
                f"inconsistent constraints for local input {input_values!r}"
            )
        rows.append(SubcircuitTruthRow(
            input_values, allowed_outputs, occurrences[input_values]
        ))
    return rows
