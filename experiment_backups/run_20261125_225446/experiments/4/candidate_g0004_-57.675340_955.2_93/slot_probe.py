import json
from pathlib import Path
import importlib.util
p=Path('/home/guoliang/multiplier/experiments/4/candidate_g0004_0005/parent.py')
s=importlib.util.spec_from_file_location('parent_inspect',p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m)
c=m.Candidate(); cols=c._product_columns(*c.setup())
for i in range(4,11):
 print('COLUMN',i,[(j,n,c.nodes[n].kind,tuple(c.nodes[n].inputs)) for j,n in enumerate(cols[i])])
a=json.loads(Path('/home/guoliang/multiplier/generations/pareto_archive/archive.json').read_text())
print('PARETO', [r['objectives'] for r in a['records']])
