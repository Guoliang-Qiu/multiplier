"""Compare complete raw output on the configured external stimulus."""
import importlib.util, pathlib, sys
import numpy as np
ROOT=pathlib.Path('/home/guoliang/multiplier')
sys.path.insert(0,str(ROOT.parent/'open_question_solver'))
paths=sys.argv[1:]
samples=np.load(ROOT/'stimulus.npy',allow_pickle=False)
modules=[]
for i,p in enumerate(paths):
    spec=importlib.util.spec_from_file_location(f'trial_{i}',p)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    modules.append(module.build_circuit())
    modules[-1].validate()
print('costs',[(c.gatecost().total,c.partial_product_count) for c in modules],flush=True)
for start in range(0,len(samples),8192):
    inputs=samples[start:start+8192].tolist()
    values=[c.simulate_many(inputs) for c in modules]
    for j,v in enumerate(values[1:],1):
        if v!=values[0]:
            bad=next(k for k,(a,b) in enumerate(zip(values[0],v)) if a!=b)
            raise AssertionError((start+bad,j,inputs[bad],values[0][bad],v[bad]))
print('RAW EQUAL',len(samples),'cases',flush=True)
