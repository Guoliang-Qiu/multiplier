"""Check full-stimulus bitwise raw equality for two complete tap2 circuits."""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, '/home/guoliang/multiplier')
from eval import load_module, load_stimulus
left, right = (load_module(Path(p)) .build_circuit() for p in sys.argv[1:3])
inputs = load_stimulus('/home/guoliang/multiplier/stimulus.npy', num_inputs=4)
unequal = 0
for start in range(0, len(inputs), 4096):
    data = inputs[start:start + 4096].tolist()
    unequal += sum(x != y for x, y in zip(left.simulate_many(data), right.simulate_many(data)))
print('raw_bitwise_unequal', unequal, 'samples', len(inputs), 'costs', left.gatecost().total, right.gatecost().total)
if unequal:
    raise SystemExit(1)
