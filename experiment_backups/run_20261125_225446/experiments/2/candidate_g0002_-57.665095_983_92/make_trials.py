"""Generate controlled standalone trial candidates from the second parent."""
from pathlib import Path
src = Path('/home/guoliang/multiplier/generations/2/candidate_g0002_-57.724238_976.2_92.py').read_text()
root = Path('/home/guoliang/multiplier/experiments/2/candidate_g0002_0009')
old = 'self._gate("MUX_XOR", one, self._bit(m_bits, k, zero), two, self._bit(m_bits, k - 1, zero), cell_neg)'
new = 'self._xor(self._or(self._and(one, self._bit(m_bits, k, zero)), self._and(two, self._bit(m_bits, k - 1, zero))), cell_neg)'
assert src.count(old) == 1
src = src.replace(old,new)
# All variants avoid the forbidden MUX_XOR cell. First experiment baseline plus
# first parent's distinct wider approximation in upper Booth rows.
(root/'base.py').write_text(src)
fused = src.replace('if step in (1, 2) and 3 <= k <= 8', 'if step in (0, 1, 2, 3) and 3 <= k <= 8')
# Parent A allows additional step-zero/three Booth cells. For these cells
# retain general negative gating, since the parent-B shortcut holds only for
# intermediate rows.
fused = fused.replace('cell_neg = self._and(negative, self._not(self._and(m, low)))', 'cell_neg = (self._and(negative, self._not(self._and(m, low))) if step in (1, 2) else self._and(negative, self._or(one, two)))')
(root/'fused.py').write_text(fused)
# Deep cone tuning: simplify final Booth-row correction using the parent-A
# expression where sign extension is redundant, and change XOR structure.
optimized = fused.replace('val = self._or(self._and(one, mk), self._and(negative, self._not(mk)))', 'val = self._or(self._and(one, mk), self._and(negative, self._not(mk)))')
optimized = optimized.replace('    def _xor(self, a, b):\n        both = self._and(a, b)\n        either = self._or(a, b)\n        return self._and(either, self._not(both))\n', '')
(root/'optimized.py').write_text(optimized)
# Target the affected Booth cell cones without disturbing globally shared XORs.
cellnative = src.replace(new, new.replace('self._xor(', 'self._gate("XOR", ', 1))
(root/'cellnative.py').write_text(cellnative)
# Parent A's shorter correction form for the high Booth cell, with its
# unaltered topology and all other approximation choices held fixed.
correction = src.replace('cell_neg = self._and(negative, self._not(self._and(m, low)))', 'cell_neg = self._and(negative, self._or(one, two))')
(root/'correction.py').write_text(correction)
# Try a different equivalent full-adder implementation on the carry chain:
# sum is parity of its input bits; carry is a shared-majority network.
fa = '''    def _fa(self, a, b, cin):
        """Carry-majority network, retaining the exact parity output."""
        ab = self._and(a, b)
        aob = self._or(a, b)
        carry = self._or(ab, self._and(aob, cin))
        total = self._xor(self._xor(a, b), cin)
        return total, carry

'''
(root/'adder.py').write_text(src.replace('    @staticmethod\n    def _bit', fa+'    @staticmethod\n    def _bit', 1))
