"""Check raw signed output equality on the authoritative configured stimulus."""
import importlib.util
from pathlib import Path
import numpy as np

ROOT = Path('/home/guoliang/multiplier')
paths = [ROOT / 'generations/3/candidate_g0003_-57.776113_958.2_93.py',
         ROOT / 'experiments/3/candidate_g0003_0009/optimized.py']

def load(path):
    spec = importlib.util.spec_from_file_location('comparison_candidate', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.build_circuit()

samples = np.load(ROOT / 'stimulus.npy', allow_pickle=False)
left, right = (load(path) for path in paths)
for start in range(0, len(samples), 8192):
    batch = samples[start:start + 8192].tolist()
    if left.simulate_many(batch) != right.simulate_many(batch):
        raise AssertionError(f'raw mismatch in batch beginning {start}')
print('sample raw-output equality:', len(samples), 'vectors')
