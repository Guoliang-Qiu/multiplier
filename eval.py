"""Evaluate a circuit for signed Q2.7 multiplication rounded to Q4.7."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from multiplier.circuit import INPUT_WIDTH, simulate_many, validate_circuit

FRACTION_BITS = 7
ROUNDING_OFFSET = 1 << (FRACTION_BITS - 1)
SCALE = 1 << FRACTION_BITS


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("candidate_multiplier", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load implementation: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def round_q4_14_to_q4_7(raw: int) -> int:
    """Round to nearest Q4.7 code, with ties away from zero."""
    if raw >= 0:
        return (raw + ROUNDING_OFFSET) >> FRACTION_BITS
    return -((-raw + ROUNDING_OFFSET) >> FRACTION_BITS)


def evaluate(module) -> dict[str, float | int]:
    if not hasattr(module, "build_circuit"):
        raise AttributeError("candidate must expose build_circuit()")
    circuit = module.build_circuit()
    validate_circuit(circuit)

    total = errors = 0
    absolute = squared = maximum = 0.0
    bound = 1 << (INPUT_WIDTH - 1)
    inputs = [(a, b) for a in range(-bound, bound) for b in range(-bound, bound)]
    for (a, b), raw_actual in zip(inputs, simulate_many(circuit, inputs)):
        actual_code = round_q4_14_to_q4_7(raw_actual)
        expected_code = round_q4_14_to_q4_7(a * b)
        error = abs(actual_code - expected_code) / SCALE
        total += 1
        errors += actual_code != expected_code
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
    args = parser.parse_args()
    start = time.perf_counter()
    result = evaluate(load_module(args.implementation.resolve()))
    result["runtime_seconds"] = time.perf_counter() - start
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
