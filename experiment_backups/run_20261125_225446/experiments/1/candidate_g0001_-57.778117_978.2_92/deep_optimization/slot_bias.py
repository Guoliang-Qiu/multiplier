"""Measure actual precompression column-slot probabilities on external stimulus."""
import sys,pathlib,importlib.util,numpy as np
ROOT=pathlib.Path('/home/guoliang/multiplier');sys.path.insert(0,str(ROOT.parent/'open_question_solver'))
from tools.circuit_kit.circuit.simulation import _simulate_packed_values
p=ROOT/'experiments/1/candidate_g0001_0003/deep_optimization/general_baseline.py'
spec=importlib.util.spec_from_file_location('baseline',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Observe(m.Candidate):
    def _compress_columns(self):
        self.slots=[list(col) for col in self._columns]
        super()._compress_columns()
c=Observe()._build_circuit(); data=np.load(ROOT/'stimulus.npy',allow_pickle=False); slots=[(col,i,n) for col,bucket in enumerate(c.slots) for i,n in enumerate(bucket)]; count=np.zeros(len(slots),dtype=np.int64)
for start in range(0,len(data),64):
    values=_simulate_packed_values(c,data[start:start+64].tolist(),input_width=9)
    count += [values[n].bit_count() for _,_,n in slots]
for (col,index,n),cnt in zip(slots,count):
    print(col,index,n,round(cnt/len(data),6),round((1-cnt/len(data))*2**col,2),sep='\t')
