"""Compare original exported and readable simplified circuit on external stimulus."""
import importlib.util
import json
from pathlib import Path
import numpy as np
from tools.circuit_kit.circuit.multiplier.conditional_compensation.node_set_information import _sample_values
root = Path('/home/guoliang/multiplier/experiments/5/candidate_g0005_0002/three_simple')
raws = []
for name, path in [('original', root / 'exported_original.py'), ('clean', root / 'compensated.py')]:
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    circuit = module.build_circuit()
    circuit.validate()
    samples = np.load('/home/guoliang/multiplier/stimulus.npy', allow_pickle=False)
    raw, _ = _sample_values(circuit, samples, [])
    raws.append(raw)
    print(name, circuit.gatecost().total, circuit.partial_product_count, flush=True)
print('raw_equal_count', int(np.count_nonzero(raws[0] == raws[1])), 'total', len(raws[0]))
assert np.array_equal(*raws)
