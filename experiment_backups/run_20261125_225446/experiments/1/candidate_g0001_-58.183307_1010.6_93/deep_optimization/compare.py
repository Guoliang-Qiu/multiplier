"""Check raw output equivalence on the configured external evaluation stimulus."""
import importlib.util,sys,numpy as np
from pathlib import Path
base=Path('/home/guoliang/multiplier/experiments/1/candidate_g0001_0000')
paths=[base/'partial_product_candidate.py']+[Path(x) for x in sys.argv[1:]]
samples=np.load('/home/guoliang/multiplier/stimulus.npy',mmap_mode='r')
def load(path):
 spec=importlib.util.spec_from_file_location('comparison_'+path.stem,path)
 m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 return m.build_circuit()
ref=load(paths[0]); candidates=[load(p) for p in paths[1:]]
for p,c in zip(paths[1:],candidates): print('COST',p.name,c.gatecost().total,'PP',c.partial_product_count,flush=True)
errors=[0]*len(candidates); checked=0
for start in range(0,len(samples),4096):
 chunk=[tuple(map(int,row)) for row in samples[start:start+4096]]
 r=ref.simulate_many(chunk)
 for i,c in enumerate(candidates):
  v=c.simulate_many(chunk)
  errors[i]+=sum(a!=b for a,b in zip(r,v))
 checked+=len(chunk)
print('RAW_COMPARISON',checked,dict(zip([p.name for p in paths[1:]],errors)),flush=True)
