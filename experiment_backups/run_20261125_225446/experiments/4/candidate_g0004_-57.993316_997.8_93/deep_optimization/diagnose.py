import importlib.util
from collections import Counter
p='experiments/4/candidate_g0004_0001/partial_product_candidate.py'
s=importlib.util.spec_from_file_location('candidate',p); m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
c=m.Candidate(); counts=Counter();old=c._add3
def add3(x,y,z):
 counts[('constant',sum(v in (c._zero,c._one) for v in (x,y,z)))]+=1
 if len({x,y,z})<3: counts['repeated']+=1
 return old(x,y,z)
c._add3=add3
original=c._build_outputs
def outputs():
 print('compressed',[(i,len(v),v[:]) for i,v in enumerate(c._columns)])
 original()
c._build_outputs=outputs;c._build_circuit();print(counts);print('columns',c.partial_product_count);print('output',c.output_ids)
for i,n in enumerate(c.nodes):
 if i<50: print(i,n.kind,n.inputs)
