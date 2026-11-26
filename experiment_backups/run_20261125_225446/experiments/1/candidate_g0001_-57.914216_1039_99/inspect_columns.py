import importlib.util
from pathlib import Path
p=Path('/home/guoliang/multiplier/experiments/1/candidate_g0001_0005/parent.py')
s=importlib.util.spec_from_file_location('parent_inspect',p); m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
c=m.Candidate(); buses=c.setup(); cols=c._product_columns(*buses)
print('prefix nodes',len(c.nodes),'slots',sum(map(len,cols)))
for col in range(7):
 print('COLUMN',col,[(i,n,c.nodes[n].kind,c.nodes[n].inputs) for i,n in enumerate(cols[col])])
for n in [91,420,421,425]:
 print('EXISTING',n,c.nodes[n].kind,c.nodes[n].inputs)
