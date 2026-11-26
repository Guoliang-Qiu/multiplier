"""Generate equivalent local Booth-row factoring experiments."""
from pathlib import Path
p=Path('/home/guoliang/multiplier/experiments/5/candidate_g0005_0003/deep_optimization')
s=(p/'general_baseline.py').read_text()
old='val = self._or(self._and(generated_one, mk), self._and(negative, self._not(mk)))'
for name,new in [('sign_mux','val = self._mux_xor(generated_one, mk, negative, self._not(mk), zero)'),('sign_pos','val = self._and(self._or(generated_one, self._not(mk)), self._or(negative, mk))'),('sign_xor','val = self._xor(self._and(self._or(generated_one, negative), mk), negative)')]:
    (p/(name+'.py')).write_text(s.replace(old,new))
old2='cell_neg = self._and(negative, self._or(generated_one, two))'
for name,new in [('neg_simple','cell_neg = self._and(negative, self._or(generated_one, two))'),('neg_factor','cell_neg = self._or(self._and(negative, generated_one), self._and(negative, two))')]:
    (p/(name+'.py')).write_text(s.replace(old2,new))
