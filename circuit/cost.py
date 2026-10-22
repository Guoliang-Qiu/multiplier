"""Circuit cost calculation."""
from collections import Counter
from dataclasses import dataclass
from .analysis import reachable_node_ids

@dataclass(frozen=True)
class GateCost:
    total: int
    counts: dict[str, int]
    weighted: dict[str, int]

def gatecost(circuit):
    ids = reachable_node_ids(circuit)
    counts = Counter(circuit.nodes[i].kind for i in ids
                     if circuit.components.require(circuit.nodes[i].kind).category == "gate")
    weighted = {name: count * circuit.components.require(name).gate_cost
                for name, count in counts.items()}
    return GateCost(sum(weighted.values()), dict(counts), weighted)
