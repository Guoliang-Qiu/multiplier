"""Generate standalone trial variations using parent B's three-stage architecture."""
from pathlib import Path
p = Path('/home/guoliang/multiplier/experiments/1/candidate_g0001_0006')
s = (p / 'parent_b.py').read_text()
# Parent A's cheaper AND/OR realization for highly shared XOR cones.
xor_a = '''    def _xor(self, a, b):
        # Parent A: shared AND/OR XNOR decomposition, cost 3 with reusable terms.
        both = self._and(a, b)
        either = self._or(a, b)
        return self._and(either, self._not(both))

'''
# NO MUX_XOR cells in this workflow. The two product terms are exclusive
# in Booth digit rows, allowing the sign toggle to be absorbed algebraically.
mux_expand = '''    def _mux_xor(self, a, b, c, d, e):
        # Gate-only realization of the inherited 5-port MUX_XOR functionality.
        return self._xor(self._or(self._and(a, b), self._and(c, d)), e)

'''
# This helper is genuinely different from tap2's mux_xor since it implements
# an AND/OR/XOR-only subgraph required by the active cell restriction.
s = s.replace('    @staticmethod\n    def _bit', mux_expand + '    @staticmethod\n    def _bit', 1)
s = s.replace('    @staticmethod\n    def _bit', xor_a + '    @staticmethod\n    def _bit', 1)
# Drop needless exact-reference compressor override by replacing with inherited
# reference dispatch? Abstract requires implementation so maintain required call.
(p / 'fused0.py').write_text(s)
# Transfer parent A's approximate compressor only where B has three active
# slots at column 3, which the B architecture does not, so do not splice it.
# Instead experiment with parent A's bit-4 observation replacing B's unit.
s2 = s.replace('columns[4].append(one)\n        return columns', 'columns[4].append(b[0])\n        return columns')
(p / 'fused_bit.py').write_text(s2)
# Parent A's extra column-4 pair deletion after B's G bit; test independently.
s3 = s.replace('columns[4].append(one)\n        return columns', 'del columns[4][3]\n        del columns[4][0]\n        columns[4].append(b[0])\n        return columns')
# Avoid expensive independent MUX expansions by sharing the sign XOR
# across adjacent Booth cells (parent A's signed-row structure).
s4 = s.replace('''                a = self._mux_xor(one, m_bits[2], two, p,
                                  self._and(one, q_bits[2 * step + 1]))''', '''                a = self._or(self._and(one, get_xor(2)), self._and(two, p))''')
s4 = s4.replace('''                        val = self._mux_xor(one, self._bit(m_bits, k, zero),
                                            two, self._bit(m_bits, k - 1, zero), cell_neg)''', '''                        val = self._or(self._and(one, get_xor(k)),
                                       self._and(two, get_xor(k - 1)))''')
(p / 'shared_row.py').write_text(s4)
s5 = s4.replace('columns[4].append(one)\n        return columns', 'columns[4].append(b[0])\n        return columns')
(p / 'shared_bit.py').write_text(s5)
s6 = s4.replace('columns[4].append(one)\n        return columns', 'del columns[4][3]\n        del columns[4][0]\n        columns[4].append(b[0])\n        return columns')
# Factor the G compensation cone directly, avoiding redundant guarded OR.
s7 = s6.replace('''g_0 = self._mux_xor(d[1], d[0], d[1], self._not(c[2]),
                            self._and(d[0], c[3]))''', '''g_0 = self._xor(self._and(d[0], c[3]),
                        self._and(d[1], self._or(d[0], self._not(c[2]))))''')
# Retain both original column-three products instead of G's approximate
# replacement; test if savings in the compensation cone justify compression.
s8 = s4.replace('''        del columns[3][1]
        del columns[3][0]''', '''        # Preserve both original low partial products.''').replace('''        columns[4].append(g_0)''', '''        # No G compensation is required when its sources remain.''')
(p / 'retain_low.py').write_text(s8)
# Keep parent B's original G and slot count, but change the unit compensation
# into parent A's input observation.
(p / 'retain_bit.py').write_text(s5)
# Differentially remove one partial-product slot after the sign-corrected G.
for index in range(7):
    x = s4.replace('''        del columns[4][6]''', f'''        del columns[4][{index}]''')
# Selective low-weight truncation; slot ordering is preserved except deletion.
for col, index in ((4, 0), (4, 1), (4, 2), (4, 3), (4, 4),
                   (5, 0), (5, 1), (5, 2), (5, 3), (5, 4), (6, 0), (6, 1)):
    x = s4.replace('''        columns[4].append(one)
        return columns''', f'''        columns[4].append(one)
        del columns[{col}][{index}]
        return columns''')
    (p / f'trunc_{col}_{index}.py').write_text(x)
# The parent A approximate compressor activates only at column three, where
# B prunes one product entirely: test the two distinct approximate adders
# independently rather than changing its LIFO ordering accidentally.
