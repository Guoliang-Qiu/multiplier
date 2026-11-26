"""Local diagnostic measurements, never a delivery dependency."""
import importlib.util
import json
import sys
from pathlib import Path
import numpy as np
ROOT = Path('/home/guoliang/multiplier')
sys.path.insert(0, '/home/guoliang/open_question_solver')
def load(path):
    spec = importlib.util.spec_from_file_location('trial_' + path.stem, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    circuit = mod.build_circuit()
    circuit.validate()
    return circuit
base = load(ROOT / 'experiments/2/candidate_g0002_0001/partial_product_candidate.py')
rows = np.load(ROOT / 'stimulus.npy')
subset = rows[::113].tolist()
ref = base.simulate_many(subset)
for name in sys.argv[1:]:
    path = Path(name)
    try:
        c = load(path)
        got = c.simulate_many(subset)
        diff = sum(x != y for x,y in zip(ref, got))
        print(json.dumps({'file':path.name, 'cost':c.gatecost().total, 'count':c.partial_product_count,'sample_raw_mismatch':diff,'gates':c.gatecost().counts}), flush=True)
    except Exception as exc:
        print(name, type(exc).__name__, str(exc),flush=True)
