"""Analyze 3:2 compressor sum/carry joint distributions in g0001_0005."""
from multiplier.initial_solutions import candidate_g0001_0005 as base
from collections import Counter


class Probe(base.Candidate):
    def __init__(self):
        super().__init__(); self.calls=[]
    def _add3(self,a,b,c):
        out=super()._add3(a,b,c); self.calls.append((a,b,c,*out)); return out


def main():
    p=Probe(); circuit=p._build_circuit()
    print('cost',circuit.gatecost().total,'compressors',len(p.calls))
    for i,(a,b,c,s,carry) in enumerate(p.calls):
        # Exact compressor output is a 2-bit integer. Uniform local input is
        # not assumed here; this reports structural kinds for selection.
        print(i, 'in',a,b,c,'->',s,carry,
              [circuit.nodes[x].kind for x in (a,b,c,s,carry)])


if __name__=='__main__':main()
