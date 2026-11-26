import importlib.util
from pathlib import Path
p=Path('/home/guoliang/multiplier/experiments/5/candidate_g0005_0003/parent.py')
s=importlib.util.spec_from_file_location('parent_candidate',p); m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
c=m.Candidate(); c._columns=c._product_columns(*c.setup())
for col in range(10):
 print('COLUMN',col,'COUNT',len(c._columns[col]))
 for pos,n in enumerate(c._columns[col]):
  node=c.nodes[n];print(' ',pos,n,node.kind,list(node.inputs))
print('TOTAL',sum(map(len,c._columns)),'NODES',len(c.nodes))
