"""Compare alternate CD low-column reductions without relocating compression."""
from pathlib import Path
import subprocess
root=Path('/home/guoliang/multiplier');d=root/'experiments/3/candidate_g0003_0004/deep_optimization'
s=(d/'general_baseline.py').read_text()
old='''        either = self._or(p0, p2)
        carry = self._and(p1, either)
        total = self._gate('XOR', p1, either)'''
changes={
 'merge02_exact':'        either = self._xor(p0, p2)\n        carry = self._or(self._and(p0, p2), self._and(p1, either))\n        total = self._xor(p1, either)',
 'merge02_or_and':'        either = self._or(p0, p2)\n        carry = self._and(p0, p2)\n        total = self._xor(p1, either)',
 'merge02_or_or':'        either = self._or(p0, p2)\n        carry = self._or(p1, self._and(p0, p2))\n        total = self._xor(p1, either)',
 'merge01':'        either = self._or(p0, p1)\n        carry = self._and(p2, either)\n        total = self._xor(p2, either)',
 'merge12':'        either = self._or(p1, p2)\n        carry = self._and(p0, either)\n        total = self._xor(p0, either)',
 'merge02_xor_carry':'        either = self._or(p0, p2)\n        carry = self._and(p1, either)\n        total = self._xor(p1, either)',
}
for name,new in changes.items():
 assert old in s
 t=s.replace(old,new).replace('COMP_COLS = (10, 11, 13, 15, 18)','COMP_COLS = (10, 11, 13, 15)')
 p=d/(name+'.py');p.write_text(t)
 r=subprocess.run(['python','gate_cost.py',str(p)],cwd=root,capture_output=True,text=True)
 print(name,r.returncode,r.stdout.strip(),r.stderr[-200:],flush=True)
