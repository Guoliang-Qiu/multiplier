"""Screen existing subcone replacements through the actual candidate circuit."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import json
import numpy as np
from multiplier.initial_solutions import candidate_g0001_0005 as base


class Probe(base.Candidate):
    changes = ()  # (column, position, path to existing child, product mask)

    def _product_columns(self, q, m, z, o, cut):
        cols = super()._product_columns(q, m, z, o, cut)
        side = 1 if q[0] == self.input_ids[9] else 2
        for col, pos, path, mask in self.changes:
            if mask & side:
                n = cols[col][pos]
                if path == 'zero': n = z
                elif path == 'one': n = o
                else:
                    for p in path: n = self.nodes[n].inputs[int(p)]
                cols[col][pos] = n
        return cols


def simulate(c, x):
    positions = {n:i for i,n in enumerate(c.input_ids)}
    values = []
    for i,n in enumerate(c.nodes):
        if i in positions:
            p=positions[i]; v=(x[p//9]>>(p%9))&1
        elif n.kind=='ZERO': v=np.zeros(x.shape[1],dtype=np.int64)
        elif n.kind=='ONE': v=np.ones(x.shape[1],dtype=np.int64)
        elif n.kind=='NOT': v=1-values[n.inputs[0]]
        else:
            a,b=(values[j] for j in n.inputs)
            if n.kind=='AND':v=a&b
            elif n.kind=='OR':v=a|b
            elif n.kind=='XOR':v=a^b
            else:raise ValueError(n.kind)
        values.append(v)
    raw=sum(values[n]*(1<<k) for k,n in enumerate(c.output_ids))
    width=len(c.output_ids)
    return (raw+(1<<(width-1)))%(1<<width)-(1<<(width-1))


def main():
    x=np.random.default_rng(984).integers(-256,256,(4,8192),dtype=np.int64)
    ref=(x[0]*x[1]+x[2]*x[3])/128
    power=np.mean(ref**2)
    def metric(c):
        y=simulate(c,x)
        return float(10*np.log10(np.mean((np.floor(y/128+.5)-ref)**2)/power))
    original=base.build_circuit()
    assert simulate(original,x[:,:128]).tolist()==original.simulate_many(x[:,:128].T.tolist())
    baseline=metric(original)
    print('baseline',baseline,flush=True)
    layout,cols=base.build_partial_product_layout()
    rows=[]
    for col in range(2,6):
        for pos in range(len(cols[col])//2):
            n=cols[col][pos]
            paths=['zero','one','0','1']
            for p in ('0','1'):
                child=layout.nodes[n].inputs[int(p)]
                paths += [p+str(i) for i in range(len(layout.nodes[child].inputs))]
            for path in paths:
                for mask in (1,2,3):
                    c=Probe();c.changes=((col,pos,path,mask),); c=c._build_circuit()
                    cost=c.gatecost().total
                    if cost>=1114:continue
                    evm=metric(c)
                    if evm< -57.6:
                        rows.append(dict(cost=cost,evm=evm,changes=[[col,pos,path,mask]]))
    frontier=[r for r in rows if not any(s['cost']<=r['cost'] and s['evm']<=r['evm']
              and (s['cost']<r['cost'] or s['evm']<r['evm']) for s in rows)]
    for r in sorted(frontier,key=lambda r:r['cost']):print(json.dumps(r),flush=True)
    Path('/tmp/opencode/subcone_screen.json').write_text(json.dumps(rows,indent=2))


if __name__=='__main__':main()
