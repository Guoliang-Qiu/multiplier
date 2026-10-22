"""Bounded exact rebuild comparison for 1010 and 1015 candidates."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import numpy as np
from multiplier.circuit import MultiplierCircuit
from multiplier.initial_solutions import candidate_dist_1020_to1010 as c1010
from multiplier.initial_solutions import candidate_dist_1020_to1015 as c1015


class Algebra(MultiplierCircuit):
    _USE_ABSORPTION=True
    depth=1
    def _gate(self,k,*ins):
        if k in ('AND','OR'):
            a,b=ins; dual='OR' if k=='AND' else 'AND'; na,nb=self.nodes[a],self.nodes[b]
            if na.kind==nb.kind==dual:
                common=set(na.inputs)&set(nb.inputs)
                if common:
                    x=min(common);y=na.inputs[1] if na.inputs[0]==x else na.inputs[0];z=nb.inputs[1] if nb.inputs[0]==x else nb.inputs[0]
                    return self._gate(dual,x,self._gate(k,y,z))
            for x,o in ((a,b),(b,a)):
                no=self.nodes[o]
                if no.kind==dual:
                    for p,q in (no.inputs,no.inputs[::-1]):
                        np_,nx=self.nodes[p],self.nodes[x]
                        if ((np_.kind=='NOT' and np_.inputs[0]==x) or (nx.kind=='NOT' and nx.inputs[0]==p)):
                            return self._gate(k,x,q)
        return super()._gate(k,*ins)


def rebuild(source):
    old=source.build_circuit();new=Algebra();mp={}
    for i,node in enumerate(old.nodes):
        if not node.inputs:
            x=new.add(node.kind)
            if node.kind=='ZERO':new._zero=x
            if node.kind=='ONE':new._one=x
        else:x=new._gate(node.kind,*(mp[j] for j in node.inputs))
        mp[i]=x
    new.input_ids=[mp[i] for i in old.input_ids];new.output_ids=[mp[i] for i in old.output_ids];return old,new


def main():
    x=np.random.default_rng(1015).integers(-256,256,(8192,4)).tolist()
    for name,source in [('1010',c1010),('1015',c1015)]:
        old,new=rebuild(source);assert old.simulate_many(x)==new.simulate_many(x)
        print(name,'old',old.gatecost().total,'new',new.gatecost().total,'8192 match',flush=True)


if __name__=='__main__':main()
