"""Cost-bounded SMT synthesis of G(X) under an integer error-table budget."""
from __future__ import annotations

import argparse
from datetime import datetime
from decimal import Decimal, ROUND_FLOOR, localcontext
import json
from pathlib import Path
import signal
import sys

import numpy as np
import z3

from .compensation_error_table import _load_candidate, evaluate_truth_table
from .node_set_information import build_experiment

HARD_INSTANCES_DIR = Path(__file__).resolve().parent / "hard_instances"
OPS = ("AND", "OR", "XOR", "NOT", "WIRE")
COSTS = (1, 1, 3, 0, 0)


def error_budget(metadata, target_db):
    """Convert dB once outside SMT; table and SMT arithmetic remain integers."""
    target = Decimal(str(target_db))
    if not target.is_finite():
        raise ValueError("target_evm_db must be finite")
    with localcontext() as context:
        context.prec = 80
        value = Decimal(metadata["reference_squared_sum"]) * (Decimal(10) ** (target / 10))
        return int(value.to_integral_value(rounding=ROUND_FLOOR))


def _select(index, values):
    result = values[-1]
    for i in range(len(values) - 2, -1, -1):
        result = z3.If(index == i, values[i], result)
    return result


def build_solver(table, num_inputs, num_outputs, max_gates, budget, timeout_ms):
    """Topological gate slots carry bit-vector truth tables (LSB = state 0).

    WIRE is an inactive slot, not an emitted gate. Thus max_gates is a hard
    physical-gate bound even though NOT has zero weighted cost.
    """
    rows = 1 << num_inputs
    solver = z3.Solver()
    solver.set(timeout=timeout_ms)
    sources = [z3.BitVecVal(sum(((x >> bit) & 1) << x for x in range(rows)), rows)
               for bit in range(num_inputs)]
    sources += [z3.BitVecVal(0, rows), z3.BitVecVal((1 << rows) - 1, rows)]
    gates, costs = [], []
    for i in range(max_gates):
        op, a, b = z3.Ints(f"op_{i} a_{i} b_{i}")
        value = z3.BitVec(f"value_{i}", rows)
        solver.add(op >= 0, op < len(OPS), a >= 0, a < len(sources), b >= 0, b < len(sources))
        solver.add(z3.If(op < 3, a <= b, a == b))
        left, right = _select(a, sources), _select(b, sources)
        solver.add(value == _select(op, [left & right, left | right, left ^ right, ~left, left]))
        sources.append(value)
        costs.append(_select(op, [z3.IntVal(c) for c in COSTS]))
        gates.append((op, a, b))
    outputs = [z3.Int(f"out_{i}") for i in range(num_outputs)]
    output_values = []
    for output in outputs:
        solver.add(output >= 0, output < len(sources))
        output_values.append(_select(output, sources))
    losses = []
    for x, row in enumerate(table):
        code = z3.Sum([z3.If(z3.Extract(x, x, v) == 1, 1 << j, 0)
                       for j, v in enumerate(output_values)])
        losses.append(_select(code, [z3.IntVal(int(v)) for v in row]))
    solver.add(z3.Sum(losses) <= budget)
    return solver, gates, outputs, z3.Sum(costs)


def decode(model, gates, outputs, num_inputs):
    nodes = [{"kind": "INPUT", "inputs": [], "index": i} for i in range(num_inputs)]
    nodes += [{"kind": "ZERO", "inputs": []}, {"kind": "ONE", "inputs": []}]
    mapping = list(range(len(nodes)))
    for op, a, b in gates:
        kind = OPS[model.eval(op).as_long()]
        left, right = mapping[model.eval(a).as_long()], mapping[model.eval(b).as_long()]
        if kind == "WIRE":
            mapping.append(left)
        else:
            mapping.append(len(nodes))
            nodes.append({"kind": kind, "inputs": [left] if kind == "NOT" else [left, right]})
    output_ids = [mapping[model.eval(o).as_long()] for o in outputs]
    reachable = set(range(num_inputs + 2))

    def visit(node):
        if node in reachable:
            return
        reachable.add(node)
        for source in nodes[node]["inputs"]:
            visit(source)

    for output in output_ids:
        visit(output)
    remap = {old: new for new, old in enumerate(sorted(reachable))}
    compact = [{**nodes[i], "inputs": [remap[j] for j in nodes[i]["inputs"]]} for i in sorted(reachable)]
    return {"nodes": compact, "input_ids": list(range(num_inputs)),
            "output_ids": [remap[i] for i in output_ids]}


def truth_table(circuit):
    result = []
    for x in range(1 << len(circuit["input_ids"])):
        values = []
        for node in circuit["nodes"]:
            kind, ins = node["kind"], node["inputs"]
            if kind == "INPUT":
                value = (x >> node["index"]) & 1
            elif kind in {"ZERO", "ONE"}:
                value = int(kind == "ONE")
            elif kind == "NOT":
                value = 1 - values[ins[0]]
            else:
                a, b = (values[j] for j in ins)
                value = {"AND": a & b, "OR": a | b, "XOR": a ^ b}[kind]
            values.append(value)
        result.append(sum(values[node] << bit for bit, node in enumerate(circuit["output_ids"])))
    return result


def instantiate_compensation(circuit, node_ids, netlist):
    """Add the synthesized G DAG to an initialized candidate; return output IDs.

    This only emits G. Exact addition to the deleted raw result must be
    implemented separately; inserting into approximate compressors is not
    automatically equivalent to the error-table model.
    """
    if len(node_ids) != len(netlist["input_ids"]):
        raise ValueError("X width does not match synthesized circuit")
    mapped = []
    for node in netlist["nodes"]:
        kind = node["kind"]
        if kind == "INPUT":
            value = node_ids[node["index"]]
        elif kind in {"ZERO", "ONE"}:
            value = circuit._zero if kind == "ZERO" else circuit._one
        else:
            value = circuit._gate(kind, *(mapped[i] for i in node["inputs"]))
        mapped.append(value)
    return [mapped[i] for i in netlist["output_ids"]]


def synthesize(table, metadata, savings, target_evm_db, *, max_gates=None, timeout_ms=60000):
    if type(savings) is not int or savings < 0:
        raise ValueError("deletion must save nonnegative weighted cost")
    cap = savings if max_gates is None else max_gates
    if type(cap) is not int or not 0 <= cap <= savings:
        raise ValueError("max_gates must be between zero and the measured deletion saving")
    if type(timeout_ms) is not int or timeout_ms <= 0:
        raise ValueError("timeout_ms must be positive")
    n, m = metadata["num_inputs"], metadata["num_outputs"]
    if not 0 <= n <= 16 or not 1 <= m <= 3:
        raise ValueError("invalid input/output widths")
    if table.shape != (1 << n, 1 << m) or table.dtype != np.int64 or np.any(table < 0):
        raise ValueError("error table must be nonnegative int64 with the declared dimensions")
    if metadata["reference_squared_sum"] <= 0:
        raise ValueError("positive reference energy required for an EVM constraint")
    if metadata["error_scale"] != 16384 or metadata["sampling"]["count"] <= 0:
        raise ValueError("expected the integer error-table scale and a positive sample count")
    budget = error_budget(metadata, target_evm_db)
    base = {"saved_cost": savings, "max_gates": cap, "target_evm_db": target_evm_db,
            "integer_error_budget": budget, "gate_costs": dict(zip(OPS[:4], COSTS[:4]))}
    if sum(int(min(row)) for row in table) > budget:
        return {**base, "status": "unsat", "reason": "Even unrestricted G truth tables exceed the error budget"}
    solver = None
    bound = 0
    try:
        solver, gates, outputs, cost = build_solver(table, n, m, cap, budget, timeout_ms)
        for bound in range(savings + 1):
            print(f"[compensation_synth] gates<={cap}, weighted_cost<={bound}", file=sys.stderr, flush=True)
            solver.push()
            solver.add(cost <= bound)
            status = solver.check()
            if status == z3.sat:
                netlist = decode(solver.model(), gates, outputs, n)
                codes = truth_table(netlist)
                metrics = evaluate_truth_table(metadata, table, codes)
                gate_nodes = [node for node in netlist["nodes"] if node["kind"] in OPS[:4]]
                actual_cost = sum(COSTS[OPS.index(node["kind"])] for node in gate_nodes)
                assert metrics["scaled_squared_error_sum"] <= budget
                assert len(gate_nodes) <= cap and actual_cost <= bound
                return {**base, "status": "sat", "weighted_cost": actual_cost,
                        "gates": len(gate_nodes), "circuit": netlist, "output_codes": codes,
                        "metrics": metrics, "optimal_within_gate_cap": True}
            if status != z3.unsat:
                reason = solver.reason_unknown()
                return {**base, "status": "timeout" if "timeout" in reason.lower() else "unknown",
                        "reason": reason, "current_cost_bound": bound,
                        "proven_unsat_cost_below": bound, "smt2": solver.to_smt2()}
            solver.pop()
    except KeyboardInterrupt:
        return {**base, "status": "interrupted", "current_cost_bound": bound,
                "proven_unsat_cost_below": bound,
                "smt2": solver.to_smt2() if solver is not None else None}
    return {**base, "status": "unsat", "reason": "No circuit within deletion saving and gate cap"}


def archive_instance(config, metadata, table, result):
    directory = HARD_INSTANCES_DIR / datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    directory.mkdir(parents=True)
    np.save(directory / "error_table.npy", table, allow_pickle=False)
    (directory / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    (directory / "config.json").write_text(json.dumps(config, indent=2) + "\n")
    smt = result.pop("smt2", None)
    if smt:
        (directory / "problem.smt2").write_text(smt)
    (directory / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    return str(directory)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    config = json.loads(args.config.read_text())

    def resolve(value):
        path = Path(value)
        return path.resolve() if path.is_absolute() else (args.config.resolve().parent / path).resolve()

    table_path = resolve(config["error_table"])
    metadata = json.loads(table_path.with_suffix(".json").read_text())
    configured_node_ids = config.get("node_ids")
    configured_columns = config.get("compensation_columns")
    if configured_node_ids is None or configured_columns is None:
        raise ValueError("synthesis config must explicitly provide node_ids and compensation_columns")
    if list(configured_node_ids) != list(metadata["node_ids"]):
        raise ValueError("config node_ids do not match the error-table metadata")
    if list(configured_columns) != list(metadata["compensation_columns"]):
        raise ValueError("config compensation_columns do not match the error-table metadata")
    metadata = {**metadata, "node_ids": list(configured_node_ids),
                "compensation_columns": list(configured_columns)}
    table = np.load(table_path, allow_pickle=False)
    candidate = _load_candidate(resolve(config["implementation"]))
    baseline, deleted, _, _ = build_experiment(candidate, metadata["removed_slots"])
    savings = baseline.gatecost().total - deleted.gatecost().total
    # Signals are handled as interruptions so the unfinished bound is archived.
    def interrupt(_signum, _frame):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, interrupt)
    result = synthesize(table, metadata, savings, config["target_evm_db"],
                        max_gates=config.get("max_gates"), timeout_ms=config.get("timeout_ms", 60000))
    result["node_ids"] = metadata["node_ids"]
    result["compensation_columns"] = metadata["compensation_columns"]
    result["baseline_cost"] = baseline.gatecost().total
    result["deleted_cost"] = deleted.gatecost().total
    if result["status"] in {"timeout", "unknown", "interrupted"}:
        result["hard_instance"] = archive_instance(config, metadata, table, result)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")


if __name__ == "__main__":
    main()
