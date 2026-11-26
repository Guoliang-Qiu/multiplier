import importlib.util
from pathlib import Path
from tools.circuit_kit.circuit.multiplier.conditional_compensation.node_set_information import build_experiment
p=Path('/home/guoliang/multiplier/experiments/4/candidate_g0004_0002/parent.py')
s=importlib.util.spec_from_file_location('parent',p); m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
c=m.Candidate(); buses=c.setup(); cols=c._product_columns(*buses)
print('prefix nodes',len(c.nodes),'slot count',sum(map(len,cols)))
for i in range(7):
 print('column',i,[(j,k,c.nodes[k].kind,c.nodes[k].inputs) for j,k in enumerate(cols[i])])
for slots in ([[4,0]],[[4,1]],[[4,2]],[[4,3]],[[4,0],[4,1]],[[4,0],[4,2]],[[4,1],[4,2]],[[4,0],[4,1],[4,2]],[[5,0]],[[5,1]],[[5,2]]):
 try:
  a,b,_,_=build_experiment(m.Candidate,slots)
  print(slots,'cost',a.gatecost().total,b.gatecost().total,'saving',round(a.gatecost().total-b.gatecost().total,2))
 except Exception as e:print(slots,'error',repr(e))
