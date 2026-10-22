"""Third-step subcone screen starting from the validated 1076/1084 points."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import json
import numpy as np
from multiplier.tools.search_existing_subcones import Probe, simulate, base


def main():
    x=np.random.default_rng(2984).integers(-256,256,(4,8192),dtype=np.int64)
    ref=(x[0]*x[1]+x[2]*x[3])/128
    power=np.mean(ref**2)
    layout,cols=base.build_partial_product_layout()
    rows=[]
    for mask0 in (2,3):
        initial=((2,0,'zero',3),(2,1,'one',mask0))
        for absorption in (False,True):
            for col in range(3,6):
                for pos in range(len(cols[col])//2):
                    n=cols[col][pos]
                    paths=['zero','one','0','1']
                    for p in ('0','1'):
                        child=layout.nodes[n].inputs[int(p)]
                        paths += [p+str(i) for i in range(len(layout.nodes[child].inputs))]
                    for path in paths:
                        for mask in (1,2,3):
                            c=Probe();c._USE_ABSORPTION=absorption
                            c.changes=initial+((col,pos,path,mask),)
                            changes=c.changes
                            c=c._build_circuit();cost=c.gatecost().total
                            if cost>=1084:continue
                            raw=simulate(c,x)
                            evm=float(10*np.log10(np.mean((np.floor(raw/128+.5)-ref)**2)/power))
                            if evm< -57.65:
                                rows.append(dict(cost=cost,evm=evm,changes=changes,absorption=absorption))
    frontier=[r for r in rows if not any(s['cost']<=r['cost'] and s['evm']<=r['evm']
             and (s['cost']<r['cost'] or s['evm']<r['evm']) for s in rows)]
    for r in sorted(frontier,key=lambda r:r['cost']): print(json.dumps(r),flush=True)
    Path('/tmp/opencode/joint_next.json').write_text(json.dumps(rows,indent=2))


if __name__=='__main__':main()
