"""Compare sample-based raw output and weighted cost using the required workload."""
import importlib.util
import json
import sys
import numpy as np
sys.path.insert(0, '/home/guoliang/open_question_solver')

def load(path):
    spec = importlib.util.spec_from_file_location('candidate_' + str(abs(hash(path))), path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    circ = mod.build_circuit()
    circ.validate()
    return circ

if __name__ == '__main__':
    lhs, rhs = (load(x) for x in sys.argv[1:3])
    data = np.load('/home/guoliang/multiplier/stimulus.npy', mmap_mode='r')
    n = int(sys.argv[3]) if len(sys.argv) > 3 else len(data)
    different = 0
    for i in range(0, n, 1024):
        rows = data[i:min(n, i + 1024)].tolist()
        different += sum(x != y for x, y in zip(lhs.simulate_many(rows), rhs.simulate_many(rows)))
    print(json.dumps({'samples': n, 'different_raw_outputs': different,
                      'left_cost': lhs.gatecost().total, 'right_cost': rhs.gatecost().total,
                      'left_slots': lhs.partial_product_count, 'right_slots': rhs.partial_product_count}))
