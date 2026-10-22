"""Exact cut/representation search over retained pre-CSA signals.

Enumerate complete marginal input space, index existing functions, and try
one-gate expressions of existing functions before recursively rebuilding D.
This is bounded local reuse search, not global synthesis or a physical export.
"""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
import json
from multiplier.initial_solutions.candidate_dist_1020_to1015 import Candidate
from multiplier.circuit.multiplier.conditional_compensation.node_set_information import build_experiment


def main():
    b,d,cols,prefix=build_experiment(Candidate,[(4,0),(4,1)])
    roots=[cols[4][0],cols[4][1]]
    supports=[]
    for i,node in enumerate(b.nodes[:prefix]):
        supports.append({i} if i in b.input_ids else set().union(*(supports[j] for j in node.inputs)))
    domain=sorted(set().union(*(supports[n] for n in roots)))
    size=1<<len(domain); mask=(1<<size)-1
    tables={}
    for i,node in enumerate(b.nodes[:prefix]):
        if not supports[i]<=set(domain):continue
        if i in domain:
            bit=domain.index(i);t=sum(((a>>bit)&1)<<a for a in range(size))
        elif node.kind=='ZERO':t=0
        elif node.kind=='ONE':t=mask
        elif node.kind=='NOT':t=mask^tables[node.inputs[0]]
        else:
            a,z=(tables[j] for j in node.inputs)
            t=a&z if node.kind=='AND' else a|z if node.kind=='OR' else a^z
        tables[i]=t
    retained=d.reachable_node_ids()
    pool=[n for n in tables if n in retained and n not in (0,1)]

    def search(available,one_gate):
        # Expression tuples are canonical enough to count shared generated gates.
        index={0:('const',0),mask:('const',1)}
        for n in available:
            index.setdefault(tables[n],('x',n))
            index.setdefault(mask^tables[n],('NOT',('x',n)))
        if one_gate:
            initial=list(index.items())
            for i,(a,ea) in enumerate(initial):
                for z,ez in initial[i:]:
                    for kind,t in [('AND',a&z),('OR',a|z)]:
                        expression=(kind,ea,ez)
                        index.setdefault(t,expression)
                        index.setdefault(mask^t,('NOT',expression))
        memo={}
        def solve(n):
            t=tables[n]
            if t in index:return index[t]
            if n not in memo:
                node=b.nodes[n];memo[n]=(node.kind,*(solve(j) for j in node.inputs))
            return memo[n]
        exprs=[solve(n) for n in roots]
        # Preserve two column-4 outputs: G0+G1 represents D/16 exactly.
        used=set(); gates=set()
        def walk(e):
            if e[0]=='x':used.add(e[1]);return
            if e[0]=='const':return
            gates.add(e)
            for child in e[1:]:walk(child)
        def truth(e):
            if e[0]=='x':return tables[e[1]]
            if e[0]=='const':return mask if e[1] else 0
            if e[0]=='NOT':return mask^truth(e[1])
            a,z=truth(e[1]),truth(e[2])
            return a&z if e[0]=='AND' else a|z if e[0]=='OR' else a^z
        for n,e in zip(roots,exprs):
            walk(e);assert truth(e)==tables[n]
        # Cost of reviving X cones, sharing with each other and retained DAG.
        revived=set()
        def visit(n):
            if n in retained or n in revived:return
            revived.add(n)
            for j in b.nodes[n].inputs:visit(j)
        for n in used:visit(n)
        g_cost=sum(0 if e[0]=='NOT' else 3 if e[0]=='XOR' else 1 for e in gates)
        x_cost=sum(b.components.require(b.nodes[n].kind).gate_cost for n in revived)
        return dict(X=sorted(used),G_expressions=exprs,G_weighted_cost=g_cost,
                    retained_X_extra_cost=x_cost,total_increment_upper_bound=g_cost+x_cost,
                    exact_cases=size,removed_conditional_variance=0)

    parents=sorted({j for n in roots for j in b.nodes[n].inputs})
    report=dict(slots=[[4,0],[4,1]],roots=roots,domain=domain,pool_size=len(pool),
                baseline_cost=b.gatecost().total,physical_deleted_cost=d.gatecost().total,
                note='G outputs are two column-4 bits. Exact D recovery, not a claim of final multiplier improvement.',
                results={})
    for name,available,local in [('raw_inputs',domain,False),('direct_parents',parents,False),
                                ('retained_cut',pool,False),('retained_plus_local',pool,True)]:
        row=search(available,local);report['results'][name]=row
        print(name,json.dumps(row),flush=True)
    Path(__file__).with_suffix('.json').write_text(json.dumps(report,indent=2))


if __name__=='__main__':main()
