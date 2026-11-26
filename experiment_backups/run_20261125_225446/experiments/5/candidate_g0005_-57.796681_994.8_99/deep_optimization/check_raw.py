import importlib.util
import numpy as np
from pathlib import Path
base=Path('/home/guoliang/multiplier/experiments/5/candidate_g0005_0006')
def load(path):
    spec=importlib.util.spec_from_file_location(path.stem,path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.build_circuit()
old=load(base/'partial_product_candidate.py')
import sys
new=load(base/'deep_optimization'/ (sys.argv[1] if len(sys.argv)>1 else 'general.py'))
samples=np.load('/home/guoliang/multiplier/stimulus.npy',allow_pickle=False)
for start in range(0,len(samples),16384):
    part=samples[start:start+16384].tolist()
    lhs=old.simulate_many(part)
    rhs=new.simulate_many(part)
    if lhs!=rhs:
        indices=[i for i,(a,b) in enumerate(zip(lhs,rhs)) if a!=b]
        print('NON_EQUIVALENT',start+indices[0],len(indices),lhs[indices[0]],rhs[indices[0]],flush=True)
        raise SystemExit(1)
print('EMPIRICALLY_RAW_EQUIVALENT',len(samples))
