"""Real-circuit low-bit replacement and compensation search from 1020."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import json
import numpy as np
from multiplier.initial_solutions import candidate_dist_recoded1020 as base
from multiplier.tools.search_existing_subcones import simulate


class Probe(base.Candidate):
    change=None
    def _product_columns(self,q,m,z,o,cut):
        cols=super()._product_columns(q,m,z,o,cut)
        if self.change:
            col,pos,path,side=self.change
            if side & (1 if q[0]==self.input_ids[9] else 2):
                n=cols[col][pos]
                if path=='zero':n=z
                elif path=='one':n=o
                else:
                    for p in path:n=self.nodes[n].inputs[int(p)]
                cols[col][pos]=n
        return cols


def main():
    rng=np.random.default_rng(71020)
    x=rng.integers(-256,256,(4,8192),dtype=np.int64)
    ref=(x[0]*x[1]+x[2]*x[3])/128
    def score(c):
        raw=simulate(c,x)
        return float(10*np.log10(np.mean((np.floor(raw/128+.5)-ref)**2)/np.mean(ref**2)))
    baseline=score(base.build_circuit());print('baseline',baseline,flush=True)
    layout,cols=Probe()._build_circuit(layout_only=True)
    rows=[]
    for col in range(4,7):
        for pos in range(len(cols[col])//2):
            for side in (1,2,3):
                # Build valid paths for both products: CD already has a different subcone.
                half=(len(cols[col])-int(col==4))//2
                nodes=[cols[col][pos+i*half] for i in range(2) if side&(1<<i)]
                paths=['zero','one']
                def walk(ns,path,depth):
                    if not depth:return
                    for j in range(min(len(layout.nodes[n].inputs) for n in ns)):
                        p=path+str(j);paths.append(p)
                        walk([layout.nodes[n].inputs[j] for n in ns],p,depth-1)
                walk(nodes,'',3)
                for path in paths:
                    for offset in (0,8,16,24,32,40,48,56,64):
                        c=Probe();c.change=(col,pos,path,side)
                        c.EXTRA_ONE={k:1 for k in range(7) if offset>>k&1}
                        c=c._build_circuit();cost=c.gatecost().total
                        if cost>=1020:continue
                        evm=score(c)
                        if evm-baseline<0.35:
                            rows.append(dict(cost=cost,evm=evm,change=(col,pos,path,side),offset=offset))
    front=[r for r in rows if not any(s['cost']<=r['cost'] and s['evm']<=r['evm'] and
            (s['cost']<r['cost'] or s['evm']<r['evm']) for s in rows)]
    for r in sorted(front,key=lambda r:r['cost']):print(json.dumps(r),flush=True)
    Path('/tmp/opencode/search1020approx.json').write_text(json.dumps(rows,indent=2))


if __name__=='__main__':main()
