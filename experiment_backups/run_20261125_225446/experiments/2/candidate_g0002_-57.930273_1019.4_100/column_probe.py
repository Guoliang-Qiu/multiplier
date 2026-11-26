import importlib.util
from pathlib import Path
p=Path('/home/guoliang/multiplier/experiments/2/candidate_g0002_0006/parent.py')
s=importlib.util.spec_from_file_location('parent',p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m)
c=m.Candidate(); columns=c._product_columns(*c.setup())
print('pre-compression nodes',len(c.nodes),'slots',sum(map(len,columns)))
for col in range(7):
 print('COLUMN',col,'slots',len(columns[col]))
 for pos,n in enumerate(columns[col]):
  node=c.nodes[n]
  print(' ',(col,pos),'id',n,'kind',node.kind,'inputs',node.inputs)
print('HIGH COLUMNS',[(k,len(v)) for k,v in enumerate(columns) if k>=7])
