import importlib.util
from pathlib import Path
p=Path('/home/guoliang/multiplier/experiments/2/candidate_g0002_0007/parent.py')
s=importlib.util.spec_from_file_location('parent',p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m)
c=m.Candidate(); buses=c.setup(); cols=c._product_columns(*buses)
for k,bucket in enumerate(cols):
    print('column',k,'slots',len(bucket),'nodes',[(j,n,c.nodes[n].kind,c.nodes[n].inputs) for j,n in enumerate(bucket)])
print('node 410..454',[(n,c.nodes[n].kind,c.nodes[n].inputs) for n in range(410,455)])
