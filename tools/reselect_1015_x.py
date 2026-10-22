"""Cost-aware X choices: retained Booth subfunctions and boundary context.

Reuse tool sampling and packed simulation once, then form the exact integer
conditional tables for each explicitly selected observation vector.
"""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import json
import numpy as np
from multiplier.initial_solutions.candidate_dist_1020_to1015 import Candidate
from multiplier.circuit.multiplier.conditional_compensation.node_set_information import (
    build_experiment, generate_evaluation_samples, _sample_values)
from multiplier.circuit.multiplier.conditional_compensation.compensation_error_table import (
    evaluate_truth_table, _add_signed_raw)
from multiplier.circuit.multiplier.conditional_compensation.synthesize import synthesize


def main():
    slots=[(4,0),(4,1)]
    baseline,deleted,cols,prefix=build_experiment(Candidate,slots)
    eligible=deleted.reachable_node_ids()
    # Original OR terms are gone, but their select/multiplicand subfunctions
    # survive in adjacent Booth bits. These permit cheap reconstruction of G.
    sub=[11,43,55,110,119,123,94,166]
    sets={
        'raw_dependencies':[2,3,4,5,6,11,12,13,14],
        'retained_subfunctions':sub,
        'boundary_context':[239,432,496,582,94,166,238,437,509,581],
        'subfunctions_with_context':sub+[239,432,496,582,238,437,509,581],
    }
    for ns in sets.values():
        assert all(n<prefix and n in eligible for n in ns),ns
    union=sorted(set().union(*map(set,sets.values())))
    samples,sampling=generate_evaluation_samples()
    raw,bits=_sample_values(deleted,samples,union)
    exact=samples[:,0]*samples[:,1]+samples[:,2]*samples[:,3]
    energy=int(np.square(exact).sum())
    losses=np.stack([np.square(exact-128*((_add_signed_raw(raw,k)+64)//128))
                     for k in (0,64)],axis=1)
    oracle=float(10*np.log10(int(losses.min(axis=1).sum())/energy))
    out=Path(__file__).resolve().parents[1]/'experiments/conditional_compensation'
    out.mkdir(parents=True, exist_ok=True)
    results={'per_sample_action_oracle_evm':oracle,'experiments':[]}
    print('Unrestricted per-sample choice of 0/64:',oracle,flush=True)
    for name,ns in sets.items():
        codes=sum(bits[:,union.index(n)].astype(np.int64)<<j for j,n in enumerate(ns))
        table=np.zeros((1<<len(ns),2),dtype=np.int64)
        for k in range(2):np.add.at(table[:,k],codes,losses[:,k])
        meta=dict(sampling={**sampling,'count':len(samples)},removed_slots=slots,
                  node_ids=ns,compensation_columns=[6],num_inputs=len(ns),num_outputs=1,
                  compensation_values=[0,64],raw_output_width=19,error_scale=16384,
                  reference_squared_sum=energy,state_counts=np.bincount(codes,minlength=len(table)).tolist())
        best=evaluate_truth_table(meta,table,table.argmin(axis=1).tolist())
        # Assess zero-gate wires/constants before considering Boolean networks.
        wires=[('ZERO',[0]*len(table)),('ONE',[1]*len(table))]
        for j,n in enumerate(ns):wires.append((str(n),[(x>>j)&1 for x in range(len(table))]))
        wire=min(((evaluate_truth_table(meta,table,v)['evm_db'],label) for label,v in wires))
        result=synthesize(table,meta,baseline.gatecost().total-deleted.gatecost().total,
                          -57.85,max_gates=4,timeout_ms=15000)
        path=out/('experiment_1015_x_'+name)
        np.save(path.with_suffix('.npy'),table)
        path.with_suffix('.json').write_text(json.dumps(meta,indent=2))
        row=dict(name=name,node_ids=ns,best_unrestricted=best,best_wire=wire,synthesis=result)
        results['experiments'].append(row)
        print(name,'oracle',best['evm_db'],'wire',wire,'SMT',result['status'],flush=True)
    (out/'experiment_1015_x_comparison.json').write_text(json.dumps(results,indent=2))


if __name__=='__main__':main()
