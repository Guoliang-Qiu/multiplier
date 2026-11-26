"""Directional trials, based only on previously verified equivalent baseline."""
from pathlib import Path
import subprocess
root=Path('/home/guoliang/multiplier');d=root/'experiments/3/candidate_g0003_0004/deep_optimization'
s=(d/'general_baseline.py').read_text()
base='        columns[4].append(g)'
variants={
 'remove_g':[(base,'        # G omitted: one pre-compression slot deleted.')],
 'g_and':[(base,'        columns[4].append(self._and(d[0], self._xor(c[4], d[1])))')],
 'g_one':[(base,'        columns[4].append(one)')],
 'g_cd':[(base,'        columns[4].append(self._and(c[0], self._xor(d[3], d[4])))')],
 'g_or':[(base,'        columns[4].append(self._or(c[0], d[0]))')],
 'g_shared':[(base,'        columns[4].append(self._and(self._or(c[0], d[0]), self._or(d[1], d[3])))')],
 'drop_comp18': [('COMP_COLS = (10, 11, 13, 15, 18)','COMP_COLS = (10, 11, 13, 15)')],
 'drop_comp10': [('COMP_COLS = (10, 11, 13, 15, 18)','COMP_COLS = (11, 13, 15, 18)')],
 'round6': [('ROUND_COLS: tuple[int, ...] = ()','ROUND_COLS: tuple[int, ...] = (6,)')],
 'round7': [('ROUND_COLS: tuple[int, ...] = ()','ROUND_COLS: tuple[int, ...] = (7,)')],
 'cut_a5': [('PROD_CUT_A = 4','PROD_CUT_A = 5')],
 'cut_b5': [('PROD_CUT_B = 4','PROD_CUT_B = 5')],
 'simplified_compress': [('if col == 3 and compressor_index <= 1:', 'if col == 3 and compressor_index <= 2:')],
}
for name,changes in variants.items():
 t=s
 for old,new in changes:
  assert old in t,(name,old);t=t.replace(old,new)
 p=d/(name+'.py');p.write_text(t)
 r=subprocess.run(['python','gate_cost.py',str(p)],cwd=root,capture_output=True,text=True)
 print(name,r.returncode,r.stdout.strip(),r.stderr[-300:],flush=True)
