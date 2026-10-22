"""Joint distribution search around the 1037 candidate."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import itertools, numpy as np
from multiplier.initial_solutions import candidate_g0001_0000 as base
from multiplier.tools.search_existing_subcones import simulate

class Probe(base.Candidate):
    changes=()
    def _product_columns(self,q,m,z,o,cut):
        cols=super()._product_columns(q,m,z,o,cut); side=1 if q[0]==self.input_ids[9] else 2
        for col,pos,path,mask in self.changes:
            if mask&side:
                n=cols[col][pos]
                if path=='zero':n=z
                elif path=='one':n=o
                else:
                    for p in path:n=self.nodes[n].inputs[int(p)]
                cols[col][pos]=n
        return cols

def main():
 x=np.random.default_rng(41037).integers(-256,256,(4,8192),dtype=np.int64);ref=(x[0]*x[1]+x[2]*x[3])/128;p=np.mean(ref**2)
 def score(c):
  y=simulate(c,x);return float(10*np.log10(np.mean((np.floor(y/128+.5)-ref)**2)/p))
 print('base',score(base.build_circuit()),flush=True)
 _,cols=base.build_partial_product_layout(); opts=[]
 for col in range(4,7):
  for pos in range(len(cols[col])//2):
   n=cols[col][pos]; paths=['zero','one','0','1']
   for pth in ('0','1'):
    child=base.build_partial_product_layout()[0].nodes[n].inputs[int(pth)]
    paths += [pth+str(i) for i in range(len(base.build_partial_product_layout()[0].nodes[child].inputs))]
   for path in paths:
    for mask in (1,2,3):opts.append((col,pos,path,mask))
 rows=[]
 for a,b in itertools.combinations(opts,2):
  if a[:2]==b[:2]:continue
  q=Probe();q.changes=(a,b);c=q._build_circuit();cost=c.gatecost().total
  if cost>1018:continue
  ev=score(c)
  if ev < -57.9:rows.append((cost,ev,a,b))
 for r in sorted(rows,key=lambda z:(z[0],z[1]))[:40]:print(r,flush=True)

if __name__=='__main__':main()
