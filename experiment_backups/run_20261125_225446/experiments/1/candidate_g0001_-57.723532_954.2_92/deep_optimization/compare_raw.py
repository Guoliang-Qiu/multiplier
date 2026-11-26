"""Empirical raw-output comparison on the external configured stimulus."""
import importlib.util
import numpy as np
from pathlib import Path

root = Path('/home/guoliang/multiplier')
samples = np.load(root / 'stimulus.npy', allow_pickle=False)

def load(path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    circuit = mod.build_circuit()
    circuit.validate()
    return circuit

parent = load(root / 'experiments/1/candidate_g0001_0002/partial_product_candidate.py')
baseline = load(root / 'experiments/1/candidate_g0001_0002/deep_optimization/general_baseline.py')
print('parent', parent.gatecost().total, parent.partial_product_count, flush=True)
print('baseline', baseline.gatecost().total, baseline.partial_product_count, flush=True)
changes = 0
for start in range(0, len(samples), 8192):
    inputs = samples[start:start + 8192].tolist()
    x = parent.simulate_many(inputs)
    y = baseline.simulate_many(inputs)
    changes += sum(a != b for a, b in zip(x, y))
print('raw unequal', changes, 'total', len(samples), flush=True)
assert changes == 0
