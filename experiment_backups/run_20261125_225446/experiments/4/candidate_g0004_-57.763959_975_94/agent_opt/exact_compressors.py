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
for col in (5,6,7,8,9,10):
 for index in (0,2,4,8,16):
  branch=f'''                if col == {col} and compressor_index <= {index}:
                    carry = self._or(self._and(x0, x1), self._and(x2, self._or(x0, x1)))
                    total = self._xor(self._xor(x0, x1), x2)
                else:
                    total, carry = self._add3(x0, x1, x2)'''
  name=f'exact_c{col}_i{index}'
  path=r/(name+'.py');path.write_text(p.replace(old,branch))
  o=subprocess.run(['python','/home/guoliang/multiplier/gate_cost.py',str(path)],capture_output=True,text=True)
  print(name,o.returncode,o.stdout.strip(),o.stderr.strip()[:80],flush=True)
