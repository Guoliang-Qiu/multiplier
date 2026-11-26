"""Generate readable circuit-stage variants; snapshots stay untouched."""
from pathlib import Path
p = Path('/home/guoliang/multiplier/experiments/1/candidate_g0001_0005')
out = p/'deep_optimization'
src = (p/'partial_product_candidate.py').read_text()
src = src.replace('''        if q[0] == self.input_ids[9]:
            cols[2][:] = [zero, one]
        else:
            cols[2][:] = [zero, one]''', '''        cols[2][:] = [zero, one]''')
src = src.replace('''        # X refers to nodes in the original pre-compression prefix.
        g_0 = 152
        g_1 = 568
        g_2 = zero
        g_3 = one
        # Match the fixed insertion buffers used by the error table.
        columns[4].append(self.add('OR', g_3, zero))''', '''        # The last correction is a constant ONE, independent of its unused observations.
        columns[4].append(one)''')
(out/'general_baseline.py').write_text(src)
(out/'general_xor.py').write_text(src.replace('''    def _xor(self, a, b):
        both = self._and(a, b)
        either = self._or(a, b)
        return self._and(either, self._not(both))''','''    def _xor(self, a, b):
        """Use the native XOR cell instead of the handoff's AND/OR network."""
        return self._gate('XOR', a, b)'''))
start = src.index('    def _compress_columns(self):')
end = src.index('    def _build_outputs(self):', start)
compress = src[start:end]
version = compress.replace('''                x0, x1, x2 = (all_columns[col].pop(), all_columns[col].pop(), all_columns[col].pop())''','''                if col != 3:
                    all_columns[col].sort(key=lambda n: n in (zero, one))
                x0, x1, x2 = (all_columns[col].pop(), all_columns[col].pop(), all_columns[col].pop())''')
(out/'general_constants.py').write_text(src[:start]+version+src[end:])
version = compress.replace('''                    carry = self._and(b_or_ac, a_or_c)
                    total = self._xor(b_or_ac, a_or_c)''','''                    carry = self._and(b_or_ac, a_or_c)
                    total = self._and(self._or(b_or_ac, a_or_c), self._not(carry))''')
(out/'general_col3.py').write_text(src[:start]+version+src[end:])
(out/'general_stage_xor.py').write_text(src.replace('''    def _compress_columns(self):''','''    def _compress_columns(self):
        # The product stage retains the original node numbering for G observations.
        self._native_xor = True''').replace('''    def _xor(self, a, b):
        both = self._and(a, b)''','''    def _xor(self, a, b):
        if getattr(self, '_native_xor', False):
            return self._gate('XOR', a, b)
        both = self._and(a, b)'''))
(out/'general_buffers.py').write_text(src.replace("self.add('OR', g_0, zero)", 'g_0').replace("self.add('OR', g_1, zero)", 'g_1').replace("self.add('OR', g_7, zero)", 'g_7').replace("self.add('OR', g_5, zero)", 'g_5'))
for name, deletions in [('drop_680', [(10,9)]),('drop_346',[(10,4)]),('drop_both',[(10,9),(10,4)]),('drop_707',[(4,2)]),('drop_680_707',[(10,9),(4,2)])]:
    lines = '\n'.join('        del columns[%d][%d]' % (col,idx) for col,idx in deletions)
    trial=src.replace('''        columns[4].append(one)
        return columns''','''        columns[4].append(one)
        # Bias-guided selective partial-product removal; before compression.
%s
        return columns''' % lines)
    (out/('direction_'+name+'.py')).write_text(trial)
for name, col, val in [('plus_3',3,'one'),('plus_5',5,'one'),('plus_6',6,'one'),('minus_4',4,'zero')]:
    if name=='minus_4':
        trial=src.replace('''        columns[4].append(one)
        return columns''','''        columns[4].append(zero)
        return columns''')
    else:
        trial=src.replace('''        columns[4].append(one)
        return columns''','''        columns[4].append(one)
        columns[%d].append(%s)
        return columns'''%(col,val))
    (out/('direction_'+name+'.py')).write_text(trial)
print('created general and directional experiments')
