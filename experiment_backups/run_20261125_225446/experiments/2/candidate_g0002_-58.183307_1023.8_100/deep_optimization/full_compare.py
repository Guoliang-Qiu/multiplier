"""Full external-stimulus raw bitwise comparison, empirical not formal."""
import importlib.util
import sys
import numpy as np
from pathlib import Path
sys.path.insert(0, '/home/guoliang/open_question_solver')
root=Path('/home/guoliang/multiplier')
def build(path):
 spec=importlib.util.spec_from_file_location('check_'+path.stem,path)
 m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 return m.build_circuit()
ref=build(root/'experiments/2/candidate_g0002_0001/partial_product_candidate.py')
gen=build(root/'experiments/2/candidate_g0002_0001/deep_optimization/general_baseline.py')
fin=build(root/'experiments/2/candidate_g0002_0001/deep_optimization/mux_all.py')
rows=np.load(root/'stimulus.npy')
counts=[0,0];total=0
for begin in range(0,len(rows),4096):
 sample=rows[begin:begin+4096].tolist()
 expected=ref.simulate_many(sample)
 for i,c in enumerate((gen,fin)):
  counts[i]+=sum(x!=y for x,y in zip(expected,c.simulate_many(sample)))
 total+=len(sample)
print('full_stimulus_rows',total,'general_raw_mismatches',counts[0],'directional_raw_mismatches',counts[1],flush=True)
assert counts==[0,0]
