"""Test alternative shared XOR Boolean forms and compressor transformations."""
from pathlib import Path
p = Path('/home/guoliang/multiplier/experiments/5/candidate_g0005_0009')
s = (p/'trial_rows_a.py').read_text()
old = '''        both = self._and(a, b)
        either = self._or(a, b)
        return self._and(either, self._not(both))'''
forms = {
    'sop': '''        return self._or(self._and(a, self._not(b)),
                        self._and(self._not(a), b))''',
    'nand': '''        return self._not(self._or(self._and(a, b),
                                   self._and(self._not(a), self._not(b))))''',
    'xorgate': '''        return self._gate('XOR', a, b)''',
}
assert old in s
for name, body in forms.items():
    (p/f'trial_{name}.py').write_text(s.replace(old, body))
# A cheaper exact 3-input compressor that shares its majority function with
# total; preserve the parent's approximate col3 compressor and LIFO ordering.
fa = '''    def _fa(self, a, b, cin):
        """Exact compressor via a shared pair parity and majority network."""
        ab = self._xor(a, b)
        return self._xor(ab, cin), self._or(self._and(a, b), self._and(ab, cin))

'''
(p/'trial_fa.py').write_text(s.replace('    def _compress_columns(self):', fa+'    def _compress_columns(self):'))
print('generated')
