"""Generate measured MUX_XOR placements on the general-pass baseline."""
from pathlib import Path
root=Path('/home/guoliang/multiplier/experiments/5/candidate_g0005_0000/deep_optimization')
src=(root/'general_v1.py').read_text()
old='val = self._and(self._or(one, two), get_xor(k - 1))'
new='val = self._mux_xor(one, self._bit(m_bits, k - 1, zero),\n                                            two, self._bit(m_bits, k - 1, zero), cell_neg)'
assert src.count(old)==1
(root/'direction_top.py').write_text(src.replace(old,new))
old='columns[4].append(self._xor(self._and(d[0], c[3]),\n                                    self._and(d[1], self._or(d[0], self._not(c[2])))))'
assert src.count(old)==1
variants = {
    'mux_g': 'columns[4].append(self._mux_xor(d[1], d[0], d[1], self._not(c[2]),\n                                         self._and(d[0], c[3])))',
    'factor_g': 'columns[4].append(self._xor(self._and(d[0], c[3]),\n                                    self._and(d[1], self._not(self._and(c[2], self._not(d[0]))))))',
    'xor_g': 'columns[4].append(self._xor(self._and(d[0], c[3]),\n                                    self._or(self._and(d[1],d[0]),self._and(d[1],self._not(c[2])))))',
}
for name, replacement in variants.items():
    (root / ('direction_'+name+'.py')).write_text((root/'direction_top.py').read_text().replace(old,replacement))
