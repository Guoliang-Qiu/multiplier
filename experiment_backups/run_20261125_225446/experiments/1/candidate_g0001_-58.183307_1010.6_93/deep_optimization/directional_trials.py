"""Explore alternative MUX_XOR placements on verified general baseline."""
from pathlib import Path
p=Path(__file__).parent
s=(p/'general_baseline.py').read_text()
trials={
 'mux_full_adder': [('    def _compress_columns(self):', '''    def _fa(self, a, b, cin):
        """Directional trial: MUX_XOR parity with factored majority carry."""
        total = self._mux_xor(a, self._not(cin), self._not(a), cin, b)
        carry = self._or(self._and(a, cin), self._and(b, self._or(a, cin)))
        return total, carry

    def _compress_columns(self):''')],
 'mux_top_rows': [('val = self._or(self._and(one, mk), self._and(negative, self._not(mk)))','val = self._mux_xor(one, mk, negative, self._not(mk), zero)')],
 'mux_g_reorder': [('self._mux_xor(d[1], d[0], d[1], self._not(c[2]),','self._mux_xor(self._not(c[2]), d[1], d[0], d[1],')],
 'mux_row_alt': [('val = self._mux_xor(one, self._bit(m_bits, k, zero),\n                                            two, self._bit(m_bits, k - 1, zero), cell_neg)','val = self._mux_xor(two, self._bit(m_bits, k - 1, zero),\n                                            one, self._bit(m_bits, k, zero), cell_neg)')],
}
for name,changes in trials.items():
 t=s
 for a,b in changes:
  assert t.count(a)==1,(name,a,t.count(a))
  t=t.replace(a,b)
 (p/(name+'.py')).write_text(t)
