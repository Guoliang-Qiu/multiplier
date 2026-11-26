"""Report complete parent/deletion costs for selected original slots."""
from importlib.util import spec_from_file_location,module_from_spec
from tools.circuit_kit.circuit.multiplier.conditional_compensation.node_set_information import build_experiment
p='/home/guoliang/multiplier/experiments/3/candidate_g0003_0001/parent.py'
s=spec_from_file_location('parent_probe',p);m=module_from_spec(s);s.loader.exec_module(m)
for slots in ([[4,0]],[[4,1]],[[4,2]],[[4,3]],[[4,4]],[[4,5]],[[4,6]],[[5,0]],[[5,3]],[[4,0],[5,0]]):
 a,b,layout,n=build_experiment(m.Candidate,slots)
 print(slots,a.gatecost().total,b.gatecost().total,a.gatecost().total-b.gatecost().total,flush=True)
