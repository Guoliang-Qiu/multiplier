"""Generate independent directional variants of the verified baseline."""
from pathlib import Path
p=Path('/home/guoliang/multiplier/experiments/2/candidate_g0002_0007/deep_optimization')
s=(p/'general_baseline.py').read_text()

def save(name,old,new):
    assert old in s and s.count(old)==1,(name,s.count(old))
    (p/(name+'.py')).write_text(s.replace(old,new))

save('without_g5', '''        columns[5].append(g_6)''','''        # Omit the jointly generated, weight-five correction.''')
save('without_g4', '''        columns[4].append(g_4)''','''        # Omit the weight-four correction.''')
save('without_g0', '''        columns[5].append(g_0)''','''        # Omit the second weight-five correction.''')
save('without_one4','''    EXTRA_ONE = {4: 1}''','''    EXTRA_ONE = {}''')
save('without_one10','''    COMP_COLS = (10, 11, 13, 15, 18)''','''    COMP_COLS = (11, 13, 15, 18)''')
save('without_one11','''    COMP_COLS = (10, 11, 13, 15, 18)''','''    COMP_COLS = (10, 13, 15, 18)''')
save('without_one13','''    COMP_COLS = (10, 11, 13, 15, 18)''','''    COMP_COLS = (10, 11, 15, 18)''')
save('without_one15','''    COMP_COLS = (10, 11, 13, 15, 18)''','''    COMP_COLS = (10, 11, 13, 18)''')
save('without_one18','''    COMP_COLS = (10, 11, 13, 15, 18)''','''    COMP_COLS = (10, 11, 13, 15)''')
save('round_6','''    ROUND_COLS: tuple[int, ...] = ()''','''    ROUND_COLS: tuple[int, ...] = (6,)''')
save('round_7','''    ROUND_COLS: tuple[int, ...] = ()''','''    ROUND_COLS: tuple[int, ...] = (7,)''')
save('round_5','''    ROUND_COLS: tuple[int, ...] = ()''','''    ROUND_COLS: tuple[int, ...] = (5,)''')
save('g4_zero','''        columns[4].append(g_4)''','''        columns[4].append(zero)  # Explicit zero-weight replacement slot.''')
save('g4_one','''        columns[4].append(g_4)''','''        columns[4].append(one)  # Constant-compensated replacement.''')
save('g5_one','''        columns[5].append(g_6)''','''        columns[5].append(one)  # Constant-compensated replacement.''')
save('g0_one','''        columns[5].append(g_0)''','''        columns[5].append(one)  # Constant-compensated replacement.''')
