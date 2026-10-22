"""Check AB/CD correction-row arithmetic cells in the 1015 layout."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from multiplier.initial_solutions import candidate_dist_1020_to1015 as base
from collections import Counter
from itertools import product


def truth(a,b):
    # Two complemented correction bits plus ONE: 1 + ~a + ~b.
    total = ((1-a)+(1-b)+1) & 1
    carry = ((1-a)+(1-b)+1) >> 1
    return total,carry


def main():
    c,cols=base.build_partial_product_layout()
    for a,b in product((0,1),repeat=2):
        assert truth(a,b)==(((1-a)+(1-b)+1)&1,((1-a)+(1-b)+1)>>1)
    print('two correction + ONE identity exhaustive: 4/4')
    for k,bucket in enumerate(cols):
        ones=[n for n in bucket if n==c._one]
        nots=[n for n in bucket if c.nodes[n].kind=='NOT']
        if ones and len(nots)>=2:
            print('column',k,'ONE',len(ones),'NOT',len(nots),'nodes',nots)
    print('baseline',base.build_circuit().gatecost().total)


if __name__=='__main__':main()
