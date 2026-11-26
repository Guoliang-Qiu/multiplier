"""Generate local Boolean rewrites for weighted whole-circuit screening."""
from pathlib import Path
root=Path('/home/guoliang/multiplier/experiments/5/candidate_g0005_0000/deep_optimization')
src=(root/'direction_top.py').read_text()
variants={
 'p_factor': ('self._or(self._and(q_bits[2 * step + 1], x_and), self._and(self._not(q_bits[2 * step + 1]), m_bits[1]))', 'self._and(self._or(q_bits[2 * step + 1], m_bits[1]), self._not(self._and(q_bits[2 * step + 1], self._and(m_bits[0], m_bits[1]))))'),
 'p_factor2': ('self._or(self._and(q_bits[2 * step + 1], x_and), self._and(self._not(q_bits[2 * step + 1]), m_bits[1]))', 'self._or(self._and(m_bits[1], self._not(q_bits[2 * step + 1])), self._and(q_bits[2 * step + 1], x_and))'),
 'cellneg': ('self._and(negative, self._not(self._and(m, low)))', 'self._and(negative, self._not(low))'),
 'top_digits': ('one = self._and(self._not(m), low)', 'one = self._and(low, self._not(m))'),
}
for name,(old,new) in variants.items():
 assert src.count(old)==1, (name,src.count(old))
 (root/('trial_'+name+'.py')).write_text(src.replace(old,new))
