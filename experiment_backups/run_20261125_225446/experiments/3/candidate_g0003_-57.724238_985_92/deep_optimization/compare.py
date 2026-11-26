import importlib.util
import json
import sys
import numpy as np
sys.path.insert(0,'/home/guoliang/open_question_solver')
from pathlib import Path
root=Path('/home/guoliang/multiplier')
samples=np.load(root/'stimulus.npy',allow_pickle=False)
inputs=list(map(tuple,samples.tolist()))
def load(path):
 spec=importlib.util.spec_from_file_location('cand_'+path.stem,path)
 mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 c=mod.build_circuit();c.validate();return c
ref=load(root/'experiments/3/candidate_g0003_0000/partial_product_candidate.py')
ref_raw=np.asarray(ref.simulate_many(inputs),dtype=np.int32)
for name in sys.argv[1:]:
 p=root/'experiments/3/candidate_g0003_0000/deep_optimization'/f'{name}.py'
 c=load(p);raw=np.asarray(c.simulate_many(inputs),dtype=np.int32)
 print(json.dumps({'name':name,'mismatches':int(np.count_nonzero(ref_raw!=raw)),'gate_cost':c.gatecost().total,'partial_product_count':c.partial_product_count}),flush=True)
