"""Circuit data model and subcircuit-analysis data structures."""
from __future__ import annotations
from dataclasses import dataclass, field
from .components import ComponentLibrary

@dataclass(frozen=True)
class Node:
    kind: str
    inputs: tuple[int, ...] = ()

@dataclass
class Circuit:
    components: ComponentLibrary = field(default_factory=ComponentLibrary.standard)
    nodes: list[Node] = field(default_factory=list)
    input_ids: list[int] = field(default_factory=list)
    output_ids: list[int] = field(default_factory=list)

    def add(self, kind: str, *inputs: int) -> int:
        spec = self.components.require(kind)
        if len(inputs) != spec.arity:
            raise ValueError(f"{kind} requires {spec.arity} inputs")
        if any(source < 0 or source >= len(self.nodes) for source in inputs):
            raise ValueError(f"{kind} references an invalid node")
        self.nodes.append(Node(kind, tuple(inputs)))
        return len(self.nodes) - 1

    def validate(self):
        from .validation import validate_circuit
        return validate_circuit(self)

    def gatecost(self):
        from .cost import gatecost
        return gatecost(self)

    def reachable_node_ids(self):
        from .analysis import reachable_node_ids
        return reachable_node_ids(self)

    def dependency_decomposition(self, node_ids, max_depth=None):
        from .analysis import decompose_dependencies
        return decompose_dependencies(self, node_ids, max_depth=max_depth)

    def simulate(self, input_values):
        from .simulation import simulate
        return simulate(self, input_values)

    def simulate_many(self, input_values, chunk_size=64):
        from .simulation import simulate_many
        return simulate_many(self, input_values, chunk_size=chunk_size)
