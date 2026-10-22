"""Search exact-layout low-column removal with distribution-derived offsets."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import numpy as np
from multiplier.initial_solutions import candidate_exact_rounding_optimized as base


def main():
    c, columns = base.build_partial_product_layout()
    count = 131072
    inputs = np.random.default_rng(871).integers(-256, 256, (4, count), dtype=np.int64)
    values=[]
    positions={n:i for i,n in enumerate(c.input_ids)}
    for i,node in enumerate(c.nodes):
        k=node.kind
        if i in positions:
            p=positions[i]; v=(inputs[p//9]>>(p%9))&1
        elif k=='ZERO':v=np.zeros(count,dtype=np.int64)
        elif k=='ONE':v=np.ones(count,dtype=np.int64)
        elif k=='NOT':v=1-values[node.inputs[0]]
        else:
            a,b=(values[n] for n in node.inputs)
            v=a&b if k=='AND' else a|b if k=='OR' else a^b
        values.append(v)
    width=len(columns)
    signed=lambda x:(x+(1<<(width-1)))%(1<<width)-(1<<(width-1))
    heap=sum(values[n]*(1<<k) for k,b in enumerate(columns) for n in b)
    truth=inputs[0]*inputs[1]+inputs[2]*inputs[3]
    assert np.array_equal(signed(heap),truth)
    power=np.mean((truth/128)**2)
    removed=np.zeros(count,dtype=np.int64)
    for cut in range(1,8):
        removed+=sum(values[n]*(1<<(cut-1)) for n in columns[cut-1])
        best=None
        # Integer compensation centered on the removed group's mean. Score
        # the SAME assignments, preserving correlation with the full product.
        center=int(removed.mean())
        for offset in range(max(0,center-128),center+129):
            out=signed(heap-removed+offset)
            mse=float(np.mean((np.floor(out/128+.5)-truth/128)**2))
            if best is None or mse<best[0]:best=(mse,offset)
        mse,offset=best
        cc,bb=base.build_partial_product_layout()
        for k in range(cut):bb[k]=[]
        for k in range(width):
            if offset>>k&1:bb[k].append(1)
        full=base.build_circuit_from_columns(cc,bb)
        print(dict(cut=cut,offset=offset,removed_mean=float(removed.mean()),
                   cost=full.gatecost().total,evm=float(10*np.log10(mse/power))),flush=True)
    # Starting at cut=4, enumerate column-4 subsets and compensating constants.
    low=sum(values[n]*(1<<k) for k in range(4) for n in columns[k])
    results=[]
    for mask in range(1,1<<len(columns[4])):
        drop=[i for i in range(len(columns[4])) if mask>>i&1]
        loss=low+sum(values[columns[4][i]]*16 for i in drop)
        for offset in range(0,129,16):
            out=signed(heap-loss+offset)
            mse=float(np.mean((np.floor(out/128+.5)-truth/128)**2))
            evm=float(10*np.log10(mse/power))
            if evm> -57.64:continue
            cc,bb=base.build_partial_product_layout()
            for k in range(4):bb[k]=[]
            bb[4]=[n for i,n in enumerate(bb[4]) if i not in drop]
            for k in range(width):
                if offset>>k&1:bb[k].append(1)
            cost=base.build_circuit_from_columns(cc,bb).gatecost().total
            results.append((cost,evm,drop,offset))
    print('cut4 subset survivors',len(results))
    for row in sorted(results)[:20]:print(row)


if __name__=='__main__':main()
