"""Reuse prior Booth-row XORs in the top +/-1 row, exact slot replacement.

Let h=q8, l=q7, x=m[k]. Top-row bit
(~h & l & x) | (h & ~l & ~x) = (h XOR l) & ~(l XOR x).
The preceding Booth row already computed (l XOR x). Reuse it rather
than separately gating x and ~x. Columns and compression order are preserved.
"""
from multiplier.experiments.conditional_compensation.candidate_x_reuse import Candidate as Base


class Candidate(Base):
    def _product_columns(self,a,b,c,d,zero,one):
        cols=super()._product_columns(a,b,c,d,zero,one)
        for m,q in ((a,b),(c,d)):
            pos=self._and(self._not(q[8]),q[7])
            neg=self._and(q[8],self._not(q[7]))
            active=self._or(pos,neg)
            for k in range(3,9):
                old=self._or(self._and(pos,m[k]),self._and(neg,self._not(m[k])))
                new=self._and(active,self._not(self._xor(q[7],m[k])))
                col=8+k
                if k==8:
                    old=self._not(old);new=self._not(new)
                assert cols[col].count(old)==1
                cols[col][cols[col].index(old)]=new
        return cols


def build_circuit():return Candidate()._build_circuit()
