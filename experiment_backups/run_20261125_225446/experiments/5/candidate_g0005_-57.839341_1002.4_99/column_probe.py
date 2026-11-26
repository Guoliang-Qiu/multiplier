"""Inspect pre-compression slots, node cones and marginal reachability savings."""
import importlib.util, json
from pathlib import Path
p=Path('/home/guoliang/multiplier/experiments/5/candidate_g0005_0001/parent.py')
s=importlib.util.spec_from_file_location('parent',p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m)
c=m.Candidate(); a,b,d,e,z,o=c.setup(); cols=c._product_columns(a,b,d,e,z,o)
def desc(i):
 n=c.nodes[i]; return {'id':i,'kind':n.kind,'inputs':list(n.inputs)}
report={'columns':{str(k):[{'position':j,**desc(v)} for j,v in enumerate(col)] for k,col in enumerate(cols)},'inputs':{'a':a,'b':b,'c':d,'d':e}, 'zero':z,'one':o,'node_count':len(c.nodes)}
Path('/home/guoliang/multiplier/experiments/5/candidate_g0005_0001/columns.json').write_text(json.dumps(report,indent=2)+'\n')
for k in range(2,9):
 print('COLUMN',k,[(j,v,c.nodes[v].kind,list(c.nodes[v].inputs)) for j,v in enumerate(cols[k])])
print('INPUTS',report['inputs'],'NODES',len(c.nodes))
