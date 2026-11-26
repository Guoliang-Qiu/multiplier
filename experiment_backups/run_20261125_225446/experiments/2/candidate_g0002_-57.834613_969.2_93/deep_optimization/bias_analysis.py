"""Measure precompression column probabilities on the configured stimulus."""
import importlib.util
import numpy as np
from pathlib import Path
from tools.circuit_kit.circuit.simulation import _simulate_packed_values
p=Path(__file__).resolve().parent / 'general_baseline.py'
spec=importlib.util.spec_from_file_location('biased',p)
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
original=mod.Candidate._compress_columns
def capture(self):
    self.original_columns=[list(x) for x in self._columns]
    return original(self)
mod.Candidate._compress_columns=capture
obj=mod.Candidate()._build_circuit()
stim=np.load('/home/guoliang/multiplier/stimulus.npy')
measure=np.zeros((19, 20),dtype=np.int64)
N=16384
for k in range(0,N,64):
    values=_simulate_packed_values(obj,stim[k:k+64].tolist(),input_width=9)
    for col, nodes in enumerate(obj.original_columns):
        for j, node in enumerate(nodes):
            measure[col,j]+=int(values[node]).bit_count()
print('sample_count',N)
for col, row in enumerate(obj.original_columns):
    if row:
        print(col,' '.join(f'{j}:{measure[col,j]/N:.4f}' for j in range(len(row))))
