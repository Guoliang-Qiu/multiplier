"""Screen column-local carry-only compressor trials on the external stimulus."""
from pathlib import Path
import importlib.util, json, sys
import numpy as np
sys.path.insert(0, '/home/guoliang/open_question_solver')
root = Path(__file__).resolve().parent
src = (root/'general_baseline.py').read_text()
samples = np.load('/home/guoliang/multiplier/stimulus.npy',allow_pickle=False)
subset = samples[::32].tolist()
ref = samples[::32]
true = (ref[:,0]*ref[:,1] + ref[:,2]*ref[:,3])/128
norm = np.linalg.norm(true)
for col in range(4,18):
 s=src.replace('MAJ_COLS = (0, 1, 2, 3)','MAJ_COLS = (0, 1, 2, 3, '+str(col)+')')
 f=root/f'maj_{col}.py';f.write_text(s)
 spec=importlib.util.spec_from_file_location('trial_'+str(col),f)
 m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 c=m.build_circuit();cost=c.gatecost().total
 if cost >= 959.2: continue
 raw=np.array(c.simulate_many(subset),dtype=np.float64)
 err=true-np.floor(raw/128+0.5)
 evm=20*np.log10(np.linalg.norm(err)/norm)
 print(json.dumps({'col':col,'cost':cost,'slots':c.partial_product_count,'sample_evm':evm}),flush=True)
