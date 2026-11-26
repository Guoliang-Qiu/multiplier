"""Compare raw bus values over the configured external workload."""
import importlib.util
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, '/home/guoliang/open_question_solver')
root = Path('/home/guoliang/multiplier')
files = [root / p for p in sys.argv[1:]]
stimulus = np.load(root / 'stimulus.npy', allow_pickle=False)
inputs = list(map(tuple, stimulus.tolist()))
def load(p):
    spec = importlib.util.spec_from_file_location('raw_comparison_' + str(len(p.name)) + p.stem, p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.build_circuit()
a = load(files[0]).simulate_many(inputs)
for p in files[1:]:
    b = load(p).simulate_many(inputs)
    mismatch = sum(x != y for x, y in zip(a, b))
    print(str(p), 'raw_mismatch', mismatch, 'samples', len(a), flush=True)
