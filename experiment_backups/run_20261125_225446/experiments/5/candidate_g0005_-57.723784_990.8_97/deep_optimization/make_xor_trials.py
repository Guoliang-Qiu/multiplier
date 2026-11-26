"""Explore globally equivalent XOR realizations and shared gate cones."""
from pathlib import Path
p=Path('/home/guoliang/multiplier/experiments/5/candidate_g0005_0003/deep_optimization')
s=(p/'general_baseline.py').read_text()
old='''        both = self._and(a, b)
        either = self._or(a, b)
        return self._and(either, self._not(both))'''
assert s.count(old)==1
for name,new in {
'xor_sop':'return self._or(self._and(a, self._not(b)), self._and(self._not(a), b))',
'xor_nand':'return self._not(self._or(self._and(a, b), self._and(self._not(a), self._not(b))))',
'xor_nor':'return self._or(self._and(a, self._not(b)), self._and(self._not(a), b))',
'xor_pos':'return self._and(self._or(a,b), self._or(self._not(a),self._not(b)))',
}.items():
    (p/(name+'.py')).write_text(s.replace(old,'        '+new))
