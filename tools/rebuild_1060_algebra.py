"""Try exact Boolean factoring on the 1060 candidate only."""
from multiplier.initial_solutions import candidate_g0001_0005_joint1060 as source
from multiplier.circuit import MultiplierCircuit


class Algebra(MultiplierCircuit):
    _USE_ABSORPTION=True
    def _gate(self,kind,*inputs):
        if kind in ('AND','OR'):
            a,b=inputs; dual='AND' if kind=='OR' else 'OR'
            na,nb=self.nodes[a],self.nodes[b]
            if na.kind==nb.kind==dual:
                shared=set(na.inputs)&set(nb.inputs)
                if shared:
                    x=min(shared)
                    y=na.inputs[1] if na.inputs[0]==x else na.inputs[0]
                    z=nb.inputs[1] if nb.inputs[0]==x else nb.inputs[0]
                    return self._gate(dual,x,self._gate(kind,y,z))
            # x + (~x*y) = x+y and x*(~x+y)=x*y
            for x,o in ((a,b),(b,a)):
                no=self.nodes[o]
                if no.kind==dual:
                    for p,q in (no.inputs,no.inputs[::-1]):
                        np,nx=self.nodes[p],self.nodes[x]
                        if ((np.kind=='NOT' and np.inputs[0]==x) or
                            (nx.kind=='NOT' and nx.inputs[0]==p)):
                            return self._gate(kind,x,q)
        return super()._gate(kind,*inputs)


def build_circuit():
    old=source.build_circuit();new=Algebra();mp={}
    for i,node in enumerate(old.nodes):
        if not node.inputs:
            x=new.add(node.kind)
            if node.kind=='ZERO':new._zero=x
            elif node.kind=='ONE':new._one=x
        else:x=new._gate(node.kind,*(mp[j] for j in node.inputs))
        mp[i]=x
    new.input_ids=[mp[i] for i in old.input_ids];new.output_ids=[mp[i] for i in old.output_ids]
    return new
