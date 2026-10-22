"""Offline residual-information screening; no compensation synthesis.

Run from the repository root with ``python -m
tools.circuit_kit.circuit.multiplier.conditional_compensation.node_set_information CONFIG.json``.
"""
from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import math
import os
import sys
from pathlib import Path

import numpy as np

from ..tap2_9bit_multiplier import OUT_TOTAL, WIDTH
from ...simulation import _simulate_packed_values


def conditional_variance(residual, codes, num_bits):
    """Empirical E[Var(R|X)], using population variance and observed weights."""
    residual = np.asarray(residual, dtype=np.float64)
    codes = np.asarray(codes)
    if not 0 <= num_bits <= 16:
        raise ValueError("num_bits must be between 0 and 16")
    if (residual.ndim != 1 or not residual.size or codes.shape != residual.shape
            or not np.isfinite(residual).all()
            or not np.issubdtype(codes.dtype, np.integer)
            or np.any(codes < 0) or np.any(codes >= 1 << num_bits)):
        raise ValueError("invalid residual or state codes")
    counts = np.bincount(codes, minlength=1 << num_bits)
    sums = np.bincount(codes, weights=residual, minlength=1 << num_bits)
    means = np.divide(sums, counts, out=np.zeros_like(sums), where=counts > 0)
    # Center explicitly to avoid cancellation in E[R^2] - E[E[R|X]^2].
    loss = float(np.mean(np.square(residual - means[codes])))
    return loss, counts


def _db(mse, reference_energy):
    # JSON has no -Infinity. A zero numerator is reported as null plus mse=0.
    if mse == 0 or reference_energy == 0:
        return None
    return 10 * math.log10(mse / reference_energy)


def generate_evaluation_samples():
    """Generate the tap2 workload locally, without importing the evaluator."""
    copies = int(os.environ.get("TAP2_COPIES", "8"))
    if not 1 <= copies <= 1 << WIDTH:
        raise ValueError("TAP2_COPIES must be between 1 and 512")
    seed = 42
    bound = 1 << (WIDTH - 1)
    values = np.arange(-bound, bound, dtype=np.int64)
    rng = np.random.default_rng(seed)
    samples = np.empty((len(values) * (len(values) + 1) // 2 * copies, 4), dtype=np.int64)
    start = 0
    for i, b in enumerate(values):
        for d in values[i:]:
            block = samples[start:start + copies]
            block[:, 0] = values[rng.permutation(len(values))[:copies]]
            block[:, 1] = b
            block[:, 2] = values[rng.permutation(len(values))[:copies]]
            block[:, 3] = d
            start += copies
    return samples, {"kind": "tap2_unordered_pairs", "seed": seed,
                     "tap2_copies": copies}


def build_experiment(implementation, removed_slots):
    """Fork one pre-CSA snapshot, preserving IDs and subclass instance state.

    Slots are (column, original position), not node IDs: repeated occurrences
    of the same node can have distinct arithmetic contributions.
    """
    prefix = implementation()
    buses = prefix.setup()
    prefix._columns = prefix._product_columns(*buses)
    if len(prefix._columns) != OUT_TOTAL:
        raise ValueError(f"expected {OUT_TOTAL} columns")
    slots = [tuple(slot) for slot in removed_slots]
    if any(len(slot) != 2 or any(type(v) is not int for v in slot) for slot in slots):
        raise ValueError("removed_slots must contain integer [column, position] pairs")
    if len(set(slots)) != len(slots):
        raise ValueError("duplicate removal slots")
    for col, position in slots:
        if not 0 <= col < 6 or not 0 <= position < len(prefix._columns[col]):
            raise ValueError(f"invalid low-column slot: {(col, position)}")
    layout = [list(bucket) for bucket in prefix._columns]
    baseline, deleted = copy.deepcopy(prefix), copy.deepcopy(prefix)
    for col, position in sorted(slots, reverse=True):
        del deleted._columns[col][position]
    for circuit in (baseline, deleted):
        circuit._compress_columns()
        circuit._build_outputs()
        circuit.validate()
        if len(circuit.output_ids) != OUT_TOTAL:
            raise ValueError(f"expected {OUT_TOTAL} output bits")
    return baseline, deleted, layout, len(prefix.nodes)


def _sample_values(circuit, samples, node_ids, chunk_size=256):
    raw = np.empty(len(samples), dtype=np.int64)
    bits = np.empty((len(samples), len(node_ids)), dtype=np.uint8)
    for start in range(0, len(samples), chunk_size):
        # Packed simulation needs arbitrary-precision Python integers, not int64.
        chunk = samples[start:start + chunk_size].tolist()
        packed = _simulate_packed_values(circuit, chunk, input_width=WIDTH)
        for offset in range(len(chunk)):
            value = sum(((packed[node] >> offset) & 1) << bit
                        for bit, node in enumerate(circuit.output_ids))
            raw[start + offset] = value - (1 << OUT_TOTAL) if value & (1 << (OUT_TOTAL - 1)) else value
            for j, node in enumerate(node_ids):
                bits[start + offset, j] = (packed[node] >> offset) & 1
    return raw, bits


def evaluate_node_set(implementation, removed_slots, node_ids, *, samples=None,
                      deletion_model="linear"):
    """Evaluate exactly the agent-specified X, without search or ranking.

    ``implementation`` is a zero-argument concrete class implementing the
    three template stages. All results are empirical, not population bounds.
    Default: linear, unquantized analytical deletion P-D, without wraparound.
    X may include any nonconstant pre-compression node for information analysis;
    unavailable nodes are explicitly reported, not treated as free hardware.
    Use deletion_model='physical' for the legacy quantized circuit-deletion model.
    """
    nodes = list(node_ids)
    if deletion_model not in {"linear", "physical"}:
        raise ValueError("deletion_model must be linear or physical")
    if len(nodes) > 16 or any(type(node) is not int for node in nodes):
        raise ValueError("node_ids must contain at most 16 integer node IDs")
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
    baseline, deleted, layout, prefix_size = build_experiment(implementation, removed_slots)
    eligible = sorted(node for node in deleted.reachable_node_ids()
                      if node < prefix_size and deleted.nodes[node].kind not in {"ZERO", "ONE"})
    allowed = eligible if deletion_model == "physical" else [
        n for n in range(prefix_size) if baseline.nodes[n].kind not in {"ZERO", "ONE"}]
    if len(set(nodes)) != len(nodes) or any(node not in allowed for node in nodes):
        raise ValueError("X must contain distinct nonconstant pre-compression nodes; "
                         "physical mode additionally requires reachability after deletion")
    removed = [layout[col][position] for col, position in removed_slots]
    if deletion_model == "linear":
        baseline_raw, observed = _sample_values(baseline, samples, nodes + removed)
        bits = observed[:, :len(nodes)]
        contribution = np.zeros(len(samples), dtype=np.int64)
        for j, (col, _) in enumerate(removed_slots):
            contribution += observed[:, len(nodes) + j].astype(np.int64) * (1 << col)
        deleted_raw = baseline_raw - contribution
    else:
        baseline_raw, _ = _sample_values(baseline, samples, [])
        deleted_raw, bits = _sample_values(deleted, samples, nodes)
    reference = (samples[:, 0] * samples[:, 1] + samples[:, 2] * samples[:, 3]) / 128.0
    residual = (reference - deleted_raw / 128.0 if deletion_model == "linear"
                else reference - np.floor(deleted_raw / 128.0 + 0.5))
    energy = float(np.mean(reference ** 2))

    def metrics(raw):
        output = raw / 128.0 if deletion_model == "linear" else np.floor(raw / 128.0 + 0.5)
        mse = float(np.mean((reference - output) ** 2))
        return {"mse": mse, "evm_db": _db(mse, energy)}

    codes = np.zeros(len(samples), dtype=np.int64)
    for bit, index in enumerate(range(len(nodes))):
        codes |= bits[:, index].astype(np.int64) << bit
    loss, counts = conditional_variance(residual, codes, len(nodes))
    result = {
        "sampling": {**sampling, "count": len(samples)},
        "deletion_model": deletion_model,
        "residual": ("(a*b+c*d - baseline_raw + removed_weighted_sum)/128; no floor, no wrap"
                     if deletion_model == "linear" else
                     "(a*b+c*d)/128 - floor(deleted_raw/128 + 0.5)"),
        "reference_energy": energy,
        "baseline": {**metrics(baseline_raw), "gate_cost": baseline.gatecost().total},
        "deleted": {**metrics(deleted_raw), "gate_cost":
                    deleted.gatecost().total if deletion_model == "physical" else None},
        "removed_slots": [list(slot) for slot in removed_slots],
        "node_ids": nodes,
        "information_mse": loss,
        "information_evm_db": _db(loss, energy),
    }
    if deletion_model == "linear":
        original_error = reference - baseline_raw / 128.0
        original_loss, _ = conditional_variance(original_error, codes, len(nodes))
        missing_loss, _ = conditional_variance(contribution / 128.0, codes, len(nodes))
        result.update(
            baseline_variance=float(np.var(original_error)),
            baseline_conditional_variance=original_loss,
            baseline_conditional_variance_evm_db=_db(original_loss, energy),
            conditional_variance_gap=loss-original_loss,
            removed_conditional_variance=missing_loss,
            x_unreachable_after_physical_deletion=[n for n in nodes if n not in eligible],
            physical_deletion_gate_cost=deleted.gatecost().total,
            note="Linear deletion is an analytical model, not an implemented cheaper circuit. "
                 "Error-table/synthesis/export retain their physical-deletion model.")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    path = Path(config.pop("implementation")).resolve()
    # Preserve package context for bundled candidates using relative imports.
    module_name = "compensation_candidate"
    if path.parent == Path(__file__).resolve().parent:
        module_name = f"{__package__}.{path.stem}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    result = evaluate_node_set(module.Candidate, **config)
    text = json.dumps(result, indent=2, allow_nan=False)
    if args.output:
        args.output.write_text(text + "\n")
    else:
        print(text)


if __name__ == "__main__":
    main()
