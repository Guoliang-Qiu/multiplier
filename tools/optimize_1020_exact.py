"""Bounded, explicit cofactor identities; no external synthesis.

x AND f = x AND f[x=1]; x OR f = x OR f[x=0].
The bound limits rewriting to local subexpressions; NOT is handled explicitly.
"""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from multiplier.circuit import MultiplierCircuit
from multiplier.initial_solutions import candidate_dist_recoded1020 as source


class LocalCircuit(MultiplierCircuit):
    _USE_ABSORPTION = True
    depth = 2

    def cofactor(self, n, x, value, depth):
        if n == x:
            return self._one if value else self._zero
        if depth == 0:
            return n
        node = self.nodes[n]
        if not node.inputs:
            return n
        args = tuple(self.cofactor(j,x,value,depth-1) for j in node.inputs)
        if args == node.inputs:
            return n
        return super()._gate(node.kind,*args)

    def _gate(self, kind, *inputs):
        if kind in ('AND','OR'):
            a,b = inputs
            # Keep one operand fixed while restricting the other, then use
            # the exact outer operator. Never assume both operands fixed.
            for x,n in ((a,b),(b,a)):
                reduced = self.cofactor(n,x,kind=='AND',self.depth)
                if reduced != n:
                    return super()._gate(kind,x,reduced)
        return super()._gate(kind,*inputs)


def build_variant(depth=2):
    old=source.build_circuit();new=LocalCircuit();new.depth=depth;mapping={}
    for i,node in enumerate(old.nodes):
        if not node.inputs:
            n=new.add(node.kind)
            if node.kind=='ZERO':new._zero=n
            if node.kind=='ONE':new._one=n
        else:
            n=new._gate(node.kind,*(mapping[j] for j in node.inputs))
        mapping[i]=n
    new.input_ids=[mapping[i] for i in old.input_ids]
    new.output_ids=[mapping[i] for i in old.output_ids]
    return new


def build_circuit():
    return build_variant(2)


if __name__=='__main__':
    import numpy as np
    x=np.random.default_rng(102020).integers(-256,256,(8192,4)).tolist()
    old=source.build_circuit();ref=old.simulate_many(x)
    print('baseline',old.gatecost().total)
    for depth in (1,2,3,4):
        c=build_variant(depth)
        assert ref==c.simulate_many(x)
        print('depth',depth,'cost',c.gatecost().total,'8192 raw outputs match',flush=True)
