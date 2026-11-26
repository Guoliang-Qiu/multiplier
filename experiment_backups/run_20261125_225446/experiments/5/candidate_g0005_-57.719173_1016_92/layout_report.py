import importlib.util, json
p='/home/guoliang/multiplier/experiments/5/candidate_g0005_0007/parent.py'
spec=importlib.util.spec_from_file_location('parent',p); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
c=mod.Candidate(); buses=c.setup(); cols=c._product_columns(*buses)
for i in range(7):
 print('COLUMN',i, [(j,n,c.nodes[n].kind,tuple(c.nodes[n].inputs)) for j,n in enumerate(cols[i])])
print('slots',sum(map(len,cols)),'nodes',len(c.nodes))
with open('/home/guoliang/multiplier/generations/pareto_archive/archive.json') as f: a=json.load(f)
print('PARETO',[(r['objectives']) for r in a['records']])
