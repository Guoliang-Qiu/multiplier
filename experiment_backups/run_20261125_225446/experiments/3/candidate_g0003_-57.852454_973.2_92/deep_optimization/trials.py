"""Generate and gate-cost equivalence rewrite trials; never modify delivery source."""
from pathlib import Path
import subprocess
root = Path('/home/guoliang/multiplier')
d = root/'experiments/3/candidate_g0003_0004/deep_optimization'
src = (d.parent/'partial_product_candidate.py').read_text()
variants = {
 'cell_neg': [('self._and(negative, self._or(generated_one, two))', 'self._and(negative, self._or(low, self._not(generated_m)))')],
 'toprow': [('self._and(active, self._not(self._xor(q[7], m[k])))', 'self._or(self._and(pos, m[k]), self._and(neg, self._not(m[k])))')],
 'xor_primitive': [('        both = self._and(a, b)\n        either = self._or(a, b)\n        return self._and(either, self._not(both))', '        return self._gate("XOR", a, b)')],
 'p_formula': [('self._or(self._and(q[2 * step + 1], x_and), self._and(self._not(q[2 * step + 1]), m[1]))', 'self._or(self._and(q[2 * step + 1], self._not(m[0])), self._and(self._not(q[2 * step + 1]), m[1]))')],
 'compress_swap': [('total, carry = self._add3(x0, x1, x2)', 'total, carry = self._add3(x1, x0, x2)')],
 'compress_cycle': [('total, carry = self._add3(x0, x1, x2)', 'total, carry = self._add3(x0, x2, x1)')],
 'compress_cycle2': [('total, carry = self._add3(x0, x1, x2)', 'total, carry = self._add3(x2, x1, x0)')],
 'output_swap': [('total, carry = self._add3(bucket[0], bucket[1], carry)', 'total, carry = self._add3(bucket[0], carry, bucket[1])')],
 'output_cycle': [('total, carry = self._add3(bucket[0], bucket[1], carry)', 'total, carry = self._add3(carry, bucket[1], bucket[0])')],
 'combined_swap': [('total, carry = self._add3(x0, x1, x2)', 'total, carry = self._add3(x1, x0, x2)'), ('total, carry = self._add3(bucket[0], bucket[1], carry)', 'total, carry = self._add3(bucket[0], carry, bucket[1])')],
 'digit_xor': [('self._xor(generated_m, low)', 'self._gate("XOR", generated_m, low)')],
 'mk_xor': [('self._xor(q[2 * step + 1], self._bit(m, k, zero))', 'self._gate("XOR", q[2 * step + 1], self._bit(m, k, zero))')],
 'top_xor': [('self._xor(q[7], m[k])', 'self._gate("XOR", q[7], m[k])')],
 'boundary_xor': [('self._xor(b[1], a[4])', 'self._gate("XOR", b[1], a[4])')],
 'compress_xor': [('total = self._xor(b_or_ac, a_or_c)', 'total = self._gate("XOR", b_or_ac, a_or_c)')],
 'low_xor': [('self._xor(bucket[0], carry)', 'self._gate("XOR", bucket[0], carry)')],
 'absorption_off': [('_USE_ABSORPTION = True', '_USE_ABSORPTION = False')],
 'top_active_xor': [('active = self._or(pos, neg)', 'active = self._xor(q[7], q[8])')],
 'top_active_primitive': [('active = self._or(pos, neg)', 'active = self._gate("XOR", q[7], q[8])')],
 'top_selector_mux': [('new = self._and(active, self._not(self._xor(q[7], m[k])))', 'new = self._and(active, self._or(self._and(q[7], m[k]), self._and(self._not(q[7]), self._not(m[k]))))')],
 'fa_cheaper': [('    def _product_columns(self, a, b, c, d, zero, one):', '    def _fa(self, a, b, cin):\n        # Alternative XOR/majority structure for gates shared with nearby cells.\n        t = self._xor(a, b)\n        return self._xor(t, cin), self._or(self._and(a, b), self._and(t, cin))\n\n    def _product_columns(self, a, b, c, d, zero, one):')],
}
for name,changes in variants.items():
 text=src
 for old,new in changes:
  assert old in text,(name,old)
  text=text.replace(old,new)
 text=text.replace('g_0 = 721', 'g_0 = self._or(self._and(d[0], self._xor(c[4], d[1])), self._and(c[0], self._xor(d[3], d[4])))')
 p=d/(name+'.py');p.write_text(text)
 r=subprocess.run(['python','gate_cost.py',str(p)],cwd=root,capture_output=True,text=True)
 print(name,r.returncode,r.stdout.strip(),r.stderr[-350:],flush=True)
