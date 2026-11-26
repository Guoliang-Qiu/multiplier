"""Compare sharing-friendly Booth row and compressor rewrites."""
from pathlib import Path
p = Path('/home/guoliang/multiplier/experiments/5/candidate_g0005_0009')
s = (p/'trial_fused.py').read_text()
old = '''                        val = self._selected_digit(generated_one, self._bit(m, k, zero), two, self._bit(m, k - 1, zero), cell_neg)'''
new = '''                        val = self._or(self._and(generated_one, get_xor(k)),
                                       self._and(two, get_xor(k - 1)))'''
assert old in s
(p/'trial_rows.py').write_text(s.replace(old,new))
# Preserve the intact parent A's correction style for comparison with k2 fusion.
a = (p/'trial_a.py').read_text()
assert old in a
(p/'trial_rows_a.py').write_text(a.replace(old,new))
# No k2 fusion: parent B 92-slot architecture with adjacent shared XOR rows.
b = (p/'trial_b.py').read_text()
old_b = '''                        val = self._selected_digit(one, self._bit(m_bits, k, zero),
                                            two, self._bit(m_bits, k - 1, zero), cell_neg)'''
new_b = '''                        val = self._or(self._and(one, get_xor(k)),
                                       self._and(two, get_xor(k - 1)))'''
assert old_b in b
(p/'trial_rows_b.py').write_text(b.replace(old_b,new_b))
print('generated')
