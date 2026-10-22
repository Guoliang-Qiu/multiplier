"""Exact two-output G using retained X, reinjected at original slot positions."""
from multiplier.initial_solutions.candidate_dist_1020_to1015 import Candidate as Base


class Candidate(Base):
    def _product_columns(self,a,b,c,d,zero,one):
        cols=super()._product_columns(a,b,c,d,zero,one)
        # IDs below belong to this unchanged baseline pre-compression layout.
        assert cols[4][:2]==[91,155]
        assert self.nodes[43].kind=='AND' and self.nodes[55].kind=='AND'
        # n43=B1&~B0. Under n43=1, (A3 XOR B1)=~A3.
        g0=self._or(self._and(11,55),self._and(43,self._not(5)))
        p=self._or(self._and(14,self._not(38)),self._and(3,self._not(14)))
        g1=self._or(self._and(110,123),self._and(119,p))
        cols[4][0]=g0
        cols[4][1]=g1
        return cols


def build_circuit():return Candidate()._build_circuit()
