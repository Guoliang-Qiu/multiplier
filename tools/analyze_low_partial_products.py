"""Analyze cheap replacements for 57.61 candidate partial-product nodes.

This is deliberately a read-only experiment: it builds the existing raw
partial-product layout, evaluates each selected node over its marginal input
space, and never changes the circuit.
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE = ROOT / "initial_solutions" / "candidate_g0000_0001.py"


def load_candidate():
    spec = importlib.util.spec_from_file_location("candidate_5761", CANDIDATE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {CANDIDATE}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@dataclass(frozen=True)
class Candidate:
    name: str
    values: tuple[int, ...]
    gate_cost: int


def input_label(index: int) -> str:
    names = "ABCD"
    return f"{names[index // 9]}[{index % 9}]"


def dependencies(circuit, node_id: int, memo: dict[int, frozenset[int]]):
    if node_id in memo:
        return memo[node_id]
    node = circuit.nodes[node_id]
    if node.kind.startswith("IN_"):
        result = frozenset((circuit.input_ids.index(node_id),))
    elif node.kind in ("ZERO", "ONE"):
        result = frozenset()
    else:
        result = frozenset().union(*(dependencies(circuit, child, memo)
                                     for child in node.inputs))
    memo[node_id] = result
    return result


def evaluate(circuit, node_id: int, assignment: dict[int, int], cache: dict[int, int]):
    if node_id in cache:
        return cache[node_id]
    node = circuit.nodes[node_id]
    kind = node.kind
    if kind.startswith("IN_"):
        value = assignment[circuit.input_ids.index(node_id)]
    elif kind == "ZERO":
        value = 0
    elif kind == "ONE":
        value = 1
    elif kind == "NOT":
        value = 1 - evaluate(circuit, node.inputs[0], assignment, cache)
    else:
        left = evaluate(circuit, node.inputs[0], assignment, cache)
        right = evaluate(circuit, node.inputs[1], assignment, cache)
        value = {"AND": left & right, "OR": left | right,
                 "XOR": left ^ right}[kind]
    cache[node_id] = value
    return value


def make_candidates(dep_count: int, truth: tuple[int, ...]):
    candidates = [Candidate("ZERO", (0,) * len(truth), 0),
                  Candidate("ONE", (1,) * len(truth), 0)]
    for i in range(dep_count):
        bit = tuple((mask >> i) & 1 for mask in range(len(truth)))
        candidates += [Candidate(f"x{i}", bit, 0),
                       Candidate(f"~x{i}", tuple(1 - x for x in bit), 0)]
    for i in range(dep_count):
        for j in range(i + 1, dep_count):
            xi = tuple((mask >> i) & 1 for mask in range(len(truth)))
            xj = tuple((mask >> j) & 1 for mask in range(len(truth)))
            candidates += [Candidate(f"x{i}&x{j}", tuple(a & b for a, b in zip(xi, xj)), 1),
                           Candidate(f"x{i}|x{j}", tuple(a | b for a, b in zip(xi, xj)), 1),
                           Candidate(f"x{i}^x{j}", tuple(a ^ b for a, b in zip(xi, xj)), 3)]
    # Remove duplicate truth tables while keeping the cheapest spelling.
    best = {}
    for candidate in candidates:
        old = best.get(candidate.values)
        if old is None or candidate.gate_cost < old.gate_cost:
            best[candidate.values] = candidate
    return tuple(best.values())


def analyze_node(circuit, node_id: int, column: int, dep_memo):
    dep_ids = sorted(dependencies(circuit, node_id, dep_memo))
    if len(dep_ids) > 14:
        return []
    exact = []
    for mask in range(1 << len(dep_ids)):
        assignment = {input_index: (mask >> i) & 1
                      for i, input_index in enumerate(dep_ids)}
        exact.append(evaluate(circuit, node_id, assignment, {}))
    results = []
    weight = 1 << column
    for candidate in make_candidates(len(dep_ids), tuple(exact)):
        errors = [candidate.values[i] - exact[i] for i in range(len(exact))]
        mismatches = sum(error != 0 for error in errors)
        bias = sum(errors) / len(errors)
        mse = sum(error * error for error in errors) / len(errors)
        results.append({
            "column": column,
            "node_id": node_id,
            "dep_count": len(dep_ids),
            "dependencies": ",".join(input_label(i) for i in dep_ids),
            "exact_p1": sum(exact) / len(exact),
            "candidate": candidate.name,
            "gate_cost": candidate.gate_cost,
            "mismatch": mismatches / len(exact),
            "bias": bias,
            "mse": mse,
            "weighted_abs": weight * sum(abs(error) for error in errors) / len(errors),
            "weighted_mse": (weight * weight) * mse,
        })
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-column", type=int, default=16)
    parser.add_argument("--top", type=int, default=8)
    parser.add_argument("--csv", type=Path,
                        default=ROOT / "tools" / "low_partial_product_candidates.csv")
    args = parser.parse_args()

    module = load_candidate()
    circuit, columns = module.build_partial_product_layout()
    dep_memo = {}
    rows = []
    for column, bucket in enumerate(columns):
        if column > args.max_column:
            break
        for node_id in bucket:
            rows.extend(analyze_node(circuit, node_id, column, dep_memo))

    args.csv.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0])
    with args.csv.open("w", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    by_node = defaultdict(list)
    for row in rows:
        by_node[row["node_id"]].append(row)
    print(f"raw layout: {len(circuit.nodes)} nodes, {len(rows)} candidate rows")
    print(f"wrote {args.csv}")
    print("\nBest candidates per node (zero-gate candidates first, then weighted MSE):")
    for node_id, node_rows in sorted(by_node.items(), key=lambda item: (int(item[1][0]["column"]), item[0])):
        ordered = sorted(node_rows, key=lambda r: (int(r["gate_cost"]), float(r["weighted_mse"]), abs(float(r["bias"]))))
        original = node_rows[0]
        print(f"col={original['column']:2} node={node_id:3} deps={original['dep_count']} "
              f"P1={float(original['exact_p1']):.4f} "
              f"best=" + "; ".join(
                  f"{r['candidate']} cost={r['gate_cost']} mis={float(r['mismatch']):.4f} "
                  f"bias={float(r['bias']):+.4f} wmse={float(r['weighted_mse']):.4g}"
                  for r in ordered[:args.top]))


if __name__ == "__main__":
    main()
