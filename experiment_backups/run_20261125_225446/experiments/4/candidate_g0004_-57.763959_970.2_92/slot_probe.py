from pathlib import Path
from gate_cost import load_module
p=Path('/home/guoliang/multiplier/experiments/4/candidate_g0004_0008/parent.py')
c=load_module(p).Candidate(); buses=c.setup(); cols=c._product_columns(*buses)
for i in range(6):
 print('COLUMN',i, 'length',len(cols[i]))
 for j,n in enumerate(cols[i]):
  node=c.nodes[n]
  print(j,n,node.kind,node.inputs)
print('input ids:',[(i,n,c.nodes[n].kind) for i,n in enumerate(c.input_ids)])
