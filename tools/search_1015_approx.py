"""Conservative distribution search from the 1015 candidate."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import numpy as np
from multiplier.initial_solutions import candidate_dist_1020_to1015 as base
from multiplier.tools.search_existing_subcones import simulate


class Probe(base.Candidate):
    change=None
    def _product_columns(self,q,m,z,o,cut):
        cols=super()._product_columns(q,m,z,o,cut)
        if self.change:
            col,pos,path,mask=self.change
            if mask&(1 if q[0]==self.input_ids[9] else 2):
                n=cols[col][pos]
                if path=='zero':n=z
                elif path=='one':n=o
                else:
                    for p in path:n=self.nodes[n].inputs[int(p)]
                cols[col][pos]=n
        return cols


def main():
    x=np.random.default_rng(81015).integers(-256,256,(4,16384),dtype=np.int64)
    ref=(x[0]*x[1]+x[2]*x[3])/128;p=np.mean(ref**2)
    def score(c):
        y=simulate(c,x);return float(10*np.log10(np.mean((np.floor(y/128+.5)-ref)**2)/p))
    base_score=score(base.build_circuit());print('baseline',base_score,flush=True)
    _,cols=base.build_partial_product_layout();rows=[]
    for col in range(4,7):
        for pos in range(len(cols[col])//2):
            for path in ('zero','one','0','1'):
                for mask in (1,2,3):
                    q=Probe();q.change=(col,pos,path,mask);c=q._build_circuit();cost=c.gatecost().total
                    if cost>=1015:continue
                    ev=score(c)
                    if ev>=-57.90:rows.append((cost,ev,col,pos,path,mask))
    for r in sorted(rows,key=lambda z:(z[0],z[1])):print(r,flush=True)


if __name__=='__main__':main()
