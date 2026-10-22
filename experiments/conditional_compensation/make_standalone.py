"""Generate self-contained deliverable candidates and verify exact DAG identity.

Local inheritance preserves super() semantics, while all candidate/tool/support
imports are eliminated. The sole project dependency is tap2_9bit_multiplier.
"""
import ast
import importlib
import inspect
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from multiplier.circuit.multiplier.tap2_9bit_multiplier import MultiplierCircuit


def graph(c):
    return ([(n.kind,n.inputs) for n in c.nodes],c.input_ids,c.output_ids)


def generate(module):
    chain=[]
    for cls in module.Candidate.__mro__:
        if cls is MultiplierCircuit:break
        chain.append(cls)
    chain.reverse()
    text=['"""Standalone candidate. Local helper classes preserve construction order."""',
          'from __future__ import annotations',
          'from multiplier.circuit.multiplier.tap2_9bit_multiplier import (',
          '    Circuit, MultiplierCircuit, WIDTH, OUT_WIDTH, OUT_TOTAL,',
          ')','']
    # Exact-reference implementation uses free arithmetic helpers and a 19-bit
    # local width. Other candidates use their class attributes for parameters.
    if module.__name__.endswith('candidate_exact_rounding_optimized'):
        text.append('OUT_WIDTH = 19')
        tree=ast.parse(inspect.getsource(module))
        src=inspect.getsource(module)
        for node in tree.body:
            if isinstance(node,ast.FunctionDef) and node.name.startswith('_'):
                text.append(ast.get_source_segment(src,node))
    parent='MultiplierCircuit'
    for i,cls in enumerate(chain):
        tree=ast.parse(inspect.getsource(cls))
        node=tree.body[0]
        name='Candidate' if i==len(chain)-1 else '_Stage'+str(i)
        node.name=name
        node.bases=[ast.Name(id=parent,ctx=ast.Load())]
        # Strip inherited dead alternate emitters; active calls use the same
        # method names and super chain as before.
        node.body=[n for n in node.body if not (isinstance(n,ast.FunctionDef) and
                    n.name in ('_product_columns_parent1','_one_product_columns_parent1') and
                    module.__name__.split('.')[-1] not in ('candidate_g0000_0003','candidate_g0000_0005'))]
        text.append(ast.unparse(ast.fix_missing_locations(tree)))
        parent=name
    text.append('def build_circuit():\n    return Candidate()._build_circuit()\n')
    return '\n\n'.join(text)


def main():
    root=Path(__file__).resolve().parents[2]
    planned=[]
    for path in sorted((root/'initial_solutions').glob('*.py')):
        module=importlib.import_module('multiplier.initial_solutions.'+path.stem)
        original=module.build_circuit()
        code=generate(module)
        namespace={'__name__':'standalone_'+path.stem}
        exec(compile(code,str(path),'exec'),namespace)
        rebuilt=namespace['build_circuit']()
        assert graph(original)==graph(rebuilt),path
        assert original.gatecost().total==rebuilt.gatecost().total
        planned.append((path,code,original.gatecost().total))
    # All candidates must verify before any original file is replaced.
    report=[]
    for path,code,cost in planned:
        path.write_text(code)
        report.append(dict(file=path.name,cost=cost,entire_graph_identical=True))
        print(path.name,cost,'identical graph',flush=True)
    (Path(__file__).parent/'standalone_verification.json').write_text(json.dumps(report,indent=2))


if __name__=='__main__':main()
