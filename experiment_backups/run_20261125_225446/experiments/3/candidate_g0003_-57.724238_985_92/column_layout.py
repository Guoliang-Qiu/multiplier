import importlib.util, json
from pathlib import Path
p=Path('/home/guoliang/multiplier/experiments/3/candidate_g0003_0000/parent.py')
s=importlib.util.spec_from_file_location('parent_inspection',p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m)
c=m.Candidate(); a,b,x,d,z,o=c.setup(); cols=c._product_columns(a,b,x,d,z,o)
for j in range(4,10):
 print('COLUMN',j,[(i,n,c.nodes[n].kind,c.nodes[n].inputs) for i,n in enumerate(cols[j])])
print('BASE',len(c.nodes),sum(map(len,cols)))
archive=json.loads(Path('/home/guoliang/multiplier/generations/pareto_archive/archive.json').read_text())
print('PARETO',[(r['source_path'].split('/')[-1],r['objectives']) for r in archive['records']])
