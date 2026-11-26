from pathlib import Path
import subprocess
r=Path(__file__).resolve().parent
p=(r/'shared_xors.py').read_text()
old="outputs.append(self._or(bucket[0], carry) if col < 7 else self._xor(bucket[0], carry))"
assert p.count(old)==1
for n in (8,9,10,11,12,13,14,18):
 path=r/f'output_or_before_{n}.py';path.write_text(p.replace(old,f"outputs.append(self._or(bucket[0], carry) if col < {n} else self._xor(bucket[0], carry))"))
 o=subprocess.run(['python','/home/guoliang/multiplier/gate_cost.py',str(path)],capture_output=True,text=True)
 print(n,o.returncode,o.stdout.strip(),o.stderr.strip(),flush=True)
