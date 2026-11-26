"""Check bitwise outputs on the prescribed external stimulus."""
import importlib.util
import sys
from pathlib import Path
import numpy as np
root=Path('/home/guoliang/multiplier')
samples=np.load(root/'stimulus.npy',allow_pickle=False)
def load(path):
 spec=importlib.util.spec_from_file_location('isolated_trial',path)
 mod=importlib.util.module_from_spec(spec)
 sys.modules[spec.name]=mod
 spec.loader.exec_module(mod)
 circuit=mod.build_circuit();circuit.validate()
 return circuit
first=load(Path(sys.argv[1]));second=load(Path(sys.argv[2]))
print('costs',first.gatecost().total,second.gatecost().total,'slots',first.partial_product_count,second.partial_product_count,flush=True)
raw1=np.asarray(first.simulate_many(samples.tolist()),dtype=np.int64)
raw2=np.asarray(second.simulate_many(samples.tolist()),dtype=np.int64)
delta=raw2-raw1
print('raw_mismatches',np.count_nonzero(delta),'maximum_raw_difference',np.max(np.abs(delta)),flush=True)
