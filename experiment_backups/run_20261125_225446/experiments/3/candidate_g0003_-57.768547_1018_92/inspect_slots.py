"""Inspect original low-column slot IDs and source nodes."""
import importlib.util
from pathlib import Path
p=Path('/home/guoliang/multiplier/experiments/3/candidate_g0003_0001/parent.py')
s=importlib.util.spec_from_file_location('parent_inspection', p)
m=importlib.util.module_from_spec(s); s.loader.exec_module(m)
c=m.Candidate(); buses=c.setup(); columns=c._product_columns(*buses)
print('nodes',len(c.nodes),'slots',sum(map(len,columns)))
for col in range(7):
 print('COLUMN',col)
 for pos,n in enumerate(columns[col]):
  node=c.nodes[n]
  print(pos,n,node.kind,node.inputs)
for n in (91,149,228,416,474,553,94,160,226,419,485,551):
 print('CONE',n)
 seen=set()
 def walk(i,depth=0):
  if i in seen or depth>3: return
  seen.add(i); t=c.nodes[i]
  print(' '*depth,i,t.kind,t.inputs)
  for j in t.inputs: walk(j,depth+1)
 walk(n)
