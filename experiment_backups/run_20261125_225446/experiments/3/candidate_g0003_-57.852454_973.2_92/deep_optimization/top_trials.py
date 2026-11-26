"""Explore exact reorganization of top-row partial-product generation."""
from pathlib import Path
import subprocess
root=Path('/home/guoliang/multiplier')
d=root/'experiments/3/candidate_g0003_0004/deep_optimization'
s=(d.parent/'partial_product_candidate.py').read_text().replace('g_0 = 721','g_0 = self._or(self._and(d[0], self._xor(c[4], d[1])), self._and(c[0], self._xor(d[3], d[4])))')
start=s.index('        for m, q in ((a, b), (c, d)):')
end=s.index('        # SMT-selected G',start)
top=s[start:end]
for name,expr in {
 'top_direct_original': 'self._or(self._and(generated_one, mk), self._and(negative, self._not(mk)))',
 'top_direct_factored': 'self._and(self._xor(q[7], q[8]), self._not(self._xor(q[7], mk)))',
 'top_direct_mux': 'self._gate("MUX_XOR", generated_one, mk, negative, self._not(mk), zero)',
 'top_direct_mux_alt': 'self._gate("MUX_XOR", generated_one, mk, negative, self._not(mk), zero)',
}.items():
 t=s.replace(top,'')
 old='val = self._or(self._and(generated_one, mk), self._and(negative, self._not(mk)))'
 if name=='top_direct_factored':
  expr=expr.replace('q[7], q[8]','q[7], q[8]')
 t=t.replace(old,'val = '+expr)
 if name=='top_direct_original':
  # remove top-row re-creation only; original already used during generation.
  pass
 if name=='top_direct_mux_alt':
  t=t.replace('self._gate("MUX_XOR", generated_one, mk, negative, self._not(mk), zero)', 'self._or(self._and(generated_one, mk), self._and(negative, self._not(mk)))')
 p=d/(name+'.py');p.write_text(t)
 r=subprocess.run(['python','gate_cost.py',str(p)],cwd=root,capture_output=True,text=True)
 print(name,r.returncode,r.stdout.strip(),r.stderr[-500:],flush=True)
