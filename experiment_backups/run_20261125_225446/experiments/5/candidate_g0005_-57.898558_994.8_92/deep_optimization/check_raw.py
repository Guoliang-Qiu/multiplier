import importlib.util, sys, numpy as np
sys.path.insert(0, "/home/guoliang/open_question_solver")
def load(path):
    spec=importlib.util.spec_from_file_location("trial_"+str(abs(hash(path))),path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module.build_circuit()
a,b=map(load,sys.argv[1:3]); samples=np.load("/home/guoliang/multiplier/stimulus.npy",mmap_mode="r")
for start in range(0,len(samples),8192):
    inputs=[tuple(map(int,row)) for row in samples[start:start+8192]]
    x,y=a.simulate_many(inputs),b.simulate_many(inputs)
    if x!=y:
        i=next(i for i,(u,v) in enumerate(zip(x,y)) if u!=v)
        print("DIFF",start+i,inputs[i],x[i],y[i]);sys.exit(1)
print("EMPIRICAL RAW EQUIVALENCE",len(samples),"slots",a.partial_product_count,b.partial_product_count,"cost",a.gatecost().total,b.gatecost().total)
