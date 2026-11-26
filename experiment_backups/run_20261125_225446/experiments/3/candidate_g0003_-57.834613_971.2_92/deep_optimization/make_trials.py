"""Construct self-contained equivalent gate-level trial candidates."""
from pathlib import Path
base = Path('/home/guoliang/multiplier/experiments/3/candidate_g0003_0003/deep_optimization')
src = Path('/home/guoliang/multiplier/experiments/3/candidate_g0003_0003/partial_product_candidate.py').read_text()
variants = {
 'shared_xor': [('g_5 = self._gate(\'XOR\', g_0, g_1)', 'g_5 = self._xor(g_0, g_1)')],
 'no_buffers': [('columns[5].append(self.add(\'OR\', g_5, zero))','columns[5].append(g_5)'), ('columns[6].append(self.add(\'OR\', g_4, zero))','columns[6].append(g_4)')],
 'shared_and_no_buffers': [('g_5 = self._gate(\'XOR\', g_0, g_1)', 'g_5 = self._xor(g_0, g_1)'), ('columns[5].append(self.add(\'OR\', g_5, zero))','columns[5].append(g_5)'), ('columns[6].append(self.add(\'OR\', g_4, zero))','columns[6].append(g_4)')],
 'plain_gates': [('g_5 = self._gate(\'XOR\', g_0, g_1)', 'g_5 = self._xor(g_0, g_1)'), ('g_4 = self._gate(\'AND\', g_0, g_1)', 'g_4 = self._and(g_0, g_1)')],
 'dynamic_g': [('g_0 = 94','g_0 = columns[5][0]'), ('g_1 = 417','g_1 = columns[5][3]')],
 'xor_xnor': [('return self._and_absorb(either, self._not(both))','return self._not(self._or(both, self._not(either)))')],
 'xor_sop': [('return self._and_absorb(either, self._not(both))','return self._or(self._and(a, self._not(b)), self._and(b, self._not(a)))')],
 'no_absorption': [('_USE_ABSORPTION = True','_USE_ABSORPTION = False')],
 'fa_mux': [('    def _build_outputs(self):', '''    def _fa(self, a, b, cin):
        pair = self._xor(a, b)
        carry = self._or(self._and(a, b), self._and(cin, pair))
        return self._xor(pair, cin), carry

    def _build_outputs(self):''')],
 'combined': [('g_0 = 94','g_0 = columns[5][0]'), ('g_1 = 417','g_1 = columns[5][3]'), ('g_5 = self._gate(\'XOR\', g_0, g_1)', 'g_5 = self._xor(g_0, g_1)'), ('columns[5].append(self.add(\'OR\', g_5, zero))','columns[5].append(g_5)'), ('columns[6].append(self.add(\'OR\', g_4, zero))','columns[6].append(g_4)')],
 'no_extra_g': [('g_0 = 94','g_0 = columns[5][0]'), ('g_1 = 417','g_1 = columns[5][3]'), ('g_4 = self._gate(\'AND\', g_0, g_1)','g_5, g_4 = self._add3(g_0, g_1, zero)'), ('g_5 = self._gate(\'XOR\', g_0, g_1)',''), ('columns[5].append(self.add(\'OR\', g_5, zero))','columns[5].append(g_5)'), ('columns[6].append(self.add(\'OR\', g_4, zero))','columns[6].append(g_4)')],
 'sign_sop': [('new = self._and(active, self._not(self._xor(q[7], m[k])))','new = self._or(self._and(pos, m[k]), self._and(neg, self._not(m[k])))')],
 'corrected_combined': [('del columns[5][3]','g_0, g_1 = columns[5][0], columns[5][3]\n        del columns[5][3]'), ('g_0 = 94\n        g_1 = 417\n        g_2 = zero\n        g_3 = one\n        ',''), ('g_5 = self._gate(\'XOR\', g_0, g_1)', 'g_5 = self._xor(g_0, g_1)'), ('columns[5].append(self.add(\'OR\', g_5, zero))','columns[5].append(g_5)'), ('columns[6].append(self.add(\'OR\', g_4, zero))','columns[6].append(g_4)')],
 'ha_g': [('del columns[5][3]','g_0, g_1 = columns[5][0], columns[5][3]\n        del columns[5][3]'), ('g_0 = 94\n        g_1 = 417\n        g_2 = zero\n        g_3 = one\n        ','g_5, g_4 = self._ha(g_0, g_1)\n        # '), ('g_4 = self._gate(\'AND\', g_0, g_1)\n        g_5 = self._gate(\'XOR\', g_0, g_1)',''), ('columns[5].append(self.add(\'OR\', g_5, zero))','columns[5].append(g_5)'), ('columns[6].append(self.add(\'OR\', g_4, zero))','columns[6].append(g_4)')],
}
for name, edits in variants.items():
 text = src
 for old, new in edits:
  assert text.count(old)==1,(name,old)
  text=text.replace(old,new)
 (base/(name+'.py')).write_text(text)
