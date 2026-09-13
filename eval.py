"""Evaluate ``a*b + c*d`` using deterministic sampled four-input cases."""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
from pathlib import Path
import random
import sys
import time

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from multiplier.circuit import INPUT_WIDTH, simulate_many, validate_circuit

DEFAULT_SEED = 0
SAMPLES_PER_BD_PAIR = 2
SCALE = 128.0


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("candidate_multiplier", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load implementation: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def make_inputs(seed: int = DEFAULT_SEED) -> list[tuple[int, int, int, int]]:
    """Enumerate unordered ``(b, d)`` pairs and sample ``(a, c)`` twice."""
    bound = 1 << (INPUT_WIDTH - 1)
    rng = random.Random(seed)
    inputs = []
    for b in range(-bound, bound):
        for d in range(b, bound):
            for _ in range(SAMPLES_PER_BD_PAIR):
                a = rng.randrange(-bound, bound)
                c = rng.randrange(-bound, bound)
                inputs.append((a, b, c, d))
    return inputs


def evaluate(
    module, seed: int = DEFAULT_SEED
) -> dict[str, float | int]:
    if not hasattr(module, "build_circuit"):
        raise AttributeError("candidate must expose build_circuit()")
    circuit = module.build_circuit()
    validate_circuit(circuit)

    inputs = make_inputs(seed)
    errors = 0
    exact_outputs: list[float] = []
    rounded_outputs: list[float] = []
    for (a, b, c, d), raw_actual in zip(inputs, simulate_many(circuit, inputs)):
        # The exact result and circuit result are compared in the scaled domain.
        exact_outputs.append((float(a) * float(b) + float(c) * float(d)) / SCALE)
        rounded_outputs.append(math.floor(raw_actual / SCALE + 0.5))

    fout = np.asarray(exact_outputs, dtype=np.float64)
    rounded = np.asarray(rounded_outputs, dtype=np.float64)
    err_rounded = rounded - fout
    norm_fout = np.linalg.norm(fout)
    relative_error_db = (
        20.0 * np.log10(np.linalg.norm(err_rounded) / norm_fout)
        if norm_fout != 0.0
        else float("-inf") if np.linalg.norm(err_rounded) == 0.0 else float("inf")
    )
    total = len(inputs)
    errors = int(np.count_nonzero(err_rounded))
    return {
        "total_cases": total,
        "error_cases": errors,
        "error_rate": errors / total,
        "mae": float(np.mean(np.abs(err_rounded))),
        "rmse": float(np.linalg.norm(err_rounded) / np.sqrt(total)),
        "max_abs_error": float(np.max(np.abs(err_rounded))),
        "relative_error_db": float(relative_error_db),
        "scale": SCALE,
        "seed": seed,
        "samples_per_bd_pair": SAMPLES_PER_BD_PAIR,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("implementation", type=Path)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    args = parser.parse_args()
    start = time.perf_counter()
    result = evaluate(load_module(args.implementation.resolve()), seed=args.seed)
    result["runtime_seconds"] = time.perf_counter() - start
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
