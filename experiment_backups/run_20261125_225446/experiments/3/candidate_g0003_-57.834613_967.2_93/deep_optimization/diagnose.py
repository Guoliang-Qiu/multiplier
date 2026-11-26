"""Offline configured-stimulus conditional error diagnosis; not part of candidate."""
import importlib.util
import numpy as np
from pathlib import Path
root = Path('/home/guoliang/multiplier')
p = root / 'experiments/3/candidate_g0003_0007/deep_optimization/general_equivalence_baseline.py'
spec = importlib.util.spec_from_file_location('diagnosed_candidate', p)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
samples = np.load(root / 'stimulus.npy').astype(np.int64)
a,b,c,d = samples.T
raw = np.asarray(module.build_circuit().simulate_many(samples.tolist()), dtype=np.int64)
reference = a*b + c*d
error = raw-reference
print('samples', len(samples), 'raw-reference mean', error.mean(), 'std', error.std())
for label, mask in [('b>=0,d>=0',(b>=0)&(d>=0)), ('b<0,d>=0',(b<0)&(d>=0)), ('b>=0,d<0',(b>=0)&(d<0)), ('b<0,d<0',(b<0)&(d<0)), ('product_cancel',(a*b)*(c*d)<0),('product_reinforce',(a*b)*(c*d)>0), ('raw_round_near', ((raw&127)>=56)&((raw&127)<=72))]:
    z=error[mask]
    print(label,'n',len(z),'bias_raw',z.mean(),'mae_raw',np.abs(z).mean(),'rmse_raw',np.sqrt(np.mean(z.astype(float)**2)))
for k in range(4,8):
    z=error[((b>>k)&1).astype(bool)]
    print('b bit',k,'n',len(z),'bias_raw',z.mean())
