import importlib.util, json
from pathlib import Path
from tools.circuit_kit.circuit.multiplier.conditional_compensation.node_set_information import build_experiment
p=Path('/home/guoliang/multiplier/experiments/5/candidate_g0005_0008/parent.py')
s=importlib.util.spec_from_file_location('parent',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
c=m.Candidate(); buses=c.setup(); cols=c._product_columns(*buses)
for j in range(7):
 print('column',j,'size',len(cols[j]))
 for i,n in enumerate(cols[j]):
  node=c.nodes[n]; print('  ',i,n,node.kind, node.inputs)
print('prefix nodes',len(c.nodes))
for slots in ([[4,0]],[[4,1]],[[4,2]],[[5,0]],[[5,1]],[[5,2]],[[4,0],[4,1]],[[5,0],[5,1]]):
 b,d,_,_=build_experiment(m.Candidate, slots)
 print('slots',slots,'base',b.gatecost().total,'deleted',d.gatecost().total,'saving',round(b.gatecost().total-d.gatecost().total,2))
a=json.loads(Path('/home/guoliang/multiplier/generations/pareto_archive/archive.json').read_text())
print('archive objectives', [r['objectives'] for r in a['records']])
