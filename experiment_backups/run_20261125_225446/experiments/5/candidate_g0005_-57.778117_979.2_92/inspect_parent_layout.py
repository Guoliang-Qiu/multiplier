import importlib.util
from pathlib import Path
p = Path('/home/guoliang/multiplier/experiments/5/candidate_g0005_0002/parent.py')
s = importlib.util.spec_from_file_location('parent', p)
m = importlib.util.module_from_spec(s)
s.loader.exec_module(m)
c = m.Candidate()
cols = c._product_columns(*c.setup())
for i, row in enumerate(cols):
    print(i, [(j, n, c.nodes[n].kind, tuple(c.nodes[n].inputs)) for j, n in enumerate(row)])
print('prefix nodes', len(c.nodes))
print('input buses', c.input_ids)
