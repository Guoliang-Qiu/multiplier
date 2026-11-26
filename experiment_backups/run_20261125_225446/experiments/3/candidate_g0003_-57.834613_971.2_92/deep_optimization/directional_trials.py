"""Generate structural and approximation trials from the measured general-pass baseline."""
from pathlib import Path
base=Path(__file__).resolve().parent
src=(base/'general_equivalence_baseline.py').read_text()
variants={
 'g_or': [('g_5 = self._xor(g_0, g_1)','g_5 = self._or(g_0, g_1)')],
 'g_and': [('g_5 = self._xor(g_0, g_1)','g_5 = self._and(g_0, g_1)')],
 'g_xor_direct': [('g_5 = self._xor(g_0, g_1)','g_5 = self._gate("XOR", g_0, g_1)')],
 'drop_g_carry': [('columns[6].append(g_4)','columns[6].append(zero)')],
 'drop_g_sum': [('columns[5].append(g_5)','columns[5].append(zero)')],
 'one_g_carry': [('columns[6].append(g_4)','columns[6].append(one)')],
 'g_carry_or': [('g_4 = self._gate(\'AND\', g_0, g_1)','g_4 = self._or(g_0, g_1)')],
 'g_sum_one': [('columns[5].append(g_5)','columns[5].append(one)')],
 'drop_column4_zero': [('cols[4][4] = zero','cols[4][4] = one')],
 'omit_comp18': [('COMP_COLS = (10, 11, 13, 15, 18)','COMP_COLS = (10, 11, 13, 15)')],
 'omit_comp10': [('COMP_COLS = (10, 11, 13, 15, 18)','COMP_COLS = (11, 13, 15, 18)')],
 'extra_round6': [('ROUND_COLS: tuple[int, ...] = ()','ROUND_COLS: tuple[int, ...] = (6,)')],
 'extra_round7': [('ROUND_COLS: tuple[int, ...] = ()','ROUND_COLS: tuple[int, ...] = (7,)')],
 'low_or_col6': [('self._or(bucket[0], carry) if col < 7 else self._xor(bucket[0], carry)','self._or(bucket[0], carry) if col < 8 else self._xor(bucket[0], carry)')],
 'low_xor_col6': [('self._or(bucket[0], carry) if col < 7 else self._xor(bucket[0], carry)','self._or(bucket[0], carry) if col < 6 else self._xor(bucket[0], carry)')],
 'g_mux_cell': [('g_5 = self._xor(g_0, g_1)','g_5 = self._mux_xor(g_0, self._not(g_1), self._not(g_0), g_1, zero)')],
 'remove_col4_zero': [('cols[4][4] = zero','del cols[4][4]')],
 'g_demorgan': [('g_4 = self._gate(\'AND\', g_0, g_1)','g_4 = self._not(self._or(self._not(g_0), self._not(g_1)))')],
 'no_and_factoring': [('    def xor_operands(self, n):','    def unused_xor_operands(self, n):'), ('    def _and(self, a, b):','    def unused_and(self, a, b):')],
 'drop_extra_one4': [('EXTRA_ONE = {4: 1}','EXTRA_ONE = {}')],
 'g_or_and_no_comp18': [('g_5 = self._xor(g_0, g_1)','g_5 = self._or(g_0, g_1)'), ('COMP_COLS = (10, 11, 13, 15, 18)','COMP_COLS = (10, 11, 13, 15)')],
 'remove4_add3': [('cols[4][4] = zero','del cols[4][4]'), ('EXTRA_ONE = {4: 1}','EXTRA_ONE = {4: 1, 3: 1}')],
 'remove4_add2': [('cols[4][4] = zero','del cols[4][4]'), ('EXTRA_ONE = {4: 1}','EXTRA_ONE = {4: 1, 2: 1}')],
 'remove4_add4': [('cols[4][4] = zero','del cols[4][4]'), ('EXTRA_ONE = {4: 1}','EXTRA_ONE = {4: 2}')],
 'remove4_add5': [('cols[4][4] = zero','del cols[4][4]'), ('EXTRA_ONE = {4: 1}','EXTRA_ONE = {4: 1, 5: 1}')],
 'remove4_g_or': [('cols[4][4] = zero','del cols[4][4]'), ('g_5 = self._xor(g_0, g_1)','g_5 = self._or(g_0, g_1)')],
 'remove4_and_comp18': [('cols[4][4] = zero','del cols[4][4]'), ('COMP_COLS = (10, 11, 13, 15, 18)','COMP_COLS = (10, 11, 13, 15)')],
 'remove4_add4_g_or': [('cols[4][4] = zero','del cols[4][4]'), ('EXTRA_ONE = {4: 1}','EXTRA_ONE = {4: 2}'), ('g_5 = self._xor(g_0, g_1)','g_5 = self._or(g_0, g_1)'), ('COMP_COLS = (10, 11, 13, 15, 18)','COMP_COLS = (10, 11, 13, 15)')],
 'remove4_add4_reorder': [('cols[4][4] = zero','del cols[4][4]'), ('EXTRA_ONE = {4: 1}','EXTRA_ONE = {4: 2}'), ('columns[5].append(g_5)\n        columns[6].append(g_4)','columns[5].insert(0, g_5)\n        columns[6].append(g_4)'), ('COMP_COLS = (10, 11, 13, 15, 18)','COMP_COLS = (10, 11, 13, 15)')],
 'remove4_add4_round7': [('cols[4][4] = zero','del cols[4][4]'), ('EXTRA_ONE = {4: 1}','EXTRA_ONE = {4: 2}'), ('ROUND_COLS: tuple[int, ...] = ()','ROUND_COLS: tuple[int, ...] = (7,)'), ('COMP_COLS = (10, 11, 13, 15, 18)','COMP_COLS = (10, 11, 13, 15)')],
 'remove4_add4_round6': [('cols[4][4] = zero','del cols[4][4]'), ('EXTRA_ONE = {4: 1}','EXTRA_ONE = {4: 2}'), ('ROUND_COLS: tuple[int, ...] = ()','ROUND_COLS: tuple[int, ...] = (6,)'), ('COMP_COLS = (10, 11, 13, 15, 18)','COMP_COLS = (10, 11, 13, 15)')],
}
for name, changes in variants.items():
 text=src
 for old,new in changes:
  assert text.count(old)==1,(name,old)
  text=text.replace(old,new)
 (base/(name+'.py')).write_text(text)
