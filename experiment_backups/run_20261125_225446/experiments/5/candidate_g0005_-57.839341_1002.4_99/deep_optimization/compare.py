"""Compare circuit raw outputs on the prescribed external stimulus (no synthetic inputs)."""
import importlib.util
import sys
import numpy as np

def build(path):
    spec = importlib.util.spec_from_file_location('candidate_' + str(len(path)), path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    circuit = mod.build_circuit()
    circuit.validate()
    return circuit

x, y = map(build, sys.argv[1:3])
samples = np.load('/home/guoliang/multiplier/stimulus.npy', mmap_mode='r')
n = int(sys.argv[3]) if len(sys.argv) > 3 else len(samples)
for start in range(0, n, 8192):
    data = samples[start:min(start + 8192, n)].tolist()
    a = x.simulate_many(data)
    b = y.simulate_many(data)
    if a != b:
        bad = next(i for i, (v, w) in enumerate(zip(a, b)) if v != w)
        print('MISMATCH', start + bad, data[bad], a[bad], b[bad]); sys.exit(1)
print('RAW EQUAL', n)
