"""Compare full raw 19-bit outputs on the external evaluator stimulus."""
import importlib.util
import sys
import numpy as np

sys.path.insert(0, '/home/guoliang/open_question_solver')

def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    circuit = module.build_circuit()
    circuit.validate()
    return circuit

samples = np.load('/home/guoliang/multiplier/stimulus.npy', allow_pickle=False)
inputs = [tuple(map(int, row)) for row in samples]
a = load(sys.argv[1], 'first')
b = load(sys.argv[2], 'second')
x = a.simulate_many(inputs)
y = b.simulate_many(inputs)
print('raw_sample_count', len(x), 'raw_mismatches', sum(i != j for i, j in zip(x, y)), flush=True)
if x != y:
    raise SystemExit(1)
