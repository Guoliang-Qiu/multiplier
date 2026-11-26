"""Produce compensation-bit and low carry variants of verified general pass."""
from pathlib import Path
p=Path('/home/guoliang/multiplier/experiments/5/candidate_g0005_0003/deep_optimization')
s=(p/'general_baseline.py').read_text()
for col in (10,11,13,15):
    new=tuple(x for x in (10,11,13,15) if x!=col)
    (p/f'drop_comp{col}.py').write_text(s.replace('COMP_COLS = (10, 11, 13, 15)',f'COMP_COLS = {new}'))
for old,new,name in [('if col <= 6 else','if col <= 5 else','low_or5'),('if col <= 6 else','if col <= 7 else','low_or7')]:
    (p/f'{name}.py').write_text(s.replace(old,new))
