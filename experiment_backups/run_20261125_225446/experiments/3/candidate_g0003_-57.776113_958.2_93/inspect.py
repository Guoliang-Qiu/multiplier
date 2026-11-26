import importlib.util, json
p='/home/guoliang/multiplier/experiments/3/candidate_g0003_0005/parent.py'
s=importlib.util.spec_from_file_location('parent',p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m)
c=m.Candidate(); c._columns=c._product_columns(*c.setup())
for i in range(6):
 print('column',i, 'count',len(c._columns[i]),[(j,n,c.nodes[n].kind, c.nodes[n].inputs) for j,n in enumerate(c._columns[i])])
print('node_count',len(c.nodes));print('input_ids',c.input_ids)
