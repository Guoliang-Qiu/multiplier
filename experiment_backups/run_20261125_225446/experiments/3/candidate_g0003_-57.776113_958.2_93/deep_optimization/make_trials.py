"""Generate bounded equivalence trials from immutable handoff source."""
from pathlib import Path
root = Path('/home/guoliang/multiplier/experiments/3/candidate_g0003_0005')
p = root / 'partial_product_candidate.py'
out = root / 'deep_optimization'
s = p.read_text()
blocks = {
 'xor_base': ('    def _xor(self, a, b):\n        # Expose shared absorption context to tap2\'s gate cache.\n        both = self._and(a, b)\n        either = self._or(a, b)\n        return self._and_absorb(either, self._not(both))\n', '    def _xor(self, a, b):\n        # Direct native XOR avoids extra intermediate gates when unshared.\n        return self._gate("XOR", a, b)\n'),
 'and_base': ('    def _and(self, a, b):\n'+s.split('    def _and(self, a, b):\n',1)[1].split('    def _product_columns(self,',1)[0], '    def _and(self, a, b):\n        # Native AND instead of the specialized three-selector identity.\n        return self._gate("AND", a, b)\n\n'),
 'factor_off': ('    def _gate(self, kind, *inputs, absorption=False):\n'+s.split('    def _gate(self, kind, *inputs, absorption=False):\n',1)[1].split('    @staticmethod',1)[0], '    def _gate(self, kind, *inputs, absorption=False):\n        # Retain global absorption; disable common-factor restructuring.\n        return super()._gate(kind, *inputs, absorption=absorption or self._USE_ABSORPTION)\n\n'),
 'fa_mux': ('    def _product_columns(self, a, b, c, d, zero, one):', '''    def _fa(self, a, b, cin):
        # Equivalent full-adder carry via shared propagate/generate and XOR sum.
        generate = self._and(a, b)
        propagate = self._or(a, b)
        carry = self._or(generate, self._and(propagate, cin))
        parity = self._xor(a, b)
        total = self._xor(parity, cin)
        return total, carry

    def _product_columns(self, a, b, c, d, zero, one):'''),
 'step4_mux': ('                new = self._and(active, self._not(self._xor(q[7], m[k])))', '                new = self._or(self._and(pos, m[k]), self._and(neg, self._not(m[k])))'),
 'output_xor': ('self._or(bucket[0], carry) if col < 7 else self._xor(bucket[0], carry)', 'self._xor(bucket[0], carry)'),
}
for name, (old, new) in blocks.items():
 assert old in s, name
 (out / f'{name}.py').write_text(s.replace(old,new))
