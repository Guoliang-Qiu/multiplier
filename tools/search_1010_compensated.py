"""Joint low-column edits with compensation; real circuit simulation."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import itertools
import json
import numpy as np
from multiplier.tools.search_1037_deep import Probe,base,simulate


def main():
    x=np.random.default_rng(5110).integers(-256,256,(4,4096),dtype=np.int64)
    ref=(x[0]*x[1]+x[2]*x[3])/128
    power=np.mean(ref**2)
    def score(c):
        y=simulate(c,x)
        return float(10*np.log10(np.mean((np.floor(y/128+.5)-ref)**2)/power))
    baseline=score(base.build_circuit())
    print('sample baseline',baseline,flush=True)
    # Enumerate low-column pair replacements with alternate rounding offsets.
    options=[(4,pos,path,mask) for pos in range(3)
             for path in ('zero','one','0','1') for mask in (1,2,3)]
    rows=[]
    for aa,bb in itertools.combinations(options,2):
        if aa[:2]==bb[:2]:continue
        for offset in (0,8,16,24,32,40,48,56,64):
            q=Probe();q.changes=(aa,bb)
            q.EXTRA_ONE={k:1 for k in range(7) if offset>>k&1}
            c=q._build_circuit();cost=c.gatecost().total
            if cost>1020:continue
            ev=score(c)
            if ev-baseline<=0.26:
                rows.append(dict(cost=cost,evm=ev,changes=(aa,bb),offset=offset))
    front=[r for r in rows if not any(s['cost']<=r['cost'] and s['evm']<=r['evm'] and
           (s['cost']<r['cost'] or s['evm']<r['evm']) for s in rows)]
    for r in sorted(front,key=lambda r:(r['cost'],r['evm'])):print(json.dumps(r),flush=True)
    Path('/tmp/opencode/1010_compensated.json').write_text(json.dumps(rows,indent=2))


if __name__=='__main__':main()
