"""Search low-column groups against quantized error; never edit the baseline."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import itertools
import json
import numpy as np
from multiplier.initial_solutions.candidate_g0000_0001 import Candidate


def main():
    c, cols = Candidate()._build_circuit(layout_only=True)
    full = Candidate()._build_circuit()
    size = 32768
    inputs = np.random.default_rng(812).integers(-256,256,(4,size),dtype=np.int64)
    values=[]
    deps=[]
    for idx,n in enumerate(full.nodes):
        k=n.kind
        ds=set().union(*(deps[i] for i in n.inputs))
        if k.startswith('IN_'):
            i=full.input_ids.index(idx); v=(inputs[i//9]>>(i%9))&1; ds={i}
        elif k=='ZERO': v=np.zeros(size,dtype=np.int64)
        elif k=='ONE': v=np.ones(size,dtype=np.int64)
        elif k=='NOT': v=1-values[n.inputs[0]]
        else:
            a,b=(values[i] for i in n.inputs)
            v=a&b if k=='AND' else a|b if k=='OR' else a^b
        values.append(v); deps.append(ds)
    raw=sum(values[n]*(1<<k) for k,n in enumerate(full.output_ids))
    signed=lambda x:(x+(1<<18))%(1<<19)-(1<<18)
    raw=signed(raw)
    heap=sum(values[n]*(1<<k) for k,b in enumerate(cols) for n in b)
    assert np.array_equal(raw,signed(heap//64*64))
    ref=(inputs[0]*inputs[1]+inputs[2]*inputs[3])/128
    score=lambda r:float(np.mean((np.floor(r/128+.5)-ref)**2))
    baseline=score(raw)
    print('baseline',baseline,flush=True)
    def cd(n):
        if n<2:return n
        if n in c.input_ids[:18]:return c.input_ids[c.input_ids.index(n)+18]
        return n+210
    rows=[]
    # Re-encode subsets in columns 4 and 5 as a constant plus one existing bit.
    for col in (4,5):
        half=len(cols[col])//2
        for count in range(1,half+1):
            for positions in itertools.combinations(range(half),count):
                old=[cols[col][p] for p in positions]
                support=set().union(*(deps[n] for n in old))
                candidates=[n for n in range(248) if deps[n]<=support]
                original=sum(values[n]+values[cd(n)] for n in old)
                for n in candidates:
                    for constant in range(count):
                        delta=(values[n]+values[cd(n)]+2*constant-original)*(1<<col)
                        r=signed((heap+delta)//64*64)
                        mse=score(r)
                        if mse<=baseline*1.025:
                            rows.append((mse,col,positions,n,constant))
    print('screen survivors',len(rows),flush=True)
    results=[]
    for mse,col,positions,n,constant in sorted(rows):
        buckets=[list(b) for b in cols]; half=len(cols[col])//2
        remove=set(positions)|{p+half for p in positions}
        buckets[col]=[v for i,v in enumerate(buckets[col]) if i not in remove]
        buckets[col]+=[n,cd(n)]+[1]*(2*constant)
        rebuilt=Candidate()._build_circuit(columns=buckets)
        cost=rebuilt.gatecost().total
        if cost<1000:
            row=dict(mse=mse,ratio=mse/baseline,column=col,positions=positions,node=n,constant=constant,cost=cost)
            results.append(row)
    results.sort(key=lambda r:(r['mse'],r['cost']))
    for row in results[:25]:print(json.dumps(row),flush=True)
    print('cost survivors',len(results))
    # Joint adjacent-column substitutions: preserve correlation through the
    # same assignments and evaluate rounding after summing both perturbations.
    opts=[]
    for col in (4,5):
        group=[]
        half=len(cols[col])//2
        for pos in range(half):
            old=cols[col][pos]
            for n in range(248):
                if not deps[n]<=deps[old] or n==old:continue
                delta=(values[n]+values[cd(n)]-values[old]-values[cd(old)])*(1<<col)
                group.append((col,pos,n,delta))
        opts.append(group)
    joint=[]
    for a in opts[0]:
        for b in opts[1]:
            mse=score(signed((heap+a[3]+b[3])//64*64))
            if mse>baseline*1.004:continue
            buckets=[list(x) for x in cols]
            for col,pos,n,_ in (a,b):
                buckets[col][pos]=n
                buckets[col][pos+len(cols[col])//2]=cd(n)
            cost=Candidate()._build_circuit(columns=buckets).gatecost().total
            if cost<1000:
                joint.append((mse,cost,a[:3],b[:3]))
    print('joint survivors',len(joint))
    for row in sorted(joint)[:25]:print(row,flush=True)
    # Allow one-sided changes and small constant compensation in columns 4..6.
    compensated=[]
    for group in opts:
        for col,pos,n,delta in group:
            for symmetric in (False,True):
                change=delta if symmetric else (values[n]-values[cols[col][pos]])*(1<<col)
                for offset in (-32,-16,0,16,32):
                    mse=score(signed((heap+change+offset)//64*64))
                    if mse>baseline*1.004:continue
                    # Negative compensation is represented modulo output width.
                    buckets=[list(x) for x in cols]
                    buckets[col][pos]=n
                    if symmetric:buckets[col][pos+len(cols[col])//2]=cd(n)
                    for k in range(19):
                        if ((offset% (1<<19))>>k)&1:buckets[k].append(1)
                    cost=Candidate()._build_circuit(columns=buckets).gatecost().total
                    if cost<1000:compensated.append((mse,cost,col,pos,n,symmetric,offset))
    print('compensated survivors',len(compensated))
    for row in sorted(compensated)[:25]:print(row,flush=True)


if __name__=='__main__':main()
