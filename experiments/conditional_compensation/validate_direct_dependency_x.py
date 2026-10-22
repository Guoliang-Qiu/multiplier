"""Check conditional variance using the exact immediate parents of removed bits.

Diagnostic only: permits observation of parents that deletion makes unreachable.
Does not relax the production tool's retained-node eligibility requirement.
"""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
import copy
import json
import numpy as np
from multiplier.initial_solutions.candidate_dist_1020_to1015 import Candidate
from multiplier.circuit.multiplier.conditional_compensation.node_set_information import (
    build_experiment,generate_evaluation_samples,_sample_values,conditional_variance,_db)


def main():
    slots=[(4,0),(4,1)]
    b,d,cols,_=build_experiment(Candidate,slots)
    removed=[cols[k][p] for k,p in slots]
    nodes=sorted({j for n in removed for j in b.nodes[n].inputs})
    samples,sampling=generate_evaluation_samples()
    br,values=_sample_values(b,samples,nodes+removed)
    dr,_=_sample_values(d,samples,[])
    codes=sum(values[:,j].astype(np.int64)<<j for j in range(len(nodes)))
    contribution=sum(values[:,len(nodes)+j].astype(np.int64)*(1<<k)
                     for j,(k,p) in enumerate(slots))
    # Independent grouped variance implementation (two-pass per observed state).
    def check(v):
        loss,counts=conditional_variance(v,codes,len(nodes))
        direct=sum(float(np.sum((v[codes==s]-v[codes==s].mean())**2))
                   for s in np.flatnonzero(counts))/len(v)
        assert np.isclose(loss,direct,rtol=1e-12,atol=1e-12)
        return loss
    for j,n in enumerate(removed):
        node=b.nodes[n]
        assert node.kind=='OR'
        rebuilt=values[:,nodes.index(node.inputs[0])] | values[:,nodes.index(node.inputs[1])]
        assert np.array_equal(rebuilt,values[:,len(nodes)+j])
    # Restore exact source positions before compression. This must reproduce
    # the baseline DAG, including order-sensitive approximate downstream logic.
    prefix=Candidate();prefix._columns=prefix._product_columns(*prefix.setup())
    restored=copy.deepcopy(prefix)
    for k,p in sorted(slots,reverse=True):del restored._columns[k][p]
    for k,p in sorted(slots):restored._columns[k].insert(p,cols[k][p])
    restored._compress_columns();restored._build_outputs()
    assert restored.nodes==b.nodes and restored.output_ids==b.output_ids
    reference=(samples[:,0]*samples[:,1]+samples[:,2]*samples[:,3])/128
    qb=(br+64)//128;qd=(dr+64)//128
    energy=float(np.mean(reference**2))
    base_error=reference-qb;residual=reference-qd
    # Requested validation: no external rounding in these residuals.
    original_raw_error=reference-br/128
    deleted_raw_error=reference-dr/128
    # Positive control: subtraction before any nonlinear circuit processing.
    synthetic_deleted=br-contribution
    synthetic_error=reference-synthetic_deleted/128
    assert np.array_equal(synthetic_error-contribution/128,original_raw_error)
    # If removal had been a linear column-sum subtraction, this would equal br.
    restored_raw=(dr+contribution+(1<<18))%(1<<19)-(1<<18)
    quantities={
        'removed_weighted_sum':contribution.astype(float),
        'baseline_minus_deleted_raw':(br-dr).astype(float),
        'baseline_minus_deleted_quantized':(qb-qd).astype(float),
        'baseline_error':base_error,
        'tool_residual':residual,
        'original_raw_error':original_raw_error,
        'deleted_raw_error':deleted_raw_error,
        'synthetic_linear_deleted_error':synthetic_error,
        'actual_raw_error_after_exact_D_compensation':reference-(dr+contribution)/128,
    }
    variances={name:check(v) for name,v in quantities.items()}
    assert variances['removed_weighted_sum']==0
    assert np.isclose(variances['original_raw_error'],
                      variances['synthetic_linear_deleted_error'],rtol=1e-12,atol=1e-12)
    witnesses=[]
    for s in np.unique(codes):
        ix=np.flatnonzero(codes==s);delta=br[ix]-dr[ix]
        if delta.min()!=delta.max():
            for t in (ix[delta.argmin()],ix[delta.argmax()]):
                witnesses.append(dict(X=int(s),input=samples[t].tolist(),
                    removed_sum=int(contribution[t]),baseline_raw=int(br[t]),deleted_raw=int(dr[t])))
            break
    report=dict(sampling=sampling,count=len(samples),slots=slots,removed_nodes=removed,
        immediate_parent_X=nodes,unreachable_after_deletion=[n for n in nodes if n not in d.reachable_node_ids()],
        baseline_evm=_db(float(np.mean(base_error**2)),energy),
        deleted_evm=_db(float(np.mean(residual**2)),energy),
        information_evm=_db(variances['tool_residual'],energy),conditional_variances=variances,
        exact_reinsertion_graph_equal=True,
        post_output_addition_raw_mismatches=int(np.count_nonzero(restored_raw!=br)),
        post_output_addition_evm=_db(float(np.mean((reference-(restored_raw+64)//128)**2)),energy),
        same_X_counterexample=witnesses)
    report['unquantized_validation']={
        'units':'raw/128; no floor in any residual in this section',
        'baseline_mse':float(np.mean(original_raw_error**2)),
        'deleted_mse':float(np.mean(deleted_raw_error**2)),
        'baseline_conditional_variance':variances['original_raw_error'],
        'deleted_conditional_variance':variances['deleted_raw_error'],
        'baseline_conditional_variance_evm_db':_db(variances['original_raw_error'],energy),
        'deleted_conditional_variance_evm_db':_db(variances['deleted_raw_error'],energy),
        'synthetic_linear_deletion_conditional_variance':variances['synthetic_linear_deleted_error'],
        'synthetic_compensation_restores_original_error':True,
        'raw_delta_equals_D_mismatches':int(np.count_nonzero(br-dr!=contribution)),
        'actual_compensation_error_mse':float(np.mean((reference-(dr+contribution)/128)**2)),
        'baseline_conditional_mean_square':float(np.mean(original_raw_error**2))-variances['original_raw_error'],
    }
    out=Path(__file__).resolve().parent/'direct_dependency_x_validation.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
