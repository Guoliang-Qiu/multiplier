"""Compare full-stimulus raw output equality for two candidate paths."""
import importlib.util
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, '/home/guoliang/open_question_solver')

def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.build_circuit()

left, right = (load(Path(p), f'candidate_{i}') for i, p in enumerate(sys.argv[1:3]))
samples = np.load('/home/guoliang/multiplier/stimulus.npy', allow_pickle=False)
a = left.simulate_many(samples.tolist())
b = right.simulate_many(samples.tolist())
print({'samples':len(samples), 'raw_mismatches':sum(x != y for x,y in zip(a,b)), 'same_graph': left.nodes == right.nodes, 'cost_left':left.gatecost().total, 'cost_right':right.gatecost().total, 'slots_left':left.partial_product_count, 'slots_right':right.partial_product_count})
