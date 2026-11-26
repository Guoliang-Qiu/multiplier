import importlib.util
from pathlib import Path
p=Path('/home/guoliang/multiplier/experiments/1/candidate_g0001_0001/parent.py')
s=importlib.util.spec_from_file_location('parent',p); m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
x=m.Candidate(); a,b,c,d,z,o=x.setup(); cols=x._product_columns_before_compensation(a,b,c,d,z,o)
for col in range(3,10):
 print('column',col,[(i,n,x.nodes[n].kind,x.nodes[n].inputs) for i,n in enumerate(cols[col])])
print('leaves', {'a':a,'b':b,'c':c,'d':d,'zero':z,'one':o})
for i in range(38,min(150,len(x.nodes))):
 n=x.nodes[i];print(i,n.kind,n.inputs)
