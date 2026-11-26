"""Inspect actual precompression slots on external workload."""
import importlib.util
from collections import Counter
import numpy as np
from tools.circuit_kit.circuit.simulation import _simulate_packed_values
p='/home/guoliang/multiplier/experiments/1/candidate_g0001_0005/deep_optimization/general_baseline.py'
s=importlib.util.spec_from_file_location('base',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class Inspect(m.Candidate):
    def _compress_columns(self):
        self.orig_cols=[list(x) for x in self._columns]
        super()._compress_columns()
c=Inspect()._build_circuit(); slots=[(col,i,n) for col, ns in enumerate(c.orig_cols) for i,n in enumerate(ns)]
data=np.load('/home/guoliang/multiplier/stimulus.npy',mmap_mode='r')
counts=Counter(); joint=Counter(); targets=[n for col,i,n in slots if col<=7]
for j in range(0,len(data),64):
    vs=_simulate_packed_values(c,data[j:j+64].tolist(),input_width=9)
    for n in set(n for _,_,n in slots):
        counts[n]+=vs[n].bit_count()
    for a in targets:
        for b in targets:
            if a<b: joint[(a,b)]+=(vs[a]&vs[b]).bit_count()
print('cases',len(data),'slots',len(slots))
for col,i,n in slots:
    if col<=9 or counts[n]/len(data)<.12 or counts[n]/len(data)>.88:
        print('slot',col,i,n,c.nodes[n].kind,round(counts[n]/len(data),5))
print('low-column joint correlations:')
for a,b in sorted(joint,key=lambda z:abs(joint[z]/len(data)-counts[z[0]]*counts[z[1]]/len(data)**2),reverse=True)[:22]:
    print(a,b,round(joint[(a,b)]/len(data),5),round(counts[a]/len(data),5),round(counts[b]/len(data),5))
