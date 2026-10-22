"""Search actual circuits derived from the validated 1025 point."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import json
import numpy as np
from multiplier.initial_solutions import candidate_dist_recoded1025 as base
from multiplier.tools.search_existing_subcones import simulate


class Probe(base.Candidate):
    change = None
    def _product_columns(self,q,m,z,o,cut):
        cols=super()._product_columns(q,m,z,o,cut)
        if self.change:
            col,pos,path,mask=self.change
            if mask & (1 if q[0]==self.input_ids[9] else 2):
                n=cols[col][pos]
                if path=='zero':n=z
                elif path=='one':n=o
                else:
                    for p in path:n=self.nodes[n].inputs[int(p)]
                cols[col][pos]=n
        return cols


def main():
    x=np.random.default_rng(61025).integers(-256,256,(4,8192),dtype=np.int64)
    ref=(x[0]*x[1]+x[2]*x[3])/128
    def metric(c):
        raw=simulate(c,x)
        return float(10*np.log10(np.mean((np.floor(raw/128+.5)-ref)**2)/np.mean(ref**2)))
    baseline=metric(base.build_circuit())
    print('baseline',baseline,flush=True)
    c,cols=Probe()._build_circuit(layout_only=True)
    rows=[]
    for col in range(4,7):
        for pos in range(len(cols[col])//2):
            n=cols[col][pos]; paths=['zero','one']
            for i,child in enumerate(c.nodes[n].inputs):
                paths.append(str(i))
                paths.extend(str(i)+str(j) for j in range(len(c.nodes[child].inputs)))
            for path in paths:
                for mask in (1,2,3):
                    for offset in (0,16,32,48,64):
                        q=Probe();q.change=(col,pos,path,mask)
                        q.EXTRA_ONE={k:1 for k in range(7) if offset>>k&1}
                        circ=q._build_circuit();cost=circ.gatecost().total
                        if cost>=1025:continue
                        evm=metric(circ)
                        if evm-baseline<0.4:
                            rows.append(dict(cost=cost,evm=evm,change=q.change,offset=offset))
    front=[r for r in rows if not any(s['cost']<=r['cost'] and s['evm']<=r['evm'] and
           (s['cost']<r['cost'] or s['evm']<r['evm']) for s in rows)]
    for r in sorted(front,key=lambda r:r['cost']):print(json.dumps(r),flush=True)
    Path('/tmp/opencode/search1025.json').write_text(json.dumps(rows,indent=2))


if __name__=='__main__':main()
