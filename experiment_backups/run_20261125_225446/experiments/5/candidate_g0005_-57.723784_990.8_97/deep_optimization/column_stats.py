"""Screen column slot removals against the required external stimulus.

This is analysis only; full evaluator validates selected circuits.
"""
import importlib.util
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0,'/home/guoliang/open_question_solver')
p=Path('/home/guoliang/multiplier/experiments/5/candidate_g0005_0003/deep_optimization')
spec=importlib.util.spec_from_file_location('baseline',p/'general_baseline.py'); m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
c=m.Candidate();a,b,d,e,z,o=c.setup(); cols=c._product_columns(a,b,d,e,z,o)
samples=np.load('/home/guoliang/multiplier/stimulus.npy',mmap_mode='r')
from tools.circuit_kit.circuit.simulation import _simulate_packed_values
slots=[(col,k,node) for col,row in enumerate(cols) for k,node in enumerate(row) if 3<=col<=11 and node not in (z,o)]
ref=(samples[:,0]*samples[:,1]+samples[:,2]*samples[:,3]).astype(np.float64)/128
results=[]
# Compare the rounded-value residual against base exact-raw output separately;
# these are first-order errors and are NOT a complete-circuit model.
for start in range(0,len(samples),64):
    chunk=samples[start:start+64].tolist()
    vals=_simulate_packed_values(c,chunk,input_width=9)
    v=np.array([[((vals[node]>>j)&1) for _,_,node in slots] for j in range(len(chunk))],dtype=np.int16)
    if start==0: counts=v.sum(axis=0).astype(np.int64)
    else: counts+=v.sum(axis=0)
for index,(col,k,node) in enumerate(slots):
    results.append((col,k,node,round(float(counts[index]/len(samples)),5)))
print('slot one-frequencies by column')
for row in results:print(*row)
print('reference raw rounding ties',int(np.count_nonzero(((samples[:,0]*samples[:,1]+samples[:,2]*samples[:,3])%128)==64)))
