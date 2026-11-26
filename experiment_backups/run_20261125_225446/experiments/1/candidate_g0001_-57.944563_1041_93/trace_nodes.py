import importlib.util
p='/home/guoliang/multiplier/experiments/1/candidate_g0001_0007/trial_b.py'
s=importlib.util.spec_from_file_location('candidate',p); m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
x=m.Candidate(); a,b,c,d,z,o=x.setup(); cols=x._product_columns_before_compensation(a,b,c,d,z,o)
for i in [91,420,421,425]:
 n=x.nodes[i];print(i,n.kind,n.inputs)
for j in [2,3,4]:
 print('COLUMN',j,[(i,x.nodes[i].kind,x.nodes[i].inputs) for i in cols[j]])
print('node count',len(x.nodes))
