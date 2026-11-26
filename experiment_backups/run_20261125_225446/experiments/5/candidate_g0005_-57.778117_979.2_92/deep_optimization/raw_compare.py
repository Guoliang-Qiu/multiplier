"""Empirical raw-bit equivalence using the configured external stimulus."""
import importlib.util,sys,numpy as np
from tools.circuit_kit.circuit.multiplier.conditional_compensation.node_set_information import _sample_values
samples=np.load('/home/guoliang/multiplier/stimulus.npy',allow_pickle=False)
raw=[]
for index,path in enumerate(sys.argv[1:]):
 spec=importlib.util.spec_from_file_location('candidate_'+str(index),path)
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 circuit=module.build_circuit();circuit.validate()
 values,_=_sample_values(circuit,samples,[])
 raw.append(values)
 print(path,'cost',circuit.gatecost().total,'slots',circuit.partial_product_count,'raw',len(values),flush=True)
 if index: print('raw_mismatches',int(np.count_nonzero(raw[0]!=values)),flush=True)
