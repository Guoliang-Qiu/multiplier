"""Compare a candidate multiplier with exact integer multiplication."""
from __future__ import annotations

import argparse
import importlib.util
import json
import time
from pathlib import Path
import sys

WIDTH = 9


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("candidate_multiplier", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load implementation: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def evaluate(module) -> dict[str, float | int]:
    total = errors = absolute = squared = maximum = 0
    for a in range(-(1 << (WIDTH - 1)), 1 << (WIDTH - 1)):
        for b in range(-(1 << (WIDTH - 1)), 1 << (WIDTH - 1)):
            actual = module.multiply(a, b)
            expected = a * b
            error = abs(actual - expected)
            total += 1
            errors += actual != expected
            absolute += error
            squared += error * error
            maximum = max(maximum, error)
    return {
        "total_cases": total,
        "error_cases": errors,
        "error_rate": errors / total,
        "mae": absolute / total,
        "rmse": (squared / total) ** 0.5,
        "max_abs_error": maximum,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("implementation", type=Path)
    parser.add_argument("--reference", type=Path, help="Optional exact reference to validate")
    args = parser.parse_args()
    start = time.perf_counter()
    candidate = load_module(args.implementation.resolve())
    if args.reference:
        reference = load_module(args.reference.resolve())
        if evaluate(reference)["error_rate"] != 0.0:
            raise RuntimeError("Reference implementation is not exact")
    result = evaluate(candidate)
    result["runtime_seconds"] = time.perf_counter() - start
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
