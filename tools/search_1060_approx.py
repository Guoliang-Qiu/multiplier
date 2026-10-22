"""Search distribution-based replacements on the verified 1060 candidate."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import numpy as np
from multiplier.initial_solutions import candidate_g0001_0005_joint1060 as base


class Probe(base.Candidate):
    changes=()
    def _product_columns(self,q,m,z,o,cut):
        cols=super()._product_columns(q,m,z,o,cut)
        side=1 if q[0]==self.input_ids[9] else 2
        for col,pos,kind,mask in self.changes:
            if mask&side:
                if kind=='zero':cols[col][pos]=z
                elif kind=='one':cols[col][pos]=o
        return cols


def main():
 x=np.random.default_rng(8080).integers(-256,256,(4,8192),dtype=np.int64);ref=(x[0]*x[1]+x[2]*x[3])/128;p=np.mean(ref**2)
 def metric(c):
  y=np.asarray(c.simulate_many(list(zip(*x.tolist()))));return 10*np.log10(np.mean((np.floor(y/128+.5)-ref)**2)/p)
 print('base',base.build_circuit().gatecost().total,metric(base.build_circuit()))
 _,cols=base.build_partial_product_layout(); rows=[]
 for col in range(3,7):
  for pos in range(len(cols[col])//2):
   for kind in ('zero','one'):
    for mask in (1,2,3):
     q=Probe();q.changes=((col,pos,kind,mask),);c=q._build_circuit();cost=c.gatecost().total;ev=float(metric(c))
     if cost<1060 and ev<-57.9:rows.append((cost,ev,col,pos,kind,mask))
 for r in sorted(rows):print(r)


if __name__=='__main__':main()
