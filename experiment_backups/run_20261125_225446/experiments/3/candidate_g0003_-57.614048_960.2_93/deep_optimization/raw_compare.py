"""Check raw outputs of variants on the configured external stimulus."""
import importlib.util
import numpy as np
from pathlib import Path
base=Path('/home/guoliang/multiplier/experiments/3/candidate_g0003_0008')
def load(path):
 spec=importlib.util.spec_from_file_location('variant_'+path.stem,path)
 mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 circuit=mod.build_circuit();circuit.validate();return circuit
samples=np.load('/home/guoliang/multiplier/stimulus.npy',allow_pickle=False)
reference=load(base/'partial_product_candidate.py')
for name in ('simplify_low','native_absorption','active_xor','native_and','native_xor','high_direct','sum_native'):
 candidate=load(base/'deep_optimization'/(name+'.py'))
 difference=0
 for start in range(0,len(samples),1024):
  batch=samples[start:start+1024].tolist()
  difference+=sum(x!=y for x,y in zip(reference.simulate_many(batch),candidate.simulate_many(batch)))
 print(name,'raw_difference',difference,flush=True)
