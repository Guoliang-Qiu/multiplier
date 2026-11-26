"""Generate standalone trial candidates from the two inspected parent sources."""
from pathlib import Path
ROOT = Path('/home/guoliang/multiplier')
HERE = ROOT / 'experiments/4/candidate_g0004_0010'
a = (ROOT/'generations/4/candidate_g0004_-57.827429_1003.8_97.py').read_text()
b = (ROOT/'generations/4/candidate_g0004_-57.711990_970.2_91.py').read_text()
# The task's AND/OR/XOR/NOT-only restriction requires expansion of MUX_XOR.
def primitive(src):
    src = src.replace('self._mux_xor(generated_one, self._bit(m, k, zero), two, self._bit(m, k - 1, zero), cell_neg)',
        'self._xor(cell_neg, self._or(self._and(generated_one, self._bit(m, k, zero)), self._and(two, self._bit(m, k - 1, zero))))')
    src = src.replace('self._gate("MUX_XOR", one, self._bit(m_bits, k, zero), two, self._bit(m_bits, k - 1, zero), cell_neg)',
        'self._xor(cell_neg, self._or(self._and(one, self._bit(m_bits, k, zero)), self._and(two, self._bit(m_bits, k - 1, zero))))')
    return src
for name, source in [('a_primitive', a), ('b_primitive', b)]:
    (HERE/(name+'.py')).write_text(primitive(source))
# Fuse A's four-row Boolean sharing with B's sign-row factoring and absorption.
fused = primitive(b).replace('step in (0, 1, 2) and', 'step in (0, 1, 2, 3) and')
(HERE/'fused.py').write_text(fused)
# Alternative: original shared Booth XORs eliminate all primitive expanded MUX cells.
(HERE/'no_mux.py').write_text(primitive(b).replace('if step in (0, 1, 2) and 3 <= k <= 8 and k < q_bits_of_step - 1:', 'if False:'))
# Algebraic optimized correction: expand e XOR mux using distributivity over disjoint
# one/two digit recode, allowing conditional negation of each selected multiplier bit.
local = primitive(b).replace('self._xor(cell_neg, self._or(self._and(one, self._bit(m_bits, k, zero)), self._and(two, self._bit(m_bits, k - 1, zero))))', 'self._or(self._and(one, self._xor(q_bits[2 * step + 1], self._bit(m_bits, k, zero))), self._and(two, self._xor(q_bits[2 * step + 1], self._bit(m_bits, k - 1, zero))))')
(HERE/'local_recode.py').write_text(local)
base = (HERE/'no_mux.py').read_text()
variants = {
 'absorb_off': base.replace('    _USE_ABSORPTION = True', '    _USE_ABSORPTION = False'),
 'sign_original': base.replace('        for m, q in ((a, b), (c, d)):', '        for m, q in (): '),
 'compress_maj3': base.replace('MAJ_COLS = (0, 1, 2, 3)', 'MAJ_COLS = (3,)'),
 'compress_maj4': base.replace('MAJ_COLS = (0, 1, 2, 3)', 'MAJ_COLS = (0, 1, 2, 3, 4)'),
 'compress_maj5': base.replace('MAJ_COLS = (0, 1, 2, 3)', 'MAJ_COLS = (0, 1, 2, 3, 4, 5)'),
 'sum_xor_cell': base.replace('        both = self._and(a, b)\n        either = self._or(a, b)\n        return self._and(either, self._not(both))', '        return super()._xor(a, b)'),
 'row4_xor': base.replace('new = self._and(active, self._not(self._xor(q[7], m[k])))', 'new = self._or(self._and(pos, m[k]), self._and(neg, self._not(m[k])))'),
 'out_no_or': base.replace('self._or(bucket[0], carry) if col < 7 else self._xor(bucket[0], carry)', 'self._xor(bucket[0], carry)'),
 'out_more_or': base.replace('col < 7', 'col < 9'),
}
for name, source in variants.items():
    (HERE/(name+'.py')).write_text(source)
for n in range(5, 11):
    src = base.replace('MAJ_COLS = (0, 1, 2, 3)', 'MAJ_COLS = '+repr(tuple(range(n+1))))
    (HERE/(f'maj_through_{n}.py')).write_text(src)
for n in (3, 5, 6):
    src = base.replace('    PROD_CUT_A = 4', f'    PROD_CUT_A = {n}').replace('    PROD_CUT_B = 4', f'    PROD_CUT_B = {n}')
    (HERE/(f'cut_{n}.py')).write_text(src)
# Keep the exact architecture; vary explicitly approximate low-column correction.
for name, x, y in [
 ('g_simple', 'g_0', 'g_1'),
 ('g_simple_swap', 'g_1', 'g_0'),
 ('g_or_and', 'self._and(g_0, self._not(g_1))', 'self._or(g_0, g_1)'),
 ('g_and_or', 'self._or(g_0, self._not(g_1))', 'self._and(g_0, g_1)'),
 ('g_not', 'self._not(g_1)', 'self._not(g_0)'),
 ('g_xor', 'self._xor(g_0, g_1)', 'self._or(g_0, g_1)'),
]:
    src = base.replace('columns[4].append(g_6)', 'columns[4].append('+x+')').replace('columns[5].append(g_5)', 'columns[5].append('+y+')')
    (HERE/(name+'.py')).write_text(src)
for name, src in [('no_extra_one',base.replace('EXTRA_ONE = {4: 1}', 'EXTRA_ONE = {}')), ('add_one_5',base.replace('EXTRA_ONE = {4: 1}', 'EXTRA_ONE = {4: 1, 5: 1}'))]:
    (HERE/(name+'.py')).write_text(src)
for perm in ('x0, x2, x1', 'x1, x0, x2', 'x1, x2, x0', 'x2, x0, x1', 'x2, x1, x0'):
    name = 'fa_' + ''.join(x[-1] for x in perm.split(', '))
    (HERE/(name+'.py')).write_text(base.replace('self._add3(x0, x1, x2)', 'self._add3('+perm+')'))
for name, src in [
 ('booth_ctrl_xor',base.replace('one = self._xor(m, low)', 'one = self._gate("XOR", m, low)').replace('self._xor(h, m)', 'self._gate("XOR", h, m)')),
 ('booth_xor_list',base.replace('self._xor(q_bits[2 * step + 1], self._bit(m_bits, k, zero))', 'self._gate("XOR", q_bits[2 * step + 1], self._bit(m_bits, k, zero))')),
 ('sign_xor_cell',base.replace('self._xor(q[7], m[k])', 'self._gate("XOR", q[7], m[k])')),
 ('low_g_xor_cell',base.replace('self._xor(b[1], a[4])', 'self._gate("XOR", b[1], a[4])').replace('self._xor(b[1], a[3])', 'self._gate("XOR", b[1], a[3])')),
 ('output_xor_cell',base.replace('self._xor(bucket[0], bucket[1])', 'self._gate("XOR", bucket[0], bucket[1])').replace('self._xor(bucket[0], carry)', 'self._gate("XOR", bucket[0], carry)')),
]:
    (HERE/(name+'.py')).write_text(src)
# First parent's accurate cutoff/correction and second parent's high Booth
# sign-row factoring, preserving sign Boolean behavior.
a_no_mux = primitive(a).replace('if step in (0, 1, 2, 3) and 3 <= k <= 8 and k < q_bits_of_step - 1:', 'if False:')
sign_start = b.index('        for m, q in ((a, b), (c, d)):')
sign_end = b.index('        return all_columns', sign_start)
sign_code = b[sign_start:sign_end]
a_sign = a_no_mux.replace('        return all_columns\n\n    def _compress_columns', sign_code + '        return all_columns\n\n    def _compress_columns')
(HERE/'a_sign.py').write_text(a_sign)
for name, src in [
 ('a_sign_absorb',a_sign.replace('    PROD_CUT_A = 2', '    _USE_ABSORPTION = True\n    def _gate(self, kind, *inputs, absorption=False):\n        return super()._gate(kind, *inputs, absorption=absorption or self._USE_ABSORPTION)\n    PROD_CUT_A = 2')),
 ('a_sign_no_special',a_sign.replace('if col == 3 and compressor_index <= 1:', 'if False:')),
 ('a_sign_xor',a_sign.replace('        both = self._and(a, b)\n        either = self._or(a, b)\n        return self._and(either, self._not(both))', '        return super()._xor(a, b)')),
 ('a_sign_cut3',a_sign.replace('PROD_CUT_A = 2', 'PROD_CUT_A = 3').replace('PROD_CUT_B = 2', 'PROD_CUT_B = 3')),
]:
    (HERE/(name+'.py')).write_text(src)


