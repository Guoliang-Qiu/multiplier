"""Check complete stimulus raw output equality for parent and selected child."""
import importlib.util
from pathlib import Path
import numpy as np
from eval import load_stimulus
ROOT = Path('/home/guoliang/multiplier')
paths = [ROOT/'generations/4/candidate_g0004_-57.827429_1003.8_97.py', ROOT/'generations/4/candidate_g0004_0010.py']
def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj.build_circuit()
samples = load_stimulus(ROOT/'stimulus.npy',num_inputs=4)
left, right = [load(p, 'test'+str(i)) for i,p in enumerate(paths)]
a = left.simulate_many(samples.tolist())
b = right.simulate_many(samples.tolist())
print({'total':len(a), 'raw_mismatches':sum(x!=y for x,y in zip(a,b)), 'costs':(left.gatecost().total,right.gatecost().total), 'slots':(left.partial_product_count,right.partial_product_count)})
