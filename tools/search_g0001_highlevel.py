"""Distribution screen of high-level g0001_0005 CPA cones."""
from multiplier.initial_solutions import candidate_g0001_0005 as base
import numpy as np


def main():
 c=base.build_circuit(); rng=np.random.default_rng(2026); x=rng.integers(-256,256,(65536,4),dtype=np.int64)
 raw=np.asarray(c.simulate_many(x.tolist()),dtype=np.int64); ref=(x[:,0]*x[:,1]+x[:,2]*x[:,3])/128
 q=lambda z:np.floor(z/128+.5)
 baseline=float(np.mean((q(raw)-ref)**2));print('baseline',baseline)
 for k in range(6,18):
  bit=(raw>>k)&1; candidates=[('zero',np.zeros_like(bit)),('one',np.ones_like(bit)),('not',1-bit)]
  for name,v in candidates:
   delta=(v-bit)*(1<<k); mse=float(np.mean((q(raw+delta)-ref)**2))
   print(k,name,mse,mse/baseline)


if __name__=='__main__':main()
