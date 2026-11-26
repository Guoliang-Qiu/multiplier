import importlib.util
from pathlib import Path
p=Path('/home/guoliang/multiplier/experiments/2/candidate_g0002_0004/partial_product_candidate.py')
s=importlib.util.spec_from_file_location('seed',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
x=m.Candidate();a,b,c,d,z,o=x.setup();cols=x._product_columns(a,b,c,d,z,o)
for n in (91,150,420,421,425,494):
 node=x.nodes[n];print('NODE',n,node.kind,node.inputs)
for k in (2,3,4,5,6,7,8,9,10): print('COL',k,cols[k])
print('pre slots',sum(map(len,cols)),'nodes',len(x.nodes))
