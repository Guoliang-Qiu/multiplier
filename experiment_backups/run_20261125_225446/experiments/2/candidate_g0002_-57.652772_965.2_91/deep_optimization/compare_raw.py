"""Compare complete-circuit signed raw outputs on the prescribed stimulus."""
import importlib.util
import sys
import numpy as np
from pathlib import Path
sys.path.insert(0, '/home/guoliang/open_question_solver')
root = Path('/home/guoliang/multiplier')
def build(path):
    spec = importlib.util.spec_from_file_location('raw_test',path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    circuit=mod.build_circuit()
    circuit.validate()
    return circuit
samples=np.load(root/'stimulus.npy',allow_pickle=False)
inputs=[tuple(map(int,row)) for row in samples]
base=build(root/'experiments/2/candidate_g0002_0007/partial_product_candidate.py')
raw_base=np.asarray(base.simulate_many(inputs),dtype=np.int32)
for name in sys.argv[1:]:
    candidate=build(root/'experiments/2/candidate_g0002_0007/deep_optimization'/f'{name}.py')
    raw=np.asarray(candidate.simulate_many(inputs),dtype=np.int32)
    print(name,'raw_bitwise_mismatches',np.count_nonzero(raw_base!=raw),'cost',candidate.gatecost().total,'slots',candidate.partial_product_count,flush=True)
