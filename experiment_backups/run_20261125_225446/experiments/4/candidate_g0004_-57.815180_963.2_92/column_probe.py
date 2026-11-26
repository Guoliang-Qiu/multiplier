import importlib.util
from tools.circuit_kit.circuit.multiplier.conditional_compensation.node_set_information import build_experiment
p='/home/guoliang/multiplier/experiments/4/candidate_g0004_0000/parent.py'
s=importlib.util.spec_from_file_location('parent',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
x=m.Candidate(); buses=x.setup(); cols=x._product_columns(*buses)
for k in range(4,7):
 print('COLUMN',k)
 for j,n in enumerate(cols[k]):
  v=x.nodes[n]; print(j,n,v.kind,list(v.inputs),[(i,x.nodes[i].kind,list(x.nodes[i].inputs)) for i in v.inputs])
print('SLOTS',sum(map(len,cols)),'NODES',len(x.nodes))
for slot in ([(4,0)],[(4,1)],[(4,2)],[(4,3)],[(4,4)],[(4,5)],[(5,0)],[(5,1)],[(5,2)],[(5,3)],[(5,4)],[(5,5)],[(5,6)],[(5,7)]):
 try:
  b,d,_,_=build_experiment(m.Candidate,slot)
  print(slot,'saving',b.gatecost().total-d.gatecost().total,'deleted',d.gatecost().total)
 except Exception as e: print(slot,'ERROR',str(e))
