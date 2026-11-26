"""Generate auditable primitive-only parent and fused trials."""
from pathlib import Path
root = Path('/home/guoliang/multiplier')
folder = root / 'experiments/5/candidate_g0005_0009'
parents = [root / 'generations/5/candidate_g0005_-57.796681_994.8_99.py', root / 'generations/5/candidate_g0005_-57.799388_997.2_92.py']
a, b = [p.read_text() for p in parents]
# Replace each MUX_XOR call at construction time with a local factored Boolean
# realization in the candidate's product stage (no new primitive override).
primitive = '''    def _selected_digit(self, a, b, c, d, e):
        """Primitive-only Booth selection: XOR a correction with two selected bits."""
        return self._xor(self._or(self._and(a, b), self._and(c, d)), e)

'''
a = a.replace('self._mux_xor(', 'self._selected_digit(')
b = b.replace('self._mux_xor(', 'self._selected_digit(')
a = a.replace('    def _one_product_columns(', primitive + '    def _one_product_columns(', 1)
b = b.replace('    def _one_product_columns(', '''    def _xor(self, a, b):
        both = self._and(a, b)
        either = self._or(a, b)
        return self._and(either, self._not(both))

''' + primitive + '    def _one_product_columns(', 1)
(folder / 'trial_a.py').write_text(a)
(folder / 'trial_b.py').write_text(b)
fused = a
old = 'a = self._or(self._and(generated_one, get_xor(2)), self._and(two, p))'
new = '''a = self._mux_xor(generated_one, m[2], two, p,
                                  self._and(generated_one, q[2 * step + 1]))'''
assert old in fused
fused = fused.replace(old, new)
old = '''                    else:
                        val = self._or(self._and(generated_one, get_xor(k)), self._and(two, get_xor(k - 1)))'''
new = '''                    elif k == q_bits_of_step - 1 and step < 4:
                        cell_neg = negative if step == 0 else self._and(negative, self._not(self._and(generated_m, low)))
                        val = self._mux_xor(generated_one, self._bit(m, k - 1, zero),
                                            two, self._bit(m, k - 1, zero), cell_neg)
                    else:
                        val = self._or(self._and(generated_one, get_xor(k)), self._and(two, get_xor(k - 1)))'''
assert old in fused
fused = fused.replace(old, new)
fused = fused.replace('self._mux_xor(', 'self._selected_digit(')
(folder / 'trial_fused.py').write_text(fused)
print('Created', [(p.name, p.stat().st_size) for p in folder.glob('trial_*.py')])
