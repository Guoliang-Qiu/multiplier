from pathlib import Path
import subprocess
r=Path(__file__).resolve().parent;p=(r/'shared_xors.py').read_text()
old='''                if col == 3 and compressor_index <= 1:
                    ac = self._and(x0, x2)
                    b_or_ac = self._or(x1, ac)
                    a_or_c = self._or(x0, x2)
                    carry = self._and(b_or_ac, a_or_c)
                    total = self._xor(b_or_ac, a_or_c)
                else:
                    total, carry = self._add3(x0, x1, x2)'''
assert p.count(old)==1
for col in (3,4,5,6,7,8):
 for idx in (0,1,2,3,4,5,8):
  name=f'comp_c{col}_i{idx}'
  text=p.replace(old,old.replace('col == 3 and compressor_index <= 1',f'col == {col} and compressor_index <= {idx}'))
  path=r/(name+'.py');path.write_text(text)
  o=subprocess.run(['python','/home/guoliang/multiplier/gate_cost.py',str(path)],capture_output=True,text=True)
  print(name,o.returncode,o.stdout.strip(),o.stderr.strip()[:80],flush=True)
