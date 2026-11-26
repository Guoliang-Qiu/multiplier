"""Empirical full-stimulus raw-output equality using evaluator's stimulus file."""
import importlib.util
import sys
import numpy as np
sys.path.insert(0, '/home/guoliang/open_question_solver')

def load(path):
    spec = importlib.util.spec_from_file_location('candidate_trial', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.build_circuit()

samples = np.load('/home/guoliang/multiplier/stimulus.npy', allow_pickle=False)
a = load(sys.argv[1]); b = load(sys.argv[2]); count = 0; first = None
for i in range(0, len(samples), 8192):
    x = samples[i:i+8192].tolist()
    y1, y2 = a.simulate_many(x), b.simulate_many(x)
    for j, (v1, v2) in enumerate(zip(y1,y2)):
        if v1 != v2:
            count += 1
            if first is None: first = (i+j, x[j], v1, v2)
print('raw_mismatches', count, 'total',len(samples),'first',first)
if count: sys.exit(1)
