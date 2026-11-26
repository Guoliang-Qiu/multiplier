import importlib.util
import numpy as np
from pathlib import Path
p=Path(__file__).with_name('general_baseline.py')
spec=importlib.util.spec_from_file_location('baseline',p);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
class Probe(mod.Candidate):
    def _compress_columns(self):
        self.before=[list(x) for x in self._columns]
        super()._compress_columns()
c=Probe()._build_circuit()
s=np.load('/home/guoliang/multiplier/stimulus.npy',mmap_mode='r')[::16].astype(np.int16)
n=len(s); v=[]; cursor={'IN_A':0,'IN_B':0,'IN_C':0,'IN_D':0}; bus={'IN_A':0,'IN_B':1,'IN_C':2,'IN_D':3}
for node in c.nodes:
    kind=node.kind; ins=node.inputs
    if kind in bus:
        k=cursor[kind]; cursor[kind]+=1; val=((s[:,bus[kind]]>>k)&1).astype(np.uint8)
    elif kind in ('ZERO','ONE'): val=np.full(n,int(kind=='ONE'),dtype=np.uint8)
    elif kind=='NOT':val=1-v[ins[0]]
    elif kind=='AND':val=v[ins[0]]&v[ins[1]]
    elif kind=='OR':val=v[ins[0]]|v[ins[1]]
    elif kind=='XOR':val=v[ins[0]]^v[ins[1]]
    elif kind=='MUX_XOR':
        a,b,d,e,f=ins;val=v[f]^((v[a]&v[b])|(v[d]&v[e]))
    else:raise ValueError(kind)
    v.append(val)
print('samples',n,'precompression slots',sum(map(len,c.before)))
for col,bucket in enumerate(c.before):
    for k,node in enumerate(bucket):
        x=v[node]; prob=float(x.mean());print(col,k,node,round(prob,5),'biased',round(min(prob,1-prob),5))
