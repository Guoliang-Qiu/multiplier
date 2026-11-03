"""Export a synthesized G as a standalone, complete compensated candidate."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import pprint

import numpy as np

from multiplier.circuit.multiplier.tap2_9bit_multiplier import OUT_TOTAL
from .compensation_error_table import _load_candidate, evaluate_truth_table
from .node_set_information import build_experiment
from .synthesize import instantiate_compensation, truth_table, error_budget
from .array_compensation import MODEL, prepare, finish


def build_compensated_candidate(implementation, metadata, synthesis, table):
    """Insert G into the partial-product array before compression and CPA."""
    if metadata.get('compensation_model') != MODEL:
        raise ValueError('Regenerate error table using the pre-compression model')
    if synthesis.get("status") != "sat":
        raise ValueError("a SAT synthesis result is required")
    for key in ("node_ids", "compensation_columns"):
        if synthesis[key] != metadata[key]:
            raise ValueError(f"synthesis and error-table metadata disagree on {key}")
    columns = metadata["compensation_columns"]
    if not 1 <= len(columns) <= 3 or any(type(c) is not int or not 0 <= c < OUT_TOTAL for c in columns):
        raise ValueError("expected one to three valid compensation columns")
    netlist = synthesis["circuit"]
    if len(netlist["output_ids"]) != len(columns):
        raise ValueError("G output width does not match compensation columns")
    codes = truth_table(netlist)
    if codes != synthesis["output_codes"]:
        raise ValueError("synthesized netlist does not match its reported truth table")
    metrics = evaluate_truth_table(metadata, table, codes)
    budget = error_budget(metadata, synthesis["target_evm_db"])
    if metrics["scaled_squared_error_sum"] > budget:
        raise ValueError("synthesized circuit exceeds target error budget")

    baseline, candidate, _, prefix_size = build_experiment(implementation, metadata["removed_slots"])
    nodes = metadata["node_ids"]
    if any(type(n) is not int or not 0 <= n < prefix_size or
           candidate.nodes[n].kind in {"ZERO", "ONE"} for n in nodes):
        raise ValueError("X IDs are not valid nonconstant pre-compression nodes")
    base_cost = baseline.gatecost().total
    deleted_cost = candidate.gatecost().total
    candidate = prepare(implementation, metadata['removed_slots'])
    remaining_terms = sum(n not in (candidate._zero, candidate._one)
                          for bucket in candidate._columns for n in bucket)
    g_nodes = instantiate_compensation(candidate, nodes, netlist)
    finish(candidate, columns, g_nodes)
    final_cost = candidate.gatecost().total
    return candidate, {
        "baseline_cost": base_cost,
        "deleted_cost": deleted_cost,
        "compensation_model": MODEL,
        "nonconstant_terms_upper_bound": remaining_terms + len(g_nodes),
        "final_cost": final_cost,
        "net_cost_saving": base_cost - final_cost,
        "strict_cost_improvement": final_cost < base_cost,
        "target_evm_db": synthesis["target_evm_db"],
        "table_metrics": metrics,
        "performance_basis": "pre-compression insertion followed by original compressor and CPA; verify full candidate",
    }


def candidate_source(circuit):
    """Freeze the reachable graph; generated code requires only the base package."""
    reachable = set(circuit.reachable_node_ids()) | set(circuit.input_ids)
    ids = sorted(reachable)
    remap = {old: new for new, old in enumerate(ids)}
    graph = [(circuit.nodes[i].kind, tuple(remap[j] for j in circuit.nodes[i].inputs)) for i in ids]
    input_ids = [remap[i] for i in circuit.input_ids]
    output_ids = [remap[i] for i in circuit.output_ids]
    return '''"""Frozen compensated candidate exported from a synthesized G network.

The graph includes the modified partial products, G, original compressor and CPA.
Columns here are final result bits, not the original partial-product layout;
do not use this frozen export for another low-partial-product deletion search.
"""
from multiplier.circuit.multiplier.tap2_9bit_multiplier import MultiplierCircuit

_GRAPH = %s
_INPUT_IDS = %r
_OUTPUT_IDS = %r


class Candidate(MultiplierCircuit):
    def _product_columns(self, a, b, c, d, zero, one):
        mapping = dict(zip(_INPUT_IDS, a + b + c + d))
        for index, (kind, sources) in enumerate(_GRAPH):
            if index in mapping:
                continue
            if kind == "ZERO":
                mapping[index] = zero
            elif kind == "ONE":
                mapping[index] = one
            else:
                mapping[index] = self.add(kind, *(mapping[s] for s in sources))
        return [[mapping[node]] for node in _OUTPUT_IDS]

    def _compress_columns(self):
        pass  # Already reduced to the complete result bus in the frozen DAG.

    def _build_outputs(self):
        self.output_ids = [bucket[0] for bucket in self._columns]


def build_circuit():
    return Candidate()._build_circuit()
''' % (pprint.pformat(graph, width=100), input_ids, output_ids)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path)
    parser.add_argument("--output", required=True, type=Path, help="new candidate .py inside the active workspace")
    args = parser.parse_args()
    output = args.output.resolve()
    workspace = Path(os.environ.get("MULTIPLIER_ROOT", Path.cwd())).resolve()
    if output.suffix != ".py" or workspace not in output.parents:
        parser.error("output must be a .py file inside the active workspace")
    if output.exists() or output.with_suffix(".json").exists():
        parser.error("output candidate or companion report already exists; choose a new name")
    config = json.loads(args.config.read_text())

    def resolve(key):
        return (args.config.resolve().parent / config[key]).resolve()

    table_path = resolve("error_table")
    metadata = json.loads(table_path.with_suffix(".json").read_text())
    synthesis = json.loads(resolve("synthesis_result").read_text())
    candidate, report = build_compensated_candidate(
        _load_candidate(resolve("implementation")), metadata, synthesis,
        np.load(table_path, allow_pickle=False),
    )
    output.write_text(candidate_source(candidate))
    report["candidate_file"] = str(output)
    output.with_suffix(".json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps(report, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
