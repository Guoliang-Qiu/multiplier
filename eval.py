"""Evaluate a multiplier circuit under qgl performance semantics.

Single-multiplier circuits (two 9-bit inputs -> 18-bit output) keep the qgl
reference ``f_out = a*b/128``. tap2 circuits (four 9-bit inputs -> 19-bit
output, computing ``a*b + c*d``) use ``f_out = (a*b + c*d)/128``.

In both modes:

- The reference keeps full precision (never rounded).
- Only the computed value is quantized: ``f_new = floor(raw/128 + 0.5)``.
- ``evm_db = 20*log10(||f_out - f_new|| / ||f_out||)`` (2-norm over all cases).

tap2 inputs are sampled by enumerating every unordered ``(b, d)`` pair over
the signed 9-bit domain, with ``TAP2_COPIES`` random values drawn per pair for
``a`` and ``c`` (seed 42).
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys
import time

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from multiplier.circuit import INPUT_WIDTH, simulate_many, validate_circuit

SCALE = 1 << 7  # 128: Q4.14 -> Q4.7 scale used by the qgl script
RNG_SEED = 42
TAP2_COPIES = int(os.environ.get("TAP2_COPIES", "8"))


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("candidate_multiplier", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load implementation: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _common_metrics(raws: list[int], f_out: np.ndarray) -> dict[str, float | int]:
    raw = np.asarray(raws, dtype=np.float64)            # signed raw result
    f_new = np.floor(raw / SCALE + 0.5)                 # quantize computed only
    equals = f_out == f_new
    total = len(raws)

    err_rounded = f_out - f_new
    err_raw = f_out - raw / SCALE
    return {
        "total_cases": total,
        "error_cases": int(total - int(equals.sum())),
        "error_rate": float(1.0 - equals.mean()),
        "evm_db": float(20 * np.log10(np.linalg.norm(err_rounded) / np.linalg.norm(f_out))),
        "mae": float(np.abs(err_rounded).mean()),
        "avg_abs_error": float(np.abs(err_rounded).mean()),
        "rmse": float(np.sqrt(np.mean(err_rounded * err_rounded))),
        "max_abs_error": float(np.abs(err_rounded).max()),
        "bias": float(err_raw.mean()),
        "mse": float(np.mean(err_raw * err_raw)),
    }


def _qgl_metrics(raws: list[int], a: np.ndarray, b: np.ndarray) -> dict[str, float | int]:
    f_out = (a * b).astype(np.float64) / SCALE          # unquantized reference
    return _common_metrics(raws, f_out)


def _tap2_metrics(
    raws: list[int], a: np.ndarray, b: np.ndarray, c: np.ndarray, d: np.ndarray
) -> dict[str, float | int]:
    f_out = (a * b + c * d).astype(np.float64) / SCALE  # unquantized reference
    return _common_metrics(raws, f_out)


def generate_data() -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Sample (a, b, c, d) using the shared tap2 procedure.

    Enumerates every unordered ``(b, d)`` pair over the signed 9-bit domain
    and independently draws ``TAP2_COPIES`` random values for ``a`` and ``c``
    per pair, with a fixed seed.
    """
    bound = 1 << (INPUT_WIDTH - 1)
    values = np.arange(-bound, bound, dtype=np.int64)
    rng = np.random.default_rng(RNG_SEED)
    copies = TAP2_COPIES

    b_vals: list[int] = []
    d_vals: list[int] = []
    a_parts: list[np.ndarray] = []
    c_parts: list[np.ndarray] = []
    for i in range(len(values)):
        for j in range(i, len(values)):
            b_vals.append(values[i])
            d_vals.append(values[j])
            a_parts.append(values[rng.permutation(len(values))[:copies]])
            c_parts.append(values[rng.permutation(len(values))[:copies]])

    a = np.concatenate(a_parts)
    c = np.concatenate(c_parts)
    b = np.repeat(np.asarray(b_vals, dtype=np.int64), copies)
    d = np.repeat(np.asarray(d_vals, dtype=np.int64), copies)
    return a, b, c, d


def evaluate(module) -> dict[str, float | int]:
    if not hasattr(module, "build_circuit"):
        raise AttributeError("candidate must expose build_circuit()")
    circuit = module.build_circuit()
    validate_circuit(circuit)

    if len(circuit.input_ids) == 4 * INPUT_WIDTH:
        a, b, c, d = generate_data()
        inputs = list(zip(a.tolist(), b.tolist(), c.tolist(), d.tolist()))
        raws = simulate_many(circuit, inputs)
        return _tap2_metrics(raws, a, b, c, d)

    bound = 1 << (INPUT_WIDTH - 1)
    inputs = [(a, b) for a in range(-bound, bound) for b in range(-bound, bound)]
    a = np.array([p[0] for p in inputs], dtype=np.int64)
    b = np.array([p[1] for p in inputs], dtype=np.int64)
    raws = simulate_many(circuit, inputs)
    return _qgl_metrics(raws, a, b)


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
