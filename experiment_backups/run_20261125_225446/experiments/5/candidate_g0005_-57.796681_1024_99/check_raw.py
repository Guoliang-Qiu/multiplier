"""Check sample-based raw bit equality of Boolean rewrites."""
import importlib.util
import numpy as np
from pathlib import Path
p = Path('/home/guoliang/multiplier/experiments/5/candidate_g0005_0009')
xs = np.load('/home/guoliang/multiplier/stimulus.npy', allow_pickle=False)
def circuit(path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.build_circuit()
base = circuit(p/'trial_a.py')
raw = base.simulate_many(xs.tolist())
for name in ('trial_fused', 'trial_rows_a', 'trial_fa', 'trial_k2'):
    cand = circuit(p/f'{name}.py')
    other = cand.simulate_many(xs.tolist())
    print(name, 'raw_equal', raw == other, 'differences', sum(x != y for x,y in zip(raw,other)),
          'cost', cand.gatecost().total, 'pp', cand.partial_product_count, flush=True)
