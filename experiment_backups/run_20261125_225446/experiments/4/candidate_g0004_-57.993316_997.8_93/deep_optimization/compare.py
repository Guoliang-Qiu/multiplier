"""Compare signed raw output words on the configured external stimulus."""
import importlib.util
import sys
import numpy as np

def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod.build_circuit()

x = np.load('/home/guoliang/multiplier/stimulus.npy', allow_pickle=False)
ref = load(sys.argv[1], 'reference_candidate')
new = load(sys.argv[2], 'trial_candidate')
mismatches = 0
for start in range(0, len(x), 4096):
    batch = x[start:start+4096].tolist()
    a = ref.simulate_many(batch)
    b = new.simulate_many(batch)
    mismatches += sum(v != w for v, w in zip(a, b))
print('raw_mismatches', mismatches, 'samples', len(x), flush=True)
if mismatches:
    sys.exit(1)
