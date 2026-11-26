"""Disentangle the two parent-B Boolean rewrites."""
from pathlib import Path
p=Path('/home/guoliang/multiplier/experiments/5/candidate_g0005_0009')
a=(p/'trial_rows_a.py').read_text()
f=(p/'trial_fused.py').read_text()
old='a = self._or(self._and(generated_one, get_xor(2)), self._and(two, p))'
new='''a = self._selected_digit(generated_one, m[2], two, p,
                                  self._and(generated_one, q[2 * step + 1]))'''
assert old in a
(p/'trial_k2.py').write_text(a.replace(old,new))
old='''                    else:
                        val = self._or(self._and(generated_one, get_xor(k)), self._and(two, get_xor(k - 1)))'''
new='''                    elif k == q_bits_of_step - 1 and step < 4:
                        cell_neg = negative if step == 0 else self._and(negative, self._not(self._and(generated_m, low)))
                        val = self._xor(self._and(self._or(generated_one, two), m[8]), cell_neg)
                    else:
                        val = self._or(self._and(generated_one, get_xor(k)), self._and(two, get_xor(k - 1)))'''
assert old in a
(p/'trial_k9.py').write_text(a.replace(old,new))
(p/'trial_k2k9.py').write_text((p/'trial_k2.py').read_text().replace(old,new))
