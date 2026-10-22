"""Search partial-product distribution replacements from the 1060 point."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import numpy as np
from multiplier.initial_solutions import candidate_g0001_0005_joint1060 as base


class Probe(base.Candidate):
    change = None
    def _product_columns(self,q,m,z,o,cut):
        cols=super()._product_columns(q,m,z,o,cut)
        if self.change is not None:
            col,pos,kind,mask=self.change
            side=1 if q[0]==self.input_ids[9] else 2
            if mask&side:
                cols[col][pos]=z if kind=='zero' else o
        return cols


def main():
    x=np.random.default_rng(5001).integers(-256,256,(4,16384),dtype=np.int64)
    ref=(x[0]*x[1]+x[2]*x[3])/128; power=np.mean(ref**2)
    def metric(c):
        y=np.asarray(c.simulate_many(list(zip(*x.tolist()))))
        return float(10*np.log10(np.mean((np.floor(y/128+.5)-ref)**2)/power))
    base_c=base.build_circuit(); print('base',base_c.gatecost().total,metric(base_c))
    _,cols=base.build_partial_product_layout(); rows=[]
    for col in range(3,7):
        # Positions are within one product; both products are candidates.
        for pos in range(2 if col==3 else len(cols[col])//2):
            for kind in ('zero','one'):
                for mask in (1,2,3):
                    p=Probe();p.change=(col,pos,kind,mask);c=p._build_circuit();cost=c.gatecost().total
                    if cost>=1060:continue
                    evm=metric(c)
                    if evm < -58.0: rows.append((cost,evm,col,pos,kind,mask))
    for r in sorted(rows):print(r)


if __name__=='__main__':main()
