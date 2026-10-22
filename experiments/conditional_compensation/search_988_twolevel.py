"""Two-level exact X reuse over full structural supports, before any SMT approximation."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
import json
from multiplier.initial_solutions import candidate_dist_top_reuse988 as source
from multiplier.experiments.conditional_compensation.search_reuse_1012 import rebuild


def main():
    global source
    import argparse, importlib
    parser=argparse.ArgumentParser()
    parser.add_argument('--source',default='multiplier.initial_solutions.candidate_dist_top_reuse988')
    parser.add_argument('--include-compressors',action='store_true')
    parser.add_argument('--output',type=Path,default=Path(__file__).with_suffix('.json'))
    args=parser.parse_args()
    source=importlib.import_module(args.source)
    old=source.build_circuit();layout=source.Candidate();layout._product_columns(*layout.setup())
    prefix=len(layout.nodes);active=old.reachable_node_ids();inputs=set(old.input_ids)
    if args.include_compressors:prefix=len(old.nodes)
    support=[]
    for i,n in enumerate(old.nodes[:prefix]):
        support.append({i} if i in inputs else set().union(*(support[j] for j in n.inputs)))
    subs={};best=old.gatecost().total;history=[];tested=0
    for root in sorted(active):
        if root>=prefix or root in inputs or not 2<=len(support[root])<=7:continue
        domain=sorted(support[root]);size=1<<len(domain);mask=(1<<size)-1;tables={}
        for i,n in enumerate(old.nodes[:root+1]):
            if not support[i]<=support[root]:continue
            if i in inputs:
                j=domain.index(i);t=sum(((a>>j)&1)<<a for a in range(size))
            elif n.kind=='ZERO':t=0
            elif n.kind=='ONE':t=mask
            elif n.kind=='NOT':t=mask^tables[n.inputs[0]]
            else:
                a,b=(tables[j] for j in n.inputs)
                t=a&b if n.kind=='AND' else a|b if n.kind=='OR' else a^b
            tables[i]=t
        pool={}
        for n,t in tables.items():
            if n==root or n not in active:continue
            pool.setdefault(t,n);pool.setdefault(mask^t,('NOT',n))
        items=list(pool.items());pairs={}
        for j,(a,ea) in enumerate(items):
            for b,eb in items[j:]:
                for op,t in [('AND',a&b),('OR',a|b)]:
                    if t not in pool:pairs.setdefault(t,(op,ea,eb))
                    if mask^t not in pool:pairs.setdefault(mask^t,('NOT',(op,ea,eb)))
        target=tables[root];seen=set()
        for wanted,invert in ((target,False),(mask^target,True)):
            for a,ea in items:
                kinds=[]
                if wanted & ~a == 0:kinds.append('AND')
                if a & ~wanted == 0:kinds.append('OR')
                for op in kinds:
                    for b,eb in pairs.items():
                        t=a&b if op=='AND' else a|b
                        if t!=wanted:continue
                        e=(op,ea,eb)
                        if invert:e=('NOT',e)
                        if e in seen:continue
                        seen.add(e);tested+=1
                        trial=dict(subs);trial[root]=e
                        c=rebuild(old,trial);cost=c.gatecost().total
                        if cost<best:
                            best=cost;subs=trial
                            history.append(dict(node=root,expression=e,cost=cost,exhaustive_cases=size))
                            print(history[-1],flush=True)
        print('root',root,'best',best,'tested',tested,flush=True) if root%100==0 else None
    report=dict(baseline=old.gatecost().total,best=best,tested=tested,history=history,substitutions=subs)
    args.output.write_text(json.dumps(report,indent=2))
    print('finished',best,tested,flush=True)


if __name__=='__main__':main()
