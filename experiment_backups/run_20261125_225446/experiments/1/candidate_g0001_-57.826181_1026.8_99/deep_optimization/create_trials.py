"""Generate controlled statistical compensation variants from measured baseline."""
from pathlib import Path
root=Path('experiments/1/candidate_g0001_0004/deep_optimization')
src=(root/'equivalent_baseline.py').read_text()
for name,old,new in [
 ('plus4','columns[4].append(g_0)','columns[4].append(g_0)\n        columns[4].append(one)'),
 ('plus5','columns[4].append(g_0)','columns[4].append(g_0)\n        columns[5].append(one)'),
 ('plus6','columns[4].append(g_0)','columns[4].append(g_0)\n        columns[6].append(one)'),
 ('plus4plus5','columns[4].append(g_0)','columns[4].append(g_0)\n        columns[4].append(one)\n        columns[5].append(one)'),
 ('plus5conditional','columns[4].append(g_0)','columns[4].append(g_0)\n        columns[5].append(g_0)'),
 ('plus5other','columns[4].append(g_0)','columns[4].append(g_0)\n        columns[5].append(self.input_ids[29])'),
 ('remove3','columns[4].append(g_0)','columns[4].append(g_0)\n        del columns[3][1]'),
]:
    assert src.count(old)==1
    (root/(name+'.py')).write_text(src.replace(old,new))
