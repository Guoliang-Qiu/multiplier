from pathlib import Path
import json
root=Path('/home/guoliang/multiplier/experiments/5/candidate_g0005_0000')
impl=str(root/'parent.py')
stim='/home/guoliang/multiplier/stimulus.npy'
trials={
 'or_d01_pair': ([[5,6]],[29,30],[5]),
 'or_d01_direct': ([[5,6]],[418],[5]),
 'or_d01_single': ([[5,6]],[29],[5]),
 'or_d01_c0': ([[5,6]],[29,30],[4,5]),
 'or_col4_pair': ([[4,4]],[290,326],[4]),
 'or_col4_direct': ([[4,4]],[327],[4]),
 'or_col4_input': ([[4,4]],[29,30],[4]),
 'or_col4_one': ([[4,4]],[290],[4]),
 'both_d01': ([[5,6],[4,4]],[29,30],[4,5]),
}
for name,(slots,nodes,cols) in trials.items():
 p=root/name;p.mkdir(exist_ok=True)
 data=dict(implementation=impl,stimulus_file=stim,removed_slots=slots,node_ids=nodes)
 (p/'screen.json').write_text(json.dumps(data,indent=2)+'\n')
 (p/'table_config.json').write_text(json.dumps(dict(data,compensation_columns=cols),indent=2)+'\n')
 (p/'synth_config.json').write_text(json.dumps(dict(implementation=impl,error_table=str(p/'table.npy'),node_ids=nodes,compensation_columns=cols,target_evm_db=-57.65),indent=2)+'\n')
 (p/'export_config.json').write_text(json.dumps(dict(implementation=impl,error_table=str(p/'table.npy'),synthesis_result=str(p/'synthesis.json')),indent=2)+'\n')
print('created',len(trials),'distinct trial configs')
