"""Inspect exact AB/CD fusion opportunities in the 1015 candidate."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from multiplier.initial_solutions import candidate_dist_1020_to1015 as base
from collections import defaultdict
import json


def deps(c, n, memo):
    if n in memo:return memo[n]
    node=c.nodes[n]
    if node.kind.startswith('IN_'): r={c.input_ids.index(n)}
    elif node.kind in ('ZERO','ONE'):r=set()
    else:r=set().union(*(deps(c,x,memo) for x in node.inputs))
    memo[n]=r;return r


def main():
    c,cols=base.build_partial_product_layout();memo={};rows=[]
    for col,bucket in enumerate(cols):
        ab=[];cd=[]
        for pos,n in enumerate(bucket):
            ds=deps(c,n,memo)
            if ds and max(ds)<18:ab.append((pos,n,ds))
            elif ds and min(ds)>=18:cd.append((pos,n,ds))
        if not ab or not cd:continue
        # Same structural function is only useful if the actual support is
        # shared; AB/CD supports are disjoint, so record exact support overlap.
        for a in ab:
            for d in cd:
                rows.append(dict(column=col,ab_pos=a[0],cd_pos=d[0],
                    ab_node=a[1],cd_node=d[1],support_overlap=sorted(a[2]&d[2]),
                    ab_deps=len(a[2]),cd_deps=len(d[2])))
    print('cross-product pairs',len(rows),'shared-input pairs',sum(bool(x['support_overlap']) for x in rows))
    print('column pair counts', {k:sum(x['column']==k for x in rows) for k in sorted(set(x['column'] for x in rows))})
    print('gate cost baseline',base.build_circuit().gatecost().total)
    with open('/tmp/opencode/explore1015_abcd.json','w') as f:json.dump(rows,f,indent=2)


if __name__=='__main__':main()
