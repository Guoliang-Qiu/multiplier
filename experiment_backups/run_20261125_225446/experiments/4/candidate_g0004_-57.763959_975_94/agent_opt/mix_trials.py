from pathlib import Path
import subprocess
root=Path(__file__).resolve().parent
base=(root/'shared_xors.py').read_text()
old='''                        val = self._or(self._and(generated_one, get_xor(k)), self._and(two, get_xor(k - 1)))'''
assert base.count(old)==2
for step in [1,2]:
 for k in range(3,8):
  name=f'mix_s{step}_k{k}'
  branch=f'''                        if step == {step} and k == {k}:
                            # Zero digit has an all-zero row.
                            cell_neg = self._and(negative, self._or(generated_one, two))
                            val = self._gate("MUX_XOR", generated_one, self._bit(m, k, zero), two, self._bit(m, k - 1, zero), cell_neg)
                        else:
                            val = self._or(self._and(generated_one, get_xor(k)), self._and(two, get_xor(k - 1)))'''
  path=root/(name+'.py');path.write_text(base.replace(old,branch,1))
  o=subprocess.run(['python','/home/guoliang/multiplier/gate_cost.py',str(path)],capture_output=True,text=True)
  print(name,o.returncode,o.stdout.strip(),o.stderr.strip(),flush=True)
