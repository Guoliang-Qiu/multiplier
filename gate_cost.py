"""Evaluate the weighted gate cost of one multiplier implementation."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("candidate_multiplier", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load implementation: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("implementation", type=Path)
    args = parser.parse_args()
    module = load_module(args.implementation.resolve())
    _, netlist = module.build_multiplier(-1, -1)
    counts = netlist.gate_count()
    costs = getattr(module, "GATE_COSTS", {"AND": 1, "OR": 1, "XOR": 3, "NOT": 0})
    cost = sum(counts.get(kind, 0) * value for kind, value in costs.items())
    print(json.dumps({"gate_cost": cost, "counts": counts}, sort_keys=True))


if __name__ == "__main__":
    main()
