import importlib.util, json
from pathlib import Path
p=Path('/home/guoliang/multiplier/experiments/2/candidate_g0002_0002/parent.py')
spec=importlib.util.spec_from_file_location('parent',p); m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
c=m.Candidate(); c._columns=c._product_columns(*c.setup())
for col in range(8):
 print('COLUMN',col)
 for pos,n in enumerate(c._columns[col]):
  node=c.nodes[n]
  print(' ',pos,n,node.kind,node.inputs, 'input kinds',[(i,c.nodes[i].kind,c.nodes[i].inputs) for i in node.inputs])
print('INPUTS',[(i,c.nodes[i].kind) for i in c.input_ids]);print('all slots',sum(map(len,c._columns)))
a=json.loads(Path('/home/guoliang/multiplier/generations/pareto_archive/archive.json').read_text())
print('PARETO',[(r['objectives'],Path(r['candidate_path']).name) for r in a['records']])
