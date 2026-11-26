"""Screen only exact compressor-input permutations; no changes to column layout."""
from pathlib import Path
import subprocess,os,json
root=Path(__file__).parent
src=(root/'general.py').read_text()
needle='                    total, carry = self._add3(x0, x1, x2)'
for order in [('x0','x2','x1'),('x1','x0','x2'),('x1','x2','x0'),('x2','x0','x1'),('x2','x1','x0')]:
 name='perm_'+''.join(str(('x0','x1','x2').index(v)) for v in order)
 p=root/(name+'.py');p.write_text(src.replace(needle,'                    total, carry = self._add3('+', '.join(order)+')'))
 env={**os.environ,'OPEN_QUESTION_SOLVER_ROOT':'/home/guoliang/open_question_solver'}
 r=subprocess.run(['python','gate_cost.py',str(p)],cwd='/home/guoliang/multiplier',env=env,text=True,capture_output=True)
 print(name,r.returncode,r.stdout.strip() if r.returncode==0 else r.stderr.strip(),flush=True)
