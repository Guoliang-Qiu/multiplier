"""Broad sampled search for one-node partial-product replacements."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))


def load():
    path = ROOT / "initial_solutions" / "candidate_g0000_0001.py"
    spec = importlib.util.spec_from_file_location("candidate_5761_search", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def main():
    mod = load()
    circuit, columns = mod.build_partial_product_layout()
    full = mod.build_circuit()
    sample_count = 65536
    signed_values = np.random.default_rng(20261020).integers(
        -256, 256, (4, sample_count), dtype=np.int64
    )

    values = []
    dep_sets = []
    input_position = {node: i for i, node in enumerate(full.input_ids)}
    for node_id, node in enumerate(full.nodes):
        kind = node.kind
        deps = set().union(*(dep_sets[i] for i in node.inputs))
        if kind.startswith("IN_"):
            pos = input_position[node_id]
            values.append((signed_values[pos // 9] >> (pos % 9)) & 1)
            deps = {pos}
        elif kind == "ZERO":
            values.append(np.zeros(sample_count, dtype=np.int64))
        elif kind == "ONE":
            values.append(np.ones(sample_count, dtype=np.int64))
        elif kind == "NOT":
            values.append(1 - values[node.inputs[0]])
        else:
            a, b = (values[i] for i in node.inputs)
            values.append(a & b if kind == "AND" else
                          a | b if kind == "OR" else a ^ b)
        dep_sets.append(deps)

    def signed(x):
        return (x + (1 << 18)) % (1 << 19) - (1 << 18)

    raw = sum(values[node] * (1 << bit)
              for bit, node in enumerate(full.output_ids))
    raw = signed(raw)
    reference = (signed_values[0] * signed_values[1] +
                 signed_values[2] * signed_values[3]) / 128.0
    quantized = lambda x: np.floor(x / 128.0 + 0.5)
    baseline_mse = float(np.mean((quantized(raw) - reference) ** 2))

    # IDs are laid out as AB first and CD second in this generator.  For a
    # raw partial-product node, map its corresponding CD node by its position
    # in the product bucket rather than guessing from the global node ID.
    candidates = []
    for col in range(4, 11):
        bucket = columns[col]
        half = len(bucket) // 2
        if half == 0:
            continue
        for pos in range(half):
            ab, cd = bucket[pos], bucket[pos + half]
            support = dep_sets[ab] | dep_sets[cd]
            # Existing nodes whose support is no larger than this pair's
            # support. Constants and input leaves are also allowed.
            pool = [n for n in range(len(full.nodes))
                    if dep_sets[n] <= support]
            for symmetric in (False, True):
                for replacement in pool:
                    if replacement == ab:
                        continue
                    delta = (values[replacement] - values[ab]) * (1 << col)
                    if symmetric:
                        delta = ((values[replacement] - values[ab]) +
                                 (values[replacement] - values[cd])) * (1 << col)
                    score = float(np.mean((quantized(signed(raw + delta)) - reference) ** 2))
                    if score <= baseline_mse * 1.01:
                        candidates.append((score, col, pos, replacement,
                                           symmetric, float(np.mean(delta))))
    candidates.sort()
    print(json.dumps({"baseline_mse": baseline_mse,
                      "sample_count": sample_count,
                      "screened": len(candidates)}))

    verified = []
    for score, col, pos, replacement, symmetric, delta_mean in candidates[:80]:
        buckets = [list(bucket) for bucket in columns]
        half = len(buckets[col]) // 2
        buckets[col][pos] = replacement
        if symmetric:
            buckets[col][pos + half] = replacement
        rebuilt = mod.Candidate()._build_circuit(columns=buckets)
        cost = rebuilt.gatecost().total
        if cost < 1000:
            verified.append({
                "sample_mse": score,
                "ratio": score / baseline_mse,
                "column": col,
                "position": pos,
                "replacement": replacement,
                "symmetric": symmetric,
                "mean_delta": delta_mean,
                "gate_cost": cost,
            })
    for row in sorted(verified, key=lambda x: (x["sample_mse"], x["gate_cost"]))[:40]:
        print(json.dumps(row))


if __name__ == "__main__":
    main()
