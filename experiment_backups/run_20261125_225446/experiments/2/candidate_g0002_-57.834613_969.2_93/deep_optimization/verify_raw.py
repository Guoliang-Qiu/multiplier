"""Compare raw output bits over the entire configured external stimulus."""
import importlib.util
import numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def load(p):
    s=importlib.util.spec_from_file_location('comparison_'+p.stem,p)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
    return m.build_circuit()
a=load(ROOT.parent/'partial_product_candidate.py')
b=load(ROOT/'general_baseline_refined.py')
stim=np.load('/home/guoliang/multiplier/stimulus.npy')
errors=0
for start in range(0,len(stim),2048):
    chunk=stim[start:start+2048].tolist()
    errors+=sum(x!=y for x,y in zip(a.simulate_many(chunk),b.simulate_many(chunk)))
print('raw_output_mismatches',errors,'samples',len(stim))
assert errors==0
