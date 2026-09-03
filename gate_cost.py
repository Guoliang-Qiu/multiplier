"""Evaluate the fixed weighted cost of a multiplier circuit DAG."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from multiplier.circuit import GATE_ARITY, reachable_node_ids, validate_circuit

GATE_COSTS = {"AND": 1, "OR": 1, "XOR": 3, "NOT": 0}


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("candidate_multiplier", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load implementation: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def evaluate(module) -> dict[str, int | dict[str, int]]:
    if not hasattr(module, "build_circuit"):
        raise AttributeError("candidate must expose build_circuit()")
    circuit = module.build_circuit()
    validate_circuit(circuit)
    counts = {kind: 0 for kind in GATE_COSTS}
    for node_id in reachable_node_ids(circuit):
        kind = circuit.nodes[node_id].kind
        if kind in GATE_ARITY:
            counts[kind] += 1
    cost = sum(counts[kind] * GATE_COSTS[kind] for kind in GATE_COSTS)
    return {"gate_cost": cost, "counts": counts}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("implementation", type=Path)
    args = parser.parse_args()
    print(json.dumps(evaluate(load_module(args.implementation.resolve())), sort_keys=True))


if __name__ == "__main__":
    main()
