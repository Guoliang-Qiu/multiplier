"""Generate readable stage-preserving equivalence trials from immutable handoff."""
from pathlib import Path
root=Path('/home/guoliang/multiplier/experiments/1/candidate_g0001_0000')
out=root/'deep_optimization'
s=(root/'partial_product_candidate.py').read_text()
variants={
 'constant_slot': [('columns[4].append(self.add(\'OR\', g_3, zero))','columns[4].append(one)')],
 'sign_guard': [('self._and(negative, self._or(one, two))','self._and(negative, self._not(self._and(m, low)))')],
 'p_factor': [('self._or(self._and(q_bits[2 * step + 1], x_and), self._and(self._not(q_bits[2 * step + 1]), m_bits[1]))','self._or(self._and(q_bits[2 * step + 1], self._not(m_bits[0])), self._and(self._not(q_bits[2 * step + 1]), m_bits[1]))')],
 'p_factor_b': [('self._or(self._and(q_bits[2 * step + 1], x_and), self._and(self._not(q_bits[2 * step + 1]), m_bits[1]))','self._or(self._and(q_bits[2 * step + 1], self._not(m_bits[0])), self._and(self._not(q_bits[2 * step + 1]), m_bits[1]))'),('self._and(one, self._and(p, self._not(q)))','self._and(one, self._and(m_bits[1], self._or(self._not(q_bits[2 * step + 1]), self._not(m_bits[0]))))')],
 'top_b': [('self._and(negative, self._and(p, self._not(q)))','self._and(negative, self._xor(m_bits[0], m_bits[1]))')],
}
for name, changes in variants.items():
 t=s
 for a,b in changes:
  assert t.count(a)==1,(name,a)
  t=t.replace(a,b)
 (out/f'{name}.py').write_text(t)
