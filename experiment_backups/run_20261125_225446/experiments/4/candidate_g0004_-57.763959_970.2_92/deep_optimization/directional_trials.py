"""Directional column/compensation experiments on the equivalent baseline."""
from pathlib import Path
import subprocess,sys,json
here=Path(__file__).resolve().parent
src=(here/'g_simplified.py').read_text()
root=Path('/home/guoliang/multiplier')
variants={
 'remove_g':src.replace('columns[4].append(self._or(d[0], d[1]))','pass  # Remove G partial product explicitly.'),
 'g_and':src.replace('columns[4].append(self._or(d[0], d[1]))','columns[4].append(self._and(d[0], d[1]))'),
 'g_first':src.replace('columns[4].append(self._or(d[0], d[1]))','columns[4].append(d[0])'),
 'g_second':src.replace('columns[4].append(self._or(d[0], d[1]))','columns[4].append(d[1])'),
 'comp_10':src.replace('COMP_COLS = (10, 11, 13, 15)','COMP_COLS = (11, 13, 15)'),
 'comp_11':src.replace('COMP_COLS = (10, 11, 13, 15)','COMP_COLS = (10, 13, 15)'),
 'comp_13':src.replace('COMP_COLS = (10, 11, 13, 15)','COMP_COLS = (10, 11, 15)'),
 'comp_15':src.replace('COMP_COLS = (10, 11, 13, 15)','COMP_COLS = (10, 11, 13)'),
 'extra_one':src.replace('EXTRA_ONE = {4: 1}','EXTRA_ONE = {}'),
 'maj_col4':src.replace('MAJ_COLS = (0, 1, 2, 3)','MAJ_COLS = (0, 1, 2, 3, 4)'),
 'maj_col5':src.replace('MAJ_COLS = (0, 1, 2, 3)','MAJ_COLS = (0, 1, 2, 3, 5)'),
}
for name,body in variants.items():
    path=here/(name+'.py');path.write_text(body)
    p=subprocess.run([sys.executable,str(root/'gate_cost.py'),str(path)],capture_output=True,text=True)
    if p.returncode:print(name,'FAILED',p.stderr[-400:],flush=True);continue
    cost=json.loads(p.stdout)
    print(name,cost,flush=True)
    if cost['gate_cost'] < 971.2 or name in ('g_and','g_first','g_second'):
        ev=subprocess.run([sys.executable,str(root/'eval.py'),str(path),'--stimulus-file',str(root/'stimulus.npy')],capture_output=True,text=True)
        print(name,'eval',ev.returncode,ev.stdout.strip(),ev.stderr[-400:],flush=True)
