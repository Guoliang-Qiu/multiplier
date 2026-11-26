"""Check full-stimulus raw outputs for equivalent gate-level candidate rewrites."""
import importlib.util
import numpy as np
from pathlib import Path
root=Path('/home/guoliang/multiplier')

def load(path):
    spec=importlib.util.spec_from_file_location('trial_check',path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.build_circuit()

stim=np.load(root/'stimulus.npy')
print('stimulus:', stim.shape, flush=True)
reference=load(root/'generations/1/candidate_g0001_-57.944563_1015.6_93.py')
optimized=load(root/'experiments/1/candidate_g0001_0007/deliver_trial.py')
count=0
for offset in range(0,len(stim),4096):
    x=[tuple(map(int,row)) for row in stim[offset:offset+4096]]
    ref=reference.simulate_many(x)
    got=optimized.simulate_many(x)
    count+=sum(a!=b for a,b in zip(ref,got))
print('raw_output_mismatches:',count,'total:',len(stim),flush=True)
