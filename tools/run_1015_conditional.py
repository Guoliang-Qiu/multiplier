"""One structurally selected conditional-compensation experiment on 1015."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import json
import numpy as np
from multiplier.initial_solutions.candidate_dist_1020_to1015 import Candidate
from multiplier.circuit.multiplier.conditional_compensation.node_set_information import evaluate_node_set
from multiplier.circuit.multiplier.conditional_compensation.compensation_error_table import generate_error_table,evaluate_truth_table
from multiplier.circuit.multiplier.conditional_compensation.synthesize import synthesize
from multiplier.circuit.multiplier.conditional_compensation.export_candidate import build_compensated_candidate,candidate_source


def main():
    out=Path(__file__).resolve().parents[1]/'experiments/conditional_compensation'
    out.mkdir(parents=True, exist_ok=True)
    prefix=out/'experiment_1015_ab4'
    slots=[(4,0),(4,1)]
    nodes=[2,3,4,5,6,11,12,13,14]
    columns=[6]
    target=-57.85
    config=dict(implementation='../../initial_solutions/candidate_dist_1020_to1015.py',
                removed_slots=slots,node_ids=nodes,compensation_columns=columns,target_evm_db=target)
    prefix.with_suffix('.config.json').write_text(json.dumps(config,indent=2))
    info=evaluate_node_set(Candidate,slots,nodes,deletion_model='physical')
    prefix.with_suffix('.information.json').write_text(json.dumps(info,indent=2))
    print('information',info['baseline'],info['deleted'],flush=True)
    meta,table=generate_error_table(Candidate,slots,nodes,columns)
    np.save(prefix.with_suffix('.npy'),table)
    prefix.with_suffix('.json').write_text(json.dumps(meta,indent=2))
    oracle=evaluate_truth_table(meta,table,table.argmin(axis=1).tolist())
    print('unrestricted conditional table optimum',oracle,flush=True)
    saving=info['baseline']['gate_cost']-info['deleted']['gate_cost']
    result=synthesize(table,meta,saving,target,max_gates=4,timeout_ms=15000)
    prefix.with_suffix('.synthesis.json').write_text(json.dumps(result,indent=2))
    print('synthesis',result,flush=True)
    if result['status']=='sat':
        circuit,report=build_compensated_candidate(Candidate,meta,result,table)
        exported=out/'candidate_1015_ab4_compensated.py'
        exported.write_text(candidate_source(circuit).replace(
            'from ..tap2_9bit_multiplier import MultiplierCircuit',
            'from multiplier.circuit.multiplier.tap2_9bit_multiplier import MultiplierCircuit'))
        exported.with_suffix('.json').write_text(json.dumps(report,indent=2))
        print('export',report,flush=True)


if __name__=='__main__':main()
