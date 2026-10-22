"""Choose exact information-preserving X cuts; keep experiments outside circuit."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
import json
import numpy as np
from multiplier.initial_solutions.candidate_dist_1020_to1015 import Candidate
from multiplier.circuit.multiplier.conditional_compensation.node_set_information import (
    build_experiment, evaluate_node_set, generate_evaluation_samples, conditional_variance)
from multiplier.circuit.simulation import _simulate_values


def main():
    slots=[(4,0),(4,1)]
    baseline,deleted,cols,prefix=build_experiment(Candidate,slots)
    roots=[cols[k][p] for k,p in slots]
    parents=sorted({i for n in roots for i in baseline.nodes[n].inputs})
    reachable=deleted.reachable_node_ids()
    inputs=set(baseline.input_ids)
    def cut(n,stop):
        node=baseline.nodes[n]
        if node.kind in ('ZERO','ONE'):return set()
        if stop(n):return {n}
        return set().union(*(cut(j,stop) for j in node.inputs))
    raw=sorted(set().union(*(cut(n,lambda i:i in inputs) for n in roots)))
    retained=sorted(set().union(*(cut(n,lambda i:i in reachable) for n in parents)))
    # Exhaust all original input dependencies, preserving correlations among X.
    # Other primary inputs are irrelevant to D and the selected ancestor cuts.
    all_values=[]
    for mask in range(1<<len(raw)):
        assigned={n:(mask>>i)&1 for i,n in enumerate(raw)}
        all_values.append(_simulate_values(baseline,[assigned.get(n,0) for n in baseline.input_ids]))
    values=np.asarray(all_values,dtype=np.int64)
    contribution=sum(values[:,n]*(1<<k) for n,(k,p) in zip(roots,slots))
    def exact_information(ns):
        code=sum((values[:,n]<<i for i,n in enumerate(ns)),np.zeros(len(values),dtype=np.int64))
        for s in np.unique(code):
            ds=contribution[code==s]
            if np.any(ds!=ds[0]):return False
        return True
    def minimize(ns):
        result=list(ns)
        for n in ns:
            trial=[j for j in result if j!=n]
            if exact_information(trial):result=trial
        return result
    selections={'direct_parents':minimize(parents),
                'retained_ancestor_cut':minimize(retained),
                'primary_dependencies':minimize(raw)}
    samples,_=generate_evaluation_samples()
    reports={}
    for name,ns in selections.items():
        assert exact_information(ns)
        report=evaluate_node_set(Candidate,slots,ns,samples=samples,deletion_model='linear')
        assert report['removed_conditional_variance']==0
        assert abs(report['conditional_variance_gap'])<1e-12
        # Cost to reconstruct the two removed functions from X, accounting for
        # shared ancestors. This is an upper bound for G=D, not a synthesis claim.
        visited=set()
        def visit(n):
            if n in ns or n in visited:return
            visited.add(n)
            for j in baseline.nodes[n].inputs:visit(j)
        for n in roots:visit(n)
        reconstruction=sum(baseline.components.require(baseline.nodes[n].kind).gate_cost for n in visited)
        report.update(exhaustive_dependency_cases=len(values),D_determined_for_all_inputs=True,
                      reconstruction_cost_upper_bound=reconstruction)
        reports[name]=report
        print(name,'X',ns,'D reconstruction cost',reconstruction,
              'original var',report['baseline_conditional_variance'],
              'deleted var',report['information_mse'],
              'gap',report['conditional_variance_gap'],flush=True)
    # Exact deterministic variance and original-error positive controls.
    assert conditional_variance(np.array([1.,1.,3.,3.]),np.array([0,0,1,1]),1)[0]==0
    (Path(__file__).resolve().parent/'linear_x_selection.json').write_text(json.dumps(reports,indent=2))


if __name__=='__main__':main()
