"""Produce cost-directed, semantically exact Boolean factoring trials."""
from pathlib import Path
p = Path('/home/guoliang/multiplier/experiments/5/candidate_g0005_0009')
base = (p / 'trial_fused.py').read_text()
# Restore original high-row shared XOR realization; neighboring Booth cells
# reuse the same (negative XOR multiplicand[k]) symbol.
start = base.index('                    if step in (0, 1, 2, 3) and 3 <= k <= 8')
end = base.index('                if k == q_bits_of_step - 1:', start)
old = base[start:end]
replacement = '''                    val = self._or(self._and(generated_one, get_xor(k)),
                                   self._and(two, get_xor(k - 1)))
'''
(p / 'trial_shared.py').write_text(base[:start] + replacement + base[end:])
# Optimize local exact digit selector using a sum-of-products expression when
# sign-toggle corrections are identical between the two disjoint digit arms.
# Factor the terminal bit's common multiplicand with an OR control.
terminal = '''val = self._selected_digit(generated_one, self._bit(m, k - 1, zero),
                                            two, self._bit(m, k - 1, zero), cell_neg)'''
assert terminal in base
factored = '''val = self._xor(self._and(self._or(generated_one, two), m[8]), cell_neg)'''
(p / 'trial_factored.py').write_text(base.replace(terminal, factored))
# Hybrid factoring and shared symbols: eliminate duplicated negated digit
# controls in row middle, while retaining B's terminal simplification.
shared = (p / 'trial_shared.py').read_text()
(p / 'trial_shared_factored.py').write_text(shared.replace(terminal, factored))
print('generated', list(x.name for x in p.glob('trial_*py')))
