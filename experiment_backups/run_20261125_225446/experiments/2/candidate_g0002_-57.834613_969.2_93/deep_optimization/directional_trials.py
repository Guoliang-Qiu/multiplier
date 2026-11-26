"""Test architecture-preserving biased-slot and compensation changes."""
import importlib.util
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parent
SRC=(ROOT/'general_baseline.py').read_text()
STIM=np.load('/home/guoliang/multiplier/stimulus.npy')

def load(path):
    spec=importlib.util.spec_from_file_location('trial',path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return mod
base=load(ROOT/'general_baseline.py').build_circuit()
reference=base.simulate_many(STIM[:4096].tolist())
variants={}
for col,idx in ((4,2),(4,4),(5,2),(6,2),(7,2),(8,2),(10,9),(11,0),(16,1)):
    key=f'zero_{col}_{idx}'
    variants[key]=SRC.replace('        return cols\n\n    def _compress_columns', f'        cols[{col}][{idx}] = zero\n        return cols\n\n    def _compress_columns')
for col,idx in ((4,2),(4,4),(5,2),(6,2),(7,2),(8,2)):
    key=f'delete_{col}_{idx}'
    variants[key]=SRC.replace('        return cols\n\n    def _compress_columns', f'        cols[{col}].pop({idx})\n        return cols\n\n    def _compress_columns')
for col in (4,5,6,7,8,9,10,11,12,13,15,18):
    key=f'comp_{col}'
    variants[key]=SRC.replace('        return cols\n\n    def _compress_columns', f'        cols[{col}].append(one)\n        return cols\n\n    def _compress_columns')
for name,src in variants.items():
    path=ROOT/(name+'.py');path.write_text(src)
    try:
        c=load(path).build_circuit();c.validate()
        output=c.simulate_many(STIM[:4096].tolist())
        diff=np.asarray(output,dtype=np.int64)-np.asarray(reference,dtype=np.int64)
        print(name, c.gatecost().total,c.partial_product_count,'exact',np.count_nonzero(diff)==0,'raw_diff_mean',float(diff.mean()),'raw_diff_max',int(np.max(np.abs(diff))),flush=True)
    except Exception as exc:
        print(name,'FAIL',repr(exc),flush=True)
