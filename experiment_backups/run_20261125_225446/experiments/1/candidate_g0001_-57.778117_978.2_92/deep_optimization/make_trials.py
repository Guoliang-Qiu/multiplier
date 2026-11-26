from pathlib import Path
root=Path('/home/guoliang/multiplier/experiments/1/candidate_g0001_0003')
out=root/'deep_optimization'
s=(root/'partial_product_candidate.py').read_text()
# Remove dead fixed node reference / dead constant buffer and collapse the two
# consecutive compensation methods without changing the live column ordering.
start=s.index('    def _product_columns_before_compensation_previous(')
end=s.index('\ndef build_circuit():', start)
replacement='''    def _product_columns(self, a, b, c, d, zero, one):
        """Keep the handoff's explicit row deletion and shifted compensation."""
        columns = self._product_columns_before_compensation(a, b, c, d, zero, one)
        g_0, g_2 = columns[4][0], columns[4][3]
        del columns[4][3]
        del columns[4][2]
        del columns[4][0]
        columns[4].append(g_2)
        columns[5].append(g_0)
        # The handoff subsequently removed this slot and inserted ZERO.
        del columns[4][2]
        columns[4].append(zero)
        return columns
'''
s=s[:start]+replacement+s[end:]
(out/'general_baseline.py').write_text(s)
variants={
'native_xor':s.replace('''        both = self._and(a, b)
        either = self._or(a, b)
        return self._and(either, self._not(both))''','''        return self._gate("XOR", a, b)'''),
'xor_alt':s.replace('''        both = self._and(a, b)
        either = self._or(a, b)
        return self._and(either, self._not(both))''','''        return self._or(self._and(a, self._not(b)), self._and(self._not(a), b))'''),
'xor_nand':s.replace('''        both = self._and(a, b)
        either = self._or(a, b)
        return self._and(either, self._not(both))''','''        return self._not(self._or(self._and(a, b), self._and(self._not(a), self._not(b))))'''),
}
for name,txt in variants.items(): (out/(name+'.py')).write_text(txt)
