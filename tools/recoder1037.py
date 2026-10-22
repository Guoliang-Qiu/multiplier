"""Source-level joint Booth one/two control factoring, not external synthesis."""
from multiplier.initial_solutions.candidate_g0001_0000 import Candidate as Base


class Candidate(Base):
    _USE_ABSORPTION=True

    def xor_operands(self,n):
        node=self.nodes[n]
        if node.kind!='AND':return None
        for a,b in (node.inputs,node.inputs[::-1]):
            na,nb=self.nodes[a],self.nodes[b]
            if na.kind=='OR' and nb.kind=='NOT':
                inner=self.nodes[nb.inputs[0]]
                if inner.kind=='AND' and set(inner.inputs)==set(na.inputs):
                    return na.inputs
        return None

    def _and(self,a,b):
        for n,x in ((a,b),(b,a)):
            node=self.nodes[n]
            if node.kind!='NOT':continue
            ml=self.xor_operands(node.inputs[0]); hm=self.xor_operands(x)
            if not ml or not hm:continue
            overlap=set(ml)&set(hm)
            if len(overlap)!=1:continue
            mid=next(iter(overlap));low=next(i for i in ml if i!=mid);high=next(i for i in hm if i!=mid)
            if not all(self.nodes[i].kind in ('IN_B','IN_D') for i in (low,mid,high)):continue
            # ~XOR(mid,low) & XOR(high,mid)
            union=self._or(mid,low)
            intersection=super()._and(mid,low)
            return super()._and(self._not(super()._and(high,union)),self._or(high,intersection))
        return super()._and(a,b)


def build_circuit():return Candidate()._build_circuit()
