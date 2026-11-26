"""Compare signed raw output across the required external stimulus."""
import importlib.util
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, '/home/guoliang/open_question_solver')
root = Path('/home/guoliang/multiplier')
def load(path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    c = m.build_circuit()
    c.validate()
    return c
samples = np.load(root / 'stimulus.npy', mmap_mode='r')
left = load(Path(sys.argv[1]))
right = load(Path(sys.argv[2]))
mismatches = 0
for start in range(0, len(samples), 4096):
    inputs = samples[start:start+4096].tolist()
    x = left.simulate_many(inputs)
    y = right.simulate_many(inputs)
    mismatches += sum(a != b for a, b in zip(x,y))
print('raw_output_mismatches', mismatches, 'cases',len(samples))
if mismatches:
    raise SystemExit(1)
