"""Try alternative exact majority/parity cells on 1010/1015."""
from multiplier.initial_solutions import candidate_dist_1020_to1010 as a,candidate_dist_1020_to1015 as b
from multiplier.circuit import MultiplierCircuit
from itertools import permutations
import numpy as np


class Probe(MultiplierCircuit):
    source=None
    def _fa(self,a,b,c):
        best=None;start=len(self.nodes);cache=self._gate_cache.copy()
        for order in permutations((a,b,c)):
            self.nodes[start:]=[];self._gate_cache=cache.copy();x,y,z=order
            ac=self._and(x,z);ao=self._or(x,z);xn=self._or(ac,self._not(ao));w=self._or(y,xn)
            out=(self._or(self._not(w),self._and(y,xn)),self._and(ao,w))
            used=set();st=list(out)
            while st:
                n=st.pop()
                if n<start or n in used:continue
                used.add(n);st.extend(self.nodes[n].inputs)
            cost=sum(self.components.require(self.nodes[n].kind).gate_cost for n in used)
            if best is None or cost<best[0]:best=(cost,out,self._gate_cache.copy(),list(self.nodes[start:]))
        self.nodes[start:]=best[3];self._gate_cache=best[2];return best[1]


def main():
    for name,source in [('1010',a),('1015',b)]:
        old=source.build_circuit();x=np.random.default_rng(10).integers(-256,256,(1024,4)).tolist();expected=old.simulate_many(x)
        p=Probe();new=p._build_circuit() if False else None
        print(name,'baseline',old.gatecost().total)


if __name__=='__main__':main()
