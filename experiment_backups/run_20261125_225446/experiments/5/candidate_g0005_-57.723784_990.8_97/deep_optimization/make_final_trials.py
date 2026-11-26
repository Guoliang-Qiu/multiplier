"""Generate targeted directional changes on the locked general-equivalence baseline."""
from pathlib import Path
p=Path('/home/guoliang/multiplier/experiments/5/candidate_g0005_0003/deep_optimization')
s=(p/'general_baseline.py').read_text()
old='        del columns[3][0]\n        return columns'
changes={
'no_zero4':'        del columns[3][0]\n        del columns[4][-1]\n        return columns',
'no_second_low3':'        del columns[3][0]\n        del columns[3][0]\n        return columns',
'no_bit4':'        del columns[3][0]\n        del columns[4][0]\n        return columns',
'no_reused_booth5':'        del columns[3][0]\n        del columns[5][-1]\n        return columns',
'no_low5last':'        del columns[3][0]\n        del columns[5][-2]\n        return columns',
'no_low6last':'        del columns[3][0]\n        del columns[6][-1]\n        return columns',
'add_round3':'        del columns[3][0]\n        columns[3].append(one)\n        return columns',
'add_round4':'        del columns[3][0]\n        columns[4].append(one)\n        return columns',
'add_round5':'        del columns[3][0]\n        columns[5].append(one)\n        return columns',
}
for name,new in changes.items():
    assert s.count(old)==1
    (p/(name+'.py')).write_text(s.replace(old,new))
