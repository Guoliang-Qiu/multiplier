"""Inspect the parent pre-compression layout and retained node cones."""
import importlib.util
from pathlib import Path
from tools.circuit_kit.circuit.multiplier.conditional_compensation.node_set_information import build_experiment
p = Path('/home/guoliang/multiplier/experiments/2/candidate_g0002_0004/parent.py')
spec = importlib.util.spec_from_file_location('parent_inspect', p)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
c = m.Candidate()
buses = c.setup()
cols = c._product_columns(*buses)
for col in range(7):
    print('COLUMN', col)
    for pos, nid in enumerate(cols[col]):
        n = c.nodes[nid]
        print(' ', pos, nid, n.kind, tuple(n.inputs))
print('prefix nodes',len(c.nodes),'slots',sum(map(len,cols)))
for slots in ([(4,0)],[(4,0),(4,3)],[(5,0)],[(3,1)],[(4,0),(4,3),(5,0)]):
    a,b,_,_=build_experiment(m.Candidate, slots)
    print('delete',slots,'costs',a.gatecost().total,b.gatecost().total,'saving',a.gatecost().total-b.gatecost().total)
