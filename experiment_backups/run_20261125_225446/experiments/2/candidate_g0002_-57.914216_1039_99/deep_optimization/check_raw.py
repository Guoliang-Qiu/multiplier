import importlib.util, numpy as np, sys
from tools.circuit_kit.circuit.multiplier.tap2_9bit_multiplier import Circuit
files=sys.argv[1:]
circuits=[]
for j,f in enumerate(files):
 s=importlib.util.spec_from_file_location('candidate'+str(j),f);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
 circuits.append(m.build_circuit())
samples=np.load('/home/guoliang/multiplier/stimulus.npy',mmap_mode='r')
for start in range(0,len(samples),4096):
 inputs=samples[start:start+4096].tolist()
 base=circuits[0].simulate_many(inputs)
 for f,c in zip(files[1:],circuits[1:]):
  new=c.simulate_many(inputs)
  for k,(x,y) in enumerate(zip(base,new)):
   if x!=y: raise AssertionError((start+k,inputs[k],x,y,f))
print('RAW EQUALITY',len(samples),'samples',files)
