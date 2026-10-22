"""Explicit p/q Booth chain identity, no synthesis or new approximation."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from itertools import product
import numpy as np
from multiplier.initial_solutions import candidate_dist_recoded1020 as source
from multiplier.circuit import MultiplierCircuit


def build_variant(mode=0, selected=None):
    old=source.build_circuit()
    lookup={(n.kind,tuple(sorted(n.inputs)) if len(n.inputs)==2 else n.inputs):i
            for i,n in enumerate(old.nodes)}
    def get(kind,*args):
        if None in args:return None
        return lookup.get((kind,tuple(sorted(args)) if len(args)==2 else args))
    targets={}
    for start in (0,18):
        u,v=old.input_ids[start:start+2]
        nand=get('NOT',get('AND',u,v))
        nor=get('NOT',get('OR',u,v))
        for bit in (1,3,5,7):
            h=old.input_ids[start+9+bit]
            p=get('OR',get('AND',h,nand),get('AND',get('NOT',h),v))
            q=get('AND',h,nor)
            t=get('AND',p,get('NOT',q))
            if t is not None:targets[t]=(u,v,h)
    if selected is not None:
        targets={n:v for index,(n,v) in enumerate(targets.items()) if index in selected}
    new=MultiplierCircuit();new._USE_ABSORPTION=True;mp={}
    for i,node in enumerate(old.nodes):
        if i in targets:
            u,v,h=(mp[n] for n in targets[i])
            if mode==0:
                n=new._xor(v,new._and(h,u))
            elif mode==1:
                hu=new._and(h,u)
                n=new._and(new._or(v,hu),new._not(new._and(v,hu)))
            else:
                uv=new._and(new._or(u,v),new._not(new._and(u,v)))
                n=new._or(new._and(h,uv),new._and(new._not(h),v))
        elif not node.inputs:
            n=new.add(node.kind)
            if node.kind=='ZERO':new._zero=n
            if node.kind=='ONE':new._one=n
        else:n=new._gate(node.kind,*(mp[j] for j in node.inputs))
        mp[i]=n
    new.input_ids=[mp[n] for n in old.input_ids]
    new.output_ids=[mp[n] for n in old.output_ids]
    return new,targets


def main():
    for u,v,h in product((0,1),repeat=3):
        p=(h & (1-(u&v)))|((1-h)&v)
        q=h & (1-(u|v))
        assert p&(1-q)==v^(h&u)
    old=source.build_circuit()
    x=np.random.default_rng(102044).integers(-256,256,(16384,4)).tolist()
    expected=old.simulate_many(x)
    for mode in range(3):
        c,targets=build_variant(mode)
        assert c.simulate_many(x)==expected
        print('mode',mode,'cost',c.gatecost().total,'matches',len(targets),
              'local 8/8; raw 16384/16384',flush=True)


if __name__=='__main__':main()
