from pathlib import Path
root=Path('/home/guoliang/multiplier/experiments/1/candidate_g0001_0003/deep_optimization')
s=(root/'general_baseline.py').read_text()
needle='        columns[4].append(zero)\n        return columns'
for col in (4,5,6,7,8):
    for index in range({4:5,5:7,6:8,7:8,8:10}[col]):
        for repl in ('zero','one'):
            if col==4 and index in (2,4): continue
            replacement=f'        columns[{col}][{index}] = {repl}\n'+needle
            (root/f'slot_{col}_{index}_{repl}.py').write_text(s.replace(needle,replacement))
