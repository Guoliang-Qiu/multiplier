"""Build A-backed experiment variants without changing either protected parent."""
from pathlib import Path
src = Path('/home/guoliang/multiplier/generations/3/candidate_g0003_-57.614048_960.2_93.py').read_text()
out = Path('/home/guoliang/multiplier/experiments/3/candidate_g0003_0010')
def save(name, old, new):
    assert src.count(old) == 1, (name,src.count(old))
    (out/(name+'.py')).write_text(src.replace(old,new))

# Change original column-four slot suppression only, not compressor order.
save('a_restore_slot', '        cols[4][4] = zero', '        # Preserve the original signal at this slot.')
save('a_remove_slot', '        cols[4][4] = zero', '        del cols[4][4]')
save('a_cut3b', '    PROD_CUT_B = 4', '    PROD_CUT_B = 3')
# Parent B's signed-digit sharing formula for top multiplicand row.
old = '''                new = self._and(active, self._not(self._xor(q[7], m[k])))'''
new = '''                new = self._and(active, self._and(self._or(q[7], m[k]), self._not(self._and(q[7], m[k]))))'''
save('a_top_decompose',old,new)
# B's signed-row XOR AND/OR factoring already A's default _xor; tune the
# compressor's XOR-only local bit-3 carry via parent B's exact _add3.
save('a_exact3', '''                if col == 3 and compressor_index <= 1:''', '''                if False:''')
save('a_low7xor', '''self._or(bucket[0], carry) if col < 7''','''self._or(bucket[0], carry) if col < 6''')
save('a_low8or', '''self._or(bucket[0], carry) if col < 7''','''self._or(bucket[0], carry) if col < 8''')
# Try no extra compensating one while preserving explicit column 4 zero slot.
save('a_no_extra_one','    EXTRA_ONE = {4: 1}','    EXTRA_ONE = {}')
