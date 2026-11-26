import importlib.util
from pathlib import Path
from tools.circuit_kit.circuit.multiplier.conditional_compensation.node_set_information import build_experiment
p=Path('/home/guoliang/multiplier/experiments/5/candidate_g0005_0004/parent.py')
s=importlib.util.spec_from_file_location('parent_inspect',p); m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
x=m.Candidate(); buses=x.setup();cols=x._product_columns(*buses)
for i in range(4,9):
 print('COLUMN',i,'length',len(cols[i]))
 for j,n in enumerate(cols[i]):
  node=x.nodes[n];print(' ',j,n,node.kind,node.inputs, 'input kinds',[(v,x.nodes[v].kind) for v in node.inputs])
print('INPUTS',[(i,x.nodes[i].kind) for i in range(2,38)])
for slots in ([(5,0)],[(5,1)],[(5,2)],[(4,0)],[(4,1)],[(5,0),(5,1)]):
 base,deleted,_,_=build_experiment(m.Candidate,slots)
 print('SAVINGS',slots,base.gatecost().total-deleted.gatecost().total, 'deleted',deleted.gatecost().total)
 reachable=set()
 def walk(n):
  if n in reachable:return
  reachable.add(n)
  for k in deleted.nodes[n].inputs:walk(k)
 for n in deleted.output_ids:walk(n)
 for col,pos in slots:
  n=cols[col][pos]; node=x.nodes[n]
  print(' REMOVED',col,pos,n,node.kind,node.inputs)
  for k in (n,*node.inputs):
   v=x.nodes[k];print('  SIGNAL',k,v.kind,v.inputs,'retained' if k in reachable else 'dead')
