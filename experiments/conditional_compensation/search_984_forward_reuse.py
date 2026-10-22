"""Exact X reuse allowing later independent pre-compression nodes.

Rebuild recursively with cycle detection, instead of assuming numeric node
order remains topological after replacements. Exhaustive marginal truth tables
prove each proposed replacement; total reachable cost selects improvements.
"""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
import json
from multiplier.initial_solutions import candidate_dist_top_reuse984 as source
from multiplier.experiments.conditional_compensation.search_reuse_1012 import Rebuild


def reconstruct(old,subs):
    new=Rebuild();mp={};busy=set()
    for i,n in enumerate(old.nodes):
        if not n.inputs:
            mp[i]=new.add(n.kind)
            if n.kind=='ZERO':new._zero=mp[i]
            if n.kind=='ONE':new._one=mp[i]
    def expr(e):
        if isinstance(e,int):return node(e)
        return new._gate(e[0],*(expr(j) for j in e[1:]))
    def node(i):
        if i in mp:return mp[i]
        if i in busy:raise ValueError('cyclic replacement')
        busy.add(i)
        if i in subs:n=expr(subs[i])
        else:n=new._gate(old.nodes[i].kind,*(node(j) for j in old.nodes[i].inputs))
        busy.remove(i);mp[i]=n;return n
    new.input_ids=[mp[i] for i in old.input_ids]
    new.output_ids=[node(i) for i in old.output_ids]
    return new


def main():
    old=source.build_circuit();p=source.Candidate();cols=p._product_columns(*p.setup());prefix=len(p.nodes)
    support=[];ancestors=[];inputs=set(old.input_ids);active=old.reachable_node_ids()
    for i,n in enumerate(old.nodes[:prefix]):
        support.append({i} if i in inputs else set().union(*(support[j] for j in n.inputs)))
        ancestors.append(set(n.inputs).union(*(ancestors[j] for j in n.inputs)))
    best=old.gatecost().total;subs={};history=[];tested=0
    for root in sorted(active):
        if root>=prefix or root in inputs or not 2<=len(support[root])<=7:continue
        domain=sorted(support[root]);size=1<<len(domain);mask=(1<<size)-1;tables={}
        for i,n in enumerate(old.nodes[:prefix]):
            if not support[i]<=support[root]:continue
            if i in inputs:
                bit=domain.index(i);t=sum(((a>>bit)&1)<<a for a in range(size))
            elif n.kind=='ZERO':t=0
            elif n.kind=='ONE':t=mask
            elif n.kind=='NOT':t=mask^tables[n.inputs[0]]
            else:
                a,b=(tables[j] for j in n.inputs)
                t=a&b if n.kind=='AND' else a|b if n.kind=='OR' else a^b
            tables[i]=t
        pool={}
        for i,t in tables.items():
            if i==root or root in ancestors[i] or i not in active:continue
            pool.setdefault(t,i);pool.setdefault(mask^t,('NOT',i))
        target=tables[root];options=[]
        if target in pool:options.append(pool[target])
        items=list(pool.items())
        for j,(a,ea) in enumerate(items):
            for b,eb in items[j:]:
                for op,t in [('AND',a&b),('OR',a|b)]:
                    if t==target:options.append((op,ea,eb))
                    elif mask^t==target:options.append(('NOT',(op,ea,eb)))
        for e in options:
            tested+=1;trial=dict(subs);trial[root]=e
            try:c=reconstruct(old,trial)
            except ValueError:continue
            cost=c.gatecost().total
            if cost<best:
                best=cost;subs=trial;history.append(dict(node=root,expression=e,cost=cost,cases=size))
                print(history[-1],flush=True)
    result=dict(baseline=984,best=best,tested=tested,history=history,substitutions=subs)
    Path(__file__).with_suffix('.json').write_text(json.dumps(result,indent=2))
    print('finished',best,tested,flush=True)


if __name__=='__main__':main()
