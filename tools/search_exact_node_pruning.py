"""Sampled node-pruning search on the exact optimized layout."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import numpy as np
from multiplier.initial_solutions import candidate_exact_rounding_optimized as base


def main():
    circuit, columns = base.build_partial_product_layout()
    count = 32768
    x = np.random.default_rng(20261021).integers(-256, 256, (4, count), dtype=np.int64)
    pos = {n:i for i,n in enumerate(circuit.input_ids)}
    values=[]
    for i,node in enumerate(circuit.nodes):
        k=node.kind
        if i in pos:
            p=pos[i]; v=(x[p//9]>>(p%9))&1
        elif k=='ZERO':v=np.zeros(count,dtype=np.int64)
        elif k=='ONE':v=np.ones(count,dtype=np.int64)
        elif k=='NOT':v=1-values[node.inputs[0]]
        else:
            a,b=(values[n] for n in node.inputs)
            v=a&b if k=='AND' else a|b if k=='OR' else a^b
        values.append(v)
    width=len(columns)
    raw=sum(values[n]*(1<<k) for k,b in enumerate(columns) for n in b)
    ref=(x[0]*x[1]+x[2]*x[3])/128
    q=lambda z:np.floor(((z+(1<<(width-1)))%(1<<width)-(1<<(width-1)))/128+.5)
    baseline=float(np.mean((q(raw)-ref)**2))
    baseline_cost=base.build_circuit().gatecost().total
    print('baseline',baseline,'cost',baseline_cost,flush=True)
    results=[]
    for col in range(0,5):
        for index,node_id in enumerate(columns[col]):
            # Try removing this node and compensating with 0..3 ONEs in the
            # same column.  This includes the distribution-derived mean choice.
            for compensation in range(4):
                delta=(-values[node_id]+compensation)*(1<<col)
                mse=float(np.mean((q(raw+delta)-ref)**2))
                if mse>baseline*1.30:continue
                buckets=[list(b) for b in columns]
                buckets[col].pop(index)
                buckets[col].extend([1]*compensation)
                # Build on a fresh layout circuit because the compressor mutates buckets.
                fresh, _=base.build_partial_product_layout()
                rebuilt=base.build_circuit_from_columns(fresh,buckets)
                cost=rebuilt.gatecost().total
                if cost<baseline_cost:
                    results.append((mse,cost,col,index,node_id,compensation,float(delta.mean())))
    for row in sorted(results)[:50]:print(row,flush=True)


if __name__=='__main__':main()
