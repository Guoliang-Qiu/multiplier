"""Create source-preserving local gate-optimization trials from immutable handoff."""
from pathlib import Path
base = Path('/home/guoliang/multiplier/experiments/2/candidate_g0002_0007/deep_optimization')
src = Path('/home/guoliang/multiplier/experiments/2/candidate_g0002_0007/partial_product_candidate.py').read_text()

def save(name, text):
    (base / (name + '.py')).write_text(text)

fa = '''    def _fa(self, a, b, cin):
        # Exact parity with majority: share the two compound majority inputs.
        ac = self._and(a, cin)
        ao = self._or(a, cin)
        bp = self._or(b, ac)
        carry = self._and(ao, bp)
        return self._xor(ao, bp), carry

'''
save('fa_share', src.replace('    def _compress_columns(self):', fa + '    def _compress_columns(self):'))
old = '''                new = self._and(active, self._not(self._xor(q[7], m[k])))'''
new = '''                new = self._and(active, self._xor(self._not(q[7]), m[k]))'''
save('top_polarity', src.replace(old, new))
save('native_xor', src.replace('''        both = self._and(a, b)
        either = self._or(a, b)
        return self._and_absorb(either, self._not(both))''', '''        return super()._xor(a, b)'''))
old = '''                    x0x2 = self._and(x0, x2)
                    x1_or_x0x2 = self._or(x1, x0x2)
                    x0_or_x2 = self._or(x0, x2)
                    carry = self._and(x1_or_x0x2, x0_or_x2)'''
new = '''                    x0x2 = self._and(x0, x2)
                    carry = self._or(x0x2, self._and(x1, self._or(x0, x2)))'''
save('majority_factored', src.replace(old,new))
