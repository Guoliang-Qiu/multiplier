"""Inspect actual pre-compression node probabilities on external stimulus."""
import importlib.util
from collections import Counter
import numpy as np
from tools.circuit_kit.circuit.simulation import _simulate_packed_values
p='experiments/1/candidate_g0001_0004/deep_optimization/equivalent_baseline.py'
s=importlib.util.spec_from_file_location('candidate_stats',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class Inspect(m.Candidate):
    def _compress_columns(self):
        self.before = [list(col) for col in self._columns]
        super()._compress_columns()
c=Inspect()._build_circuit()
x=np.load('stimulus.npy',allow_pickle=False)[::10].tolist()
counts=Counter()
for start in range(0,len(x),64):
    chunk=x[start:start+64]
    values=_simulate_packed_values(c,chunk,input_width=9)
    for col in range(3,9):
        for i,node in enumerate(c.before[col]):
            counts[col,i]+=int(values[node]).bit_count()
for col in range(3,9):
    print('column',col,[(i,n,round(counts[col,i]/len(x),5),c.nodes[n].kind) for i,n in enumerate(c.before[col])])
