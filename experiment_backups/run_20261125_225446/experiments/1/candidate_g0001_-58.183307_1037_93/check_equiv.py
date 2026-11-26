"""Sample-based raw-output equivalence check on required external stimulus."""
import importlib.util
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, '/home/guoliang/open_question_solver')
p = Path('/home/guoliang/multiplier')
def build(path):
    spec = importlib.util.spec_from_file_location('sample_candidate', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.build_circuit()
a = build(p/'generations/1/candidate_g0001_-58.183307_1010.6_93.py')
b = build(p/'experiments/1/candidate_g0001_0006/shared_row.py')
x = np.load(p/'stimulus.npy', allow_pickle=False)
for start in range(0,len(x),4096):
    samples=x[start:start+4096].tolist()
    aa=a.simulate_many(samples); bb=b.simulate_many(samples)
    for offset,(v,w) in enumerate(zip(aa,bb)):
        if v!=w:
            raise AssertionError((start+offset,v,w))
print('raw outputs equal on',len(x),'external stimulus inputs; sample-based, not formal')
