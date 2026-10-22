"""Screen actual 1037-derived circuits, including compensation interactions."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import json
import numpy as np
from multiplier.initial_solutions import candidate_g0001_0000 as base
from multiplier.tools.search_existing_subcones import simulate


class Probe(base.Candidate):
    change=None
    def _product_columns(self,q,m,z,o,cut):
        cols=super()._product_columns(q,m,z,o,cut)
        if self.change:
            col,pos,path,mask=self.change
            side=1 if q[0]==self.input_ids[9] else 2
            if mask&side:
                n=cols[col][pos]
                if path=='zero':n=z
                elif path=='one':n=o
                else:
                    for p in path:n=self.nodes[n].inputs[int(p)]
                cols[col][pos]=n
        return cols


def main():
    x=np.random.default_rng(31037).integers(-256,256,(4,8192),dtype=np.int64)
    ref=(x[0]*x[1]+x[2]*x[3])/128
    power=np.mean(ref**2)
    def metric(c):
        raw=simulate(c,x)
        return float(10*np.log10(np.mean((np.floor(raw/128+.5)-ref)**2)/power))
    c,cols=base.build_partial_product_layout()
    baseline=base.build_circuit()
    assert simulate(baseline,x[:,:64]).tolist()==baseline.simulate_many(x[:,:64].T.tolist())
    print('baseline',baseline.gatecost().total,metric(baseline),flush=True)
    rows=[]
    for col in range(4,7):
        for pos in range(len([n for n in cols[col] if n!=1])//2):
            node=cols[col][pos]
            paths=['zero','one','0','1']
            for p in ('0','1'):
                child=c.nodes[node].inputs[int(p)]
                paths.extend(p+str(i) for i in range(len(c.nodes[child].inputs)))
            for path in paths:
                for mask in (1,2,3):
                    for offset in (0,8,16,24,32):
                        q=Probe();q.change=(col,pos,path,mask)
                        q.EXTRA_ONE={k:1 for k in range(6) if offset>>k&1}
                        circ=q._build_circuit();cost=circ.gatecost().total
                        if cost>=1037:continue
                        evm=metric(circ)
                        if evm< -57.65:
                            rows.append(dict(cost=cost,evm=evm,change=q.change,offset=offset))
    front=[r for r in rows if not any(s['cost']<=r['cost'] and s['evm']<=r['evm'] and
          (s['cost']<r['cost'] or s['evm']<r['evm']) for s in rows)]
    for row in sorted(front,key=lambda r:r['cost']):print(json.dumps(row),flush=True)
    Path('/tmp/opencode/search1037.json').write_text(json.dumps(rows,indent=2))


if __name__=='__main__':main()
