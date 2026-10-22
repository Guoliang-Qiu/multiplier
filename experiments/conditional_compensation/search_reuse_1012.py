"""Bounded existing-X reuse: exact full-support checking, no ABC synthesis.

For each pre-CSA node, try a wire, NOT, or single AND/OR of existing earlier
signals (including inverted signals). Choose by whole-circuit reachable cost,
not by expression size. All selected functions match on the full support.
"""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
import json
from multiplier.candidate_support.staged import StagedCandidate
from multiplier.experiments.conditional_compensation import candidate_x_reuse as source


class Rebuild(StagedCandidate):
    _USE_ABSORPTION=True
    def _product_columns(self,*args):raise NotImplementedError
    def _compress_columns(self):raise NotImplementedError
    def _build_outputs(self):raise NotImplementedError


def rebuild(old, substitutions):
    new=Rebuild(); mp={}
    def emit(e):
        if isinstance(e,int):return mp[e]
        return new._gate(e[0],*(emit(a) for a in e[1:]))
    for i,n in enumerate(old.nodes):
        if i in substitutions:q=emit(substitutions[i])
        elif not n.inputs:
            q=new.add(n.kind)
            if n.kind=='ZERO':new._zero=q
            if n.kind=='ONE':new._one=q
        else:q=new._gate(n.kind,*(mp[j] for j in n.inputs))
        mp[i]=q
    new.input_ids=[mp[i] for i in old.input_ids]
    new.output_ids=[mp[i] for i in old.output_ids]
    return new


def candidates(old,prefix):
    support=[]; inputs=set(old.input_ids)
    for i,n in enumerate(old.nodes[:prefix]):
        support.append({i} if i in inputs else set().union(*(support[j] for j in n.inputs)))
    active=old.reachable_node_ids()
    for root in sorted(active):
        if root>=prefix or root in inputs or not old.nodes[root].inputs:continue
        domain=sorted(support[root])
        if len(domain)>10:continue
        size=1<<len(domain); mask=(1<<size)-1; tables={}
        for i,n in enumerate(old.nodes[:root+1]):
            if not support[i]<=support[root]:continue
            if i in inputs:
                bit=domain.index(i); t=sum(((a>>bit)&1)<<a for a in range(size))
            elif n.kind=='ZERO':t=0
            elif n.kind=='ONE':t=mask
            elif n.kind=='NOT':t=mask^tables[n.inputs[0]]
            else:
                a,b=(tables[j] for j in n.inputs)
                t=a&b if n.kind=='AND' else a|b if n.kind=='OR' else a^b
            tables[i]=t
        target=tables[root]; pool={}
        for i,t in tables.items():
            if i==root or i not in active:continue
            pool.setdefault(t,i);pool.setdefault(mask^t,('NOT',i))
        if target in pool:yield root,pool[target],len(domain)
        items=list(pool.items())
        for j,(a,ea) in enumerate(items):
            for b,eb in items[j:]:
                for op,t in [('AND',a&b),('OR',a|b)]:
                    if t==target:yield root,(op,ea,eb),len(domain)
                    elif mask^t==target:yield root,('NOT',(op,ea,eb)),len(domain)


def main():
    global source
    import argparse, importlib
    parser=argparse.ArgumentParser()
    parser.add_argument('--source',default='multiplier.experiments.conditional_compensation.candidate_x_reuse')
    parser.add_argument('--output',type=Path,default=Path(__file__).with_suffix('.json'))
    args=parser.parse_args()
    source=importlib.import_module(args.source)
    old=source.build_circuit();p=source.Candidate();p._product_columns(*p.setup());prefix=len(p.nodes)
    subs={};best=old.gatecost().total;history=[];tested=0
    for root,e,nbits in candidates(old,prefix):
        tested+=1
        trial=dict(subs);trial[root]=e
        c=rebuild(old,trial);cost=c.gatecost().total
        if cost<best:
            best=cost;subs=trial;history.append(dict(node=root,expression=e,cost=cost,exhaustive_inputs=nbits))
            print(history[-1],flush=True)
    report=dict(baseline_cost=old.gatecost().total,best_cost=best,tested=tested,
                substitutions=subs,history=history)
    args.output.write_text(json.dumps(report,indent=2))
    print('result',best,'tested',tested)


if __name__=='__main__':main()
