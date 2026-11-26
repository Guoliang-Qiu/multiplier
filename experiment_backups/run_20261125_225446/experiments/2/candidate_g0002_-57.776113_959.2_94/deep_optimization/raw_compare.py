"""Compare every raw output against the immutable handoff on the configured stimulus."""
import sys
from pathlib import Path
import numpy as np
root=Path('/home/guoliang/multiplier')
sys.path.insert(0,str(root.parent))
sys.path.insert(0,str(root.parent/'open_question_solver'))
import importlib.util

def load(path):
 spec=importlib.util.spec_from_file_location('isolated_candidate',path)
 module=importlib.util.module_from_spec(spec)
 spec.loader.exec_module(module)
 c=module.build_circuit(); c.validate(); return c
samples=np.load(root/'stimulus.npy',allow_pickle=False)
reference=load(root/'experiments/2/candidate_g0002_0002/partial_product_candidate.py')
other=load(Path(sys.argv[1]))
print('samples',len(samples),'cost',reference.gatecost().total,other.gatecost().total,'slots',reference.partial_product_count,other.partial_product_count,flush=True)
for k in range(0,len(samples),4096):
 inputs=[tuple(map(int,row)) for row in samples[k:k+4096]]
 a=reference.simulate_many(inputs); b=other.simulate_many(inputs)
 for i,(x,y) in enumerate(zip(a,b)):
  if x!=y:
   raise AssertionError(f'raw mismatch at {k+i}: {x} != {y}, input {inputs[i]}')
print('all raw outputs identical; empirical comparison, not formal proof')
