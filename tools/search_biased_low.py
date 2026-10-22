"""Screen symmetric low-column replacements using uniform-input simulation."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import numpy as np
from multiplier.initial_solutions.candidate_g0000_0001 import Candidate


def main():
    rng = np.random.default_rng(123)
    size = 131072
    inputs = rng.integers(-256, 256, (4, size), dtype=np.int64)
    c, cols = Candidate()._build_circuit(layout_only=True)
    full = Candidate()._build_circuit()
    values = {}
    for i, node in enumerate(full.nodes):
        k = node.kind
        if k.startswith('IN_'):
            idx = full.input_ids.index(i)
            v = (inputs[idx // 9] >> (idx % 9)) & 1
        elif k == 'ZERO': v = np.zeros(size, dtype=np.int64)
        elif k == 'ONE': v = np.ones(size, dtype=np.int64)
        elif k == 'NOT': v = 1-values[node.inputs[0]]
        else:
            a,b = (values[x] for x in node.inputs)
            if k == 'AND': v = a & b
            elif k == 'OR': v = a | b
            elif k == 'XOR': v = a ^ b
            else: raise ValueError(k)
        values[i] = v
    raw = sum(values[n] << i for i,n in enumerate(full.output_ids))
    raw = (raw + (1<<18)) % (1<<19) - (1<<18)
    residue = sum(values[n]*(1<<k) for k in (4,5) for n in cols[k]) % 64
    ref = (inputs[0]*inputs[1]+inputs[2]*inputs[3])/128
    def score(r): return float(np.mean((np.floor(r/128+.5)-ref)**2))
    baseline=score(raw)
    print('baseline',baseline,flush=True)
    rows=[]
    for col in (4,5):
        half=len(cols[col])//2
        for pos in range(half):
            left,right=cols[col][pos],cols[col][pos+half]
            # Candidate functions use corresponding AB/CD input indices.
            options=[('ZERO',values[0],values[0]),('ONE',values[1],values[1])]
            for i in range(18):
                a=values[c.input_ids[i]]; b=values[c.input_ids[i+18]]
                options.extend([(f'I{i}',a,b),(f'N{i}',1-a,1-b)])
            for name,a,b in options:
                delta=((a-values[left])+(b-values[right]))*(1<<col)
                changed=raw+((residue+delta)//64)*64
                changed=(changed+(1<<18))%(1<<19)-(1<<18)
                rows.append((score(changed),col,pos,name))
    for row in sorted(rows)[:20]:print(row, 'ratio',row[0]/baseline)


if __name__=='__main__':main()
