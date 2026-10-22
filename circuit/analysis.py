"""Dependency and subcircuit analysis."""
from __future__ import annotations
from collections.abc import Iterable
from dataclasses import dataclass
from .model import Circuit


@dataclass(frozen=True)
class DependencyDecomposition:
    selected_ids: tuple[int, ...]
    dependency_ids: tuple[int, ...]
    boundary_ids: tuple[int, ...]
    distances: dict[int, int]

def reachable_node_ids(circuit):
    reachable = set(circuit.output_ids)
    pending = list(circuit.output_ids)
    while pending:
        for source in circuit.nodes[pending.pop()].inputs:
            if source not in reachable:
                reachable.add(source)
                pending.append(source)
    return reachable

def decompose_dependencies(circuit: Circuit, node_ids: Iterable[int], max_depth: int | None = None):
    selected = tuple(dict.fromkeys(node_ids))
    if not selected or any(i < 0 or i >= len(circuit.nodes) for i in selected):
        raise ValueError("selected node is outside the circuit or empty")
    if max_depth is not None and max_depth < 0:
        raise ValueError("max_depth must be non-negative")
    distances = {i: 0 for i in selected}
    pending, boundary = list(selected), set()
    while pending:
        i = pending.pop(0)
        parents = circuit.nodes[i].inputs
        if not parents or (max_depth is not None and distances[i] >= max_depth):
            boundary.add(i)
            continue
        for parent in parents:
            distance = distances[i] + 1
            if parent not in distances or distance < distances[parent]:
                distances[parent] = distance
                pending.append(parent)
    return DependencyDecomposition(selected, tuple(sorted(set(distances) - set(selected))),
                                   tuple(sorted(boundary)), distances)
