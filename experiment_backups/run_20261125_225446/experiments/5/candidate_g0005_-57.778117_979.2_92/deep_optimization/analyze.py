"""Analyze reachability and local gate identities for general optimization."""
import importlib.util
from collections import Counter
from pathlib import Path
p=Path(__file__).with_name('general.py')
spec=importlib.util.spec_from_file_location('candidate',p)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
c=m.build_circuit(); c.validate()
reach=set(c.output_ids)
for i in range(len(c.nodes)-1,-1,-1):
 if i in reach: reach.update(c.nodes[i].inputs)
print('reachable',len(reach),'total',len(c.nodes),'cost',c.gatecost().total)
counts=Counter()
for i in reach:
 n=c.nodes[i]
 if n.kind in ('AND','OR'):
  a,b=n.inputs
  for x,y in ((a,b),(b,a)):
   ny=c.nodes[y]
   if ny.kind=='NOT':
    z=ny.inputs[0];nz=c.nodes[z]
    if nz.kind in ('AND','OR') and x in nz.inputs: counts[(n.kind,'NOT_'+nz.kind,'contains')]+=1
   if ny.kind in ('AND','OR') and x in ny.inputs: counts[(n.kind,ny.kind,'contains')]+=1
   if ny.kind=='NOT' and c.nodes[x].kind=='NOT': counts[(n.kind,'both_not')]+=1
print(counts)
print('columns after compression',[(i,len(x),[c.nodes[v].kind for v in x]) for i,x in enumerate(c._columns)])
