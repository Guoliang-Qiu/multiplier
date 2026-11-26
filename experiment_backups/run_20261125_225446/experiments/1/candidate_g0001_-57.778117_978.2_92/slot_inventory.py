import importlib.util
from pathlib import Path
p=Path('/home/guoliang/multiplier/experiments/1/candidate_g0001_0003/parent.py')
s=importlib.util.spec_from_file_location('parent',p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m)
c=m.Candidate(); buses=c.setup(); cols=c._product_columns(*buses)
for k in range(0,9):
 print('column',k,[(i,n,c.nodes[n].kind, c.nodes[n].inputs) for i,n in enumerate(cols[k])])
print('inputs',[(i,c.nodes[i].kind) for i in range(38)])
print('total slots',sum(map(len,cols)))
for target in [152,466,538,405,94,162,222,408,476,536,667]:
 print('\nCONE',target)
 seen=set()
 def visit(n,depth):
  if n in seen or depth > 5:return
  seen.add(n); node=c.nodes[n]; print('  '*depth,n,node.kind,node.inputs)
  for sub in node.inputs: visit(sub,depth+1)
 visit(target,0)
