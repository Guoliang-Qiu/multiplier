import importlib.util, numpy as np
from tools.circuit_kit.circuit.simulation import _simulate_packed_values
p='/home/guoliang/multiplier/experiments/2/candidate_g0002_0004/deep_optimization/general.py'
s=importlib.util.spec_from_file_location('base',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
c=m.Candidate(); a,b,d,e,z,o=c.setup(); cols=c._product_columns(a,b,d,e,z,o)
samples=np.load('/home/guoliang/multiplier/stimulus.npy', mmap_mode='r')
ids=sorted(set(n for col in cols for n in col))
ones={n:0 for n in ids}; joint={(x,y):0 for col in cols[:8] for x in col for y in col if x<y}
for start in range(0,len(samples),64):
 block=samples[start:start+64].tolist();values=_simulate_packed_values(c,block,input_width=9)
 for n in ids:ones[n]+=values[n].bit_count()
 for x,y in joint:joint[x,y]+=(values[x]&values[y]).bit_count()
N=len(samples)
for col in range(2,11):
 print('column',col,'weight',1<<col,'slots',len(cols[col]))
 for n in cols[col]:print(' ',n,c.nodes[n].kind,'p1',round(ones[n]/N,5),'cone',c.nodes[n].inputs)
for col in range(2,7):
 print('correlations column',col)
 for x in cols[col]:
  for y in cols[col]:
   if x>=y or (x,y) not in joint:continue
   p=joint[x,y]/N;print(x,y,'joint',round(p,4),'xor',round((ones[x]+ones[y])/N-2*p,4))
