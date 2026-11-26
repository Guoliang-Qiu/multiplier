"""Build low-column slot simplifications and sign-row mapping trial."""
from pathlib import Path
p=Path('/home/guoliang/multiplier/experiments/5/candidate_g0005_0003/deep_optimization')
s=(p/'general_baseline.py').read_text()
old='        columns[5].append(deleted_first_product_bit)\n        return columns'
for name, action in [('both_low3','        del columns[3][1]\n        del columns[3][0]'),('both_low3_dropzero','        del columns[3][1]\n        del columns[3][0]\n        del columns[4][-1]'),('low3_dropconstant','        del columns[3][2]'),('low3_all','        columns[3].clear()')]:
    (p/(name+'.py')).write_text(s.replace(old,'        columns[5].append(deleted_first_product_bit)\n'+action+'\n        return columns'))
