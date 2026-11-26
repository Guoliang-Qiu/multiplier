import importlib.util
from pathlib import Path
p = Path('/home/guoliang/multiplier/experiments/5/candidate_g0005_0000/parent.py')
s = importlib.util.spec_from_file_location('parent', p)
m = importlib.util.module_from_spec(s)
s.loader.exec_module(m)
c = m.Candidate()
cols = c._product_columns(*c.setup())
for i in range(7):
    print('column', i, [(j, n, c.nodes[n].kind, c.nodes[n].inputs) for j, n in enumerate(cols[i])])
print('all slots', sum(map(len, cols)), 'prefix nodes', len(c.nodes))
