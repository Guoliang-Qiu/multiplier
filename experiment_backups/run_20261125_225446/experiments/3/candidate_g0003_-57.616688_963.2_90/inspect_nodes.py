import importlib.util
p='/home/guoliang/multiplier/experiments/3/candidate_g0003_0002/parent.py'
s=importlib.util.spec_from_file_location('parent',p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m)
c=m.Candidate(); c._columns=c._product_columns(*c.setup())
for k in range(4,8):
 print('COLUMN',k)
 for j,n in enumerate(c._columns[k]):
  node=c.nodes[n]; print(j,n,node.kind,node.inputs)
print('COUNT',sum(map(len,c._columns)),'NODES',len(c.nodes))
