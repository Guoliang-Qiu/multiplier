"""Evaluate parent-B primitive-only styles and final-adder sharing."""
from pathlib import Path
p=Path('/home/guoliang/multiplier/experiments/5/candidate_g0005_0009')
b=(p/'trial_b.py').read_text()
x='''    def _xor(self, a, b):
        both = self._and(a, b)
        either = self._or(a, b)
        return self._and(either, self._not(both))

'''
assert x in b
(p/'trial_b_xor.py').write_text(b.replace(x,''))
# Parent A uses bitwise full-adders at col3; remove the unreachable and
# duplicate control logic in the interior rows (without moving compression).
a=(p/'trial_rows_a.py').read_text()
old='''                    if step in (0, 1, 2, 3) and 3 <= k <= 8 and k < q_bits_of_step - 1:
                        # Zero digit has an all-zero row; preserve original Booth semantics.
                        cell_neg = negative if step == 0 else self._and(negative, self._not(self._and(generated_m, low)))
                        # All four nonterminal Booth rows can share the recode control.
                        # The kit's port order is (a, b, c, d, e).
                        val = self._or(self._and(generated_one, get_xor(k)),
                                       self._and(two, get_xor(k - 1)))
                    else:
                        val = self._or(self._and(generated_one, get_xor(k)), self._and(two, get_xor(k - 1)))'''
new='''                    # Adjacent Booth digits reuse the same signed multiplicand
                    # XOR: this beats decomposing each five-input selection.
                    val = self._or(self._and(generated_one, get_xor(k)),
                                   self._and(two, get_xor(k - 1)))'''
assert old in a
(p/'trial_clean.py').write_text(a.replace(old,new))
