"""Audit current candidates, propose conservative simplifications, verify DAGs.

No deletion of candidates is performed by this script. Reports identify the
dominated set for explicit review and deletion.
"""
import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT.parent))


def load(path):
    spec = importlib.util.spec_from_file_location('audit_candidate', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def signature(c):
    return c.nodes, c.input_ids, c.output_ids, c.gatecost()


def simplify(text):
    tree = ast.parse(text)
    candidate = next(n for n in tree.body if isinstance(n, ast.ClassDef))
    removals = []
    policy = next((n for n in candidate.body if isinstance(n, ast.Assign)
                   and isinstance(n.targets[0], ast.Name)
                   and n.targets[0].id == '_USE_ABSORPTION'), None)
    if policy is not None and isinstance(policy.value, ast.Constant) and policy.value.value is False:
        # False OR argument is identical to the inherited method's argument.
        gate = next((n for n in candidate.body if isinstance(n, ast.FunctionDef) and n.name == '_gate'), None)
        if gate and len(gate.body) == 1 and isinstance(gate.body[0], ast.Return):
            expected = 'return super()._gate(kind, *inputs, absorption=absorption or self._USE_ABSORPTION)'
            if ast.unparse(gate.body[0]) == expected:
                removals.extend([policy, gate])
    loads = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}
    for n in ast.walk(candidate):
        if (isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name)
                and n.target.id in ('step1_one', 'step1_two') and n.target.id not in loads):
            removals.append(n)
    lines = text.splitlines(keepends=True)
    for node in sorted(removals, key=lambda n:n.lineno, reverse=True):
        del lines[node.lineno-1:node.end_lineno]
    return ''.join(lines), len(removals)


def main():
    report = []
    env = dict(os.environ, TAP2_COPIES='8', OPENBLAS_NUM_THREADS='1')
    for path in sorted((ROOT/'initial_solutions').glob('*.py')):
        original = load(path).build_circuit()
        text, edits = simplify(path.read_text())
        namespace = {'__name__':'simplified_candidate'}
        exec(compile(text, str(path), 'exec'), namespace)
        new = namespace['build_circuit']()
        assert signature(original) == signature(new), path
        original.validate(); new.validate()
        if edits:
            path.write_text(text)
        result = subprocess.run([sys.executable,'eval.py',str(path)], cwd=ROOT,
            env=env, text=True, capture_output=True, check=True, timeout=1200)
        metrics = json.loads(result.stdout)
        row = dict(file=path.name, gate_cost=new.gatecost().total, **metrics,
                   removed_redundant_definitions=edits, full_graph_unchanged=True,
                   sha256=hashlib.sha256(text.encode()).hexdigest())
        report.append(row)
        Path(__file__).with_suffix('.json').write_text(json.dumps(report,indent=2))
        print(path.name,row['gate_cost'],row['evm_db'],'simplifications',edits,flush=True)
    for r in report:
        r['dominated_by']=[s['file'] for s in report if
            s['gate_cost']<=r['gate_cost'] and s['evm_db']<=r['evm_db'] and
            (s['gate_cost']<r['gate_cost'] or s['evm_db']<r['evm_db'])]
    Path(__file__).with_suffix('.json').write_text(json.dumps(report,indent=2))
    for r in report:
        if r['dominated_by']:print('REMOVE',r['file'],r['dominated_by'],flush=True)


if __name__=='__main__':main()
