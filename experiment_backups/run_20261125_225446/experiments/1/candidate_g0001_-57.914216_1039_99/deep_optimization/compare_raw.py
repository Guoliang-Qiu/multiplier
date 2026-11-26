"""Check bitwise output equivalence on configured external stimulus."""
import importlib.util, sys
import numpy as np
from tools.circuit_kit.circuit.multiplier.tap2_9bit_multiplier import Circuit
from tools.circuit_kit.circuit.simulation import _simulate_packed_values

def build(path):
    spec = importlib.util.spec_from_file_location('compared',path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.build_circuit()

ref, cand = [build(p) for p in sys.argv[1:3]]
inputs = np.load('/home/guoliang/multiplier/stimulus.npy', mmap_mode='r')
errors = 0
for i in range(0,len(inputs),64):
    chunk = inputs[i:i+64].tolist()
    a = _simulate_packed_values(ref,chunk,input_width=9)
    b = _simulate_packed_values(cand,chunk,input_width=9)
    for k in range(19):
        errors += (a[ref.output_ids[k]] ^ b[cand.output_ids[k]]).bit_count()
print({'cases':len(inputs),'output_bit_mismatches':errors,'reference_cost':ref.gatecost().total,'candidate_cost':cand.gatecost().total,'reference_slots':ref.partial_product_count,'candidate_slots':cand.partial_product_count})
