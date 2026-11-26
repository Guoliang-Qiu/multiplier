"""Fuse A's compact MUX_XOR cell with B's correction architecture."""
from pathlib import Path
p=Path('/home/guoliang/multiplier/experiments/3/candidate_g0003_0010')
src=(p/'fused_low.py').read_text()
old='''                        val = self._or(self._and(one, get_xor(k)),
                                       self._and(two, get_xor(k - 1)))'''
new='''                        # Parent A's biased sign-dependent shared Booth cell;
                        # only rows 1 and 2 have its exact guard structure.
                        if step in (1, 2):
                            cell_neg = self._and(negative, self._not(self._and(m, low)))
                            val = self._mux_xor(one, self._bit(m_bits, k, zero),
                                                two, self._bit(m_bits, k - 1, zero), cell_neg)
                        else:
                            val = self._or(self._and(one, get_xor(k)),
                                           self._and(two, get_xor(k - 1)))'''
assert src.count(old)==1
(p/'fused_mux.py').write_text(src.replace(old,new))
src2=Path('/home/guoliang/multiplier/generations/3/candidate_g0003_-57.768547_1018_92.py').read_text()
assert src2.count(old)==1
(p/'b_mux.py').write_text(src2.replace(old,new))
