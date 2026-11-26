"""Further perturbation and exact gate sharing experiments around fused B."""
from pathlib import Path
p=Path('/home/guoliang/multiplier/experiments/3/candidate_g0003_0010')
src=(p/'fused_low.py').read_text()
def save(name,old,new):
 assert src.count(old)==1, (name,src.count(old))
 (p/(name+'.py')).write_text(src.replace(old,new))
save('drop_zero','        columns[4][0] = zero','        del columns[4][0]')
save('drop_zero_corr','        columns[4][0] = zero','        del columns[4][0]\n        columns[4].append(one)')
# Factor B's duplicated signed XOR signal in the last Booth digit via the
# identity (q7 XOR bit) = ~(q7==bit), gated by mutually exclusive guards.
save('fused_top','                val = self._or(self._and(one, mk), self._and(negative, self._not(mk)))','                val = self._and(self._or(one, negative), self._not(self._xor(q_bits[7], mk)))')
save('fused_digit','                two = self._or(self._and(self._and(m, low), self._not(h)),\n                               self._and(self._not(self._or(m, low)), h))','                two = self._and(self._not(one), self._xor(h, m))')
save('fused_low7','                if col <= 6:','                if col <= 7:')
# Exact _fa optimization candidate only: shared two-row half-adder propagates
# same carry as library _fa with a factorized majority circuit.
save('fused_fa','    def _compress_columns(self):','''    def _fa(self, a, b, cin):
        # XOR sum with shared propagate and generate for majority carry.
        propagate = self._xor(a, b)
        generate = self._and(a, b)
        carry = self._or(generate, self._and(propagate, cin))
        return self._xor(propagate, cin), carry

    def _compress_columns(self):''')
# A's AND/OR XOR sharing across sign, digit, and compressor cones.
save('fused_sharedxor','    def _compress_columns(self):','''    def _xor(self, a, b):
        # Parent A's AND/OR factorization, sharing precomputed input pairs.
        return self._and_absorb(self._or(a, b), self._not(self._and(a, b)))

    def _compress_columns(self):''')
save('fused_sharedxor_digit','    def _compress_columns(self):','''    def _xor(self, a, b):
        return self._and_absorb(self._or(a, b), self._not(self._and(a, b)))

    def _compress_columns(self):''')
