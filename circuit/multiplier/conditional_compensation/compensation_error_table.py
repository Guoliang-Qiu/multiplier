"""Generate an integer compensation error table for downstream SMT synthesis.

The compensation contains at most three Boolean partial products. If their
columns are k0, k1, k2, action code b2b1b0 adds
``b0*2**k0 + b1*2**k1 + b2*2**k2`` to the deleted raw result before rounding.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

from ..tap2_9bit_multiplier import OUT_TOTAL
from .node_set_information import (
    _db,
    _sample_values,
    build_experiment,
    generate_evaluation_samples,
)


def _add_signed_raw(raw, value):
    """Add an exact weighted value with the circuit's fixed output width."""
    modulus = 1 << OUT_TOTAL
    sign_bit = 1 << (OUT_TOTAL - 1)
    unsigned = (raw + value) % modulus
    return np.where(unsigned >= sign_bit, unsigned - modulus, unsigned)


def generate_error_table(
    implementation,
    removed_slots,
    node_ids,
    compensation_columns,
    *,
    samples=None,
):
    """Return E[x,y] = sum((T - 128*Q(D+C(y)))**2 | X=x).

    No truth table is selected here. Output codes index compensation bits in
    the supplied column order. Repeated columns represent separate bits.
    """
    nodes = list(node_ids)
    columns = list(compensation_columns)
    if len(nodes) > 16 or any(type(node) is not int for node in nodes):
        raise ValueError("node_ids must contain at most 16 integer node IDs")
    if not 1 <= len(columns) <= 3:
        raise ValueError("compensation_columns must contain between 1 and 3 columns")
    if any(type(col) is not int or not 0 <= col <= 18 for col in columns):
        raise ValueError("compensation columns must be integer columns 0 through 18")

    if samples is None:
        samples, sampling = generate_evaluation_samples()
    else:
        sampling = {"kind": "provided"}
    samples = np.asarray(samples)
    if (samples.ndim != 2 or samples.shape[1] != 4 or not len(samples)
            or not np.issubdtype(samples.dtype, np.integer)
            or np.any(samples < -256) or np.any(samples > 255)):
        raise ValueError("samples must be a nonempty (N,4) signed 9-bit integer array")
    samples = samples.astype(np.int64)

    _, deleted, _, prefix_size = build_experiment(implementation, removed_slots)
    eligible = set(node for node in deleted.reachable_node_ids()
                   if node < prefix_size and deleted.nodes[node].kind not in {"ZERO", "ONE"})
    if len(set(nodes)) != len(nodes) or any(node not in eligible for node in nodes):
        raise ValueError("X nodes must be distinct, reachable, nonconstant pre-compression nodes")

    deleted_raw, bits = _sample_values(deleted, samples, nodes)
    exact_raw = samples[:, 0] * samples[:, 1] + samples[:, 2] * samples[:, 3]
    # A per-sample squared error is below 2**38 for the 19-bit model.
    # Guard integer reductions rather than silently overflowing int64.
    if len(samples) > np.iinfo(np.int64).max // (1 << 38):
        raise ValueError("sample count exceeds safe int64 accumulation range")
    reference_energy_sum = int(np.square(exact_raw).sum(dtype=np.int64))
    state_count = 1 << len(nodes)
    codes = np.zeros(len(samples), dtype=np.int64)
    for bit in range(len(nodes)):
        codes |= bits[:, bit].astype(np.int64) << bit
    counts = np.bincount(codes, minlength=state_count)

    compensation_values = [
        sum(((code >> bit) & 1) << col for bit, col in enumerate(columns))
        for code in range(1 << len(columns))
    ]
    error_table = np.zeros((state_count, len(compensation_values)), dtype=np.int64)
    for code, value in enumerate(compensation_values):
        compensated_raw = _add_signed_raw(deleted_raw, value)
        output = (compensated_raw + 64) // 128
        squared_error = np.square(exact_raw - 128 * output)
        # Weighted bincount converts to float; add.at preserves integer sums.
        np.add.at(error_table[:, code], codes, squared_error)

    metadata = {
        "sampling": {**sampling, "count": len(samples)},
        "removed_slots": [list(slot) for slot in removed_slots],
        "node_ids": nodes,
        "compensation_columns": columns,
        "num_inputs": len(nodes),
        "num_outputs": len(columns),
        "compensation_values": compensation_values,
        "raw_output_width": OUT_TOTAL,
        "error_scale": 128 ** 2,
        "reference_squared_sum": reference_energy_sum,
        "state_counts": counts.tolist(),
    }
    return metadata, error_table


def evaluate_truth_table(report, table, output_codes):
    """Evaluate a specified G table without any additional circuit simulation."""
    codes = list(output_codes)
    if len(codes) != len(table) or any(
        type(code) is not int or not 0 <= code < (1 << report["num_outputs"])
        for code in codes
    ):
        raise ValueError("provide one valid G output code for every X state")
    error_sum = sum(int(row[code]) for row, code in zip(table, codes))
    return {
        "scaled_squared_error_sum": error_sum,
        "mse": error_sum / report["error_scale"] / report["sampling"]["count"],
        "evm_db": _db(error_sum, report["reference_squared_sum"]),
    }


def _load_candidate(path):
    path = Path(path).resolve()
    module_name = "compensation_table_candidate"
    if path.parent == Path(__file__).resolve().parent:
        module_name = f"{__package__}.{path.stem}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.Candidate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path)
    parser.add_argument("--output", type=Path, required=True, help=".npy matrix path; metadata is saved alongside as .json")
    args = parser.parse_args()
    if args.output.suffix != ".npy":
        parser.error("--output must have a .npy extension")
    config = json.loads(args.config.read_text())
    candidate = _load_candidate(config.pop("implementation"))
    result, matrix = generate_error_table(candidate, **config)
    result["error_table_file"] = args.output.name
    result["error_table_shape"] = list(matrix.shape)
    result["error_table_dtype"] = str(matrix.dtype)
    np.save(args.output, matrix, allow_pickle=False)
    args.output.with_suffix(".json").write_text(
        json.dumps(result, indent=2, allow_nan=False) + "\n"
    )


if __name__ == "__main__":
    main()
