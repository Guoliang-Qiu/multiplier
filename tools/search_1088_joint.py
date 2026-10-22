"""Second-step existing-subcone search retaining the 1088 approximation."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import json
import numpy as np
from multiplier.tools.search_existing_subcones import Probe, simulate, base


def main():
    x = np.random.default_rng(1984).integers(-256,256,(4,8192),dtype=np.int64)
    ref = (x[0]*x[1]+x[2]*x[3])/128
    power = np.mean(ref**2)
    def metric(c):
        y = simulate(c,x)
        return float(10*np.log10(np.mean((np.floor(y/128+.5)-ref)**2)/power))
    first = (2,0,'zero',3)
    c = Probe(); c.changes=(first,); c=c._build_circuit()
    print('baseline',c.gatecost().total,metric(c),flush=True)
    layout,cols=base.build_partial_product_layout()
    rows=[]
    for col in range(2,6):
        for pos in range(len(cols[col])//2):
            if (col,pos)==(2,0):continue
            n=cols[col][pos]
            paths=['zero','one','0','1']
            for p in ('0','1'):
                child=layout.nodes[n].inputs[int(p)]
                paths += [p+str(i) for i in range(len(layout.nodes[child].inputs))]
            for path in paths:
                for mask in (1,2,3):
                    changes=(first,(col,pos,path,mask))
                    c=Probe(); c.changes=changes; c=c._build_circuit()
                    cost=c.gatecost().total
                    if cost>=1088:continue
                    evm=metric(c)
                    if evm < -57.65:
                        rows.append(dict(cost=cost,evm=evm,changes=changes))
    frontier=[r for r in rows if not any(s['cost']<=r['cost'] and s['evm']<=r['evm']
              and (s['cost']<r['cost'] or s['evm']<r['evm']) for s in rows)]
    for row in sorted(frontier,key=lambda r:r['cost']): print(json.dumps(row),flush=True)
    Path('/tmp/opencode/joint1088.json').write_text(json.dumps(rows,indent=2))


if __name__=='__main__':main()
