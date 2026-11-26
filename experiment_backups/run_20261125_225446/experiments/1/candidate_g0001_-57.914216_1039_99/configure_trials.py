import json
from pathlib import Path
root=Path('/home/guoliang/multiplier/experiments/1/candidate_g0001_0005')
parent=str(root/'parent.py'); stimulus='/home/guoliang/multiplier/stimulus.npy'
trials={
 't01': ([[4,5],[4,6]],[91,425],[4]),
 't02': ([[4,5],[4,6]],[420,421],[4]),
 't03': ([[4,5],[4,6]],[91],[4]),
 't04': ([[4,5],[4,6]],[425],[4]),
 't05': ([[5,0],[5,3]],[94,428],[5]),
 't06': ([[4,0],[4,3]],[152,568],[4]),
 't07': ([[4,5],[4,6],[5,0]],[91,425,94],[4,5]),
}
for name,(slots,nodes,cols) in trials.items():
 p=root/name;p.mkdir(exist_ok=True)
 screen=dict(implementation=parent,stimulus_file=stimulus,removed_slots=slots,node_ids=nodes)
 (p/'screen.json').write_text(json.dumps(screen,indent=2)+'\n')
 (p/'table_config.json').write_text(json.dumps({**screen,'compensation_columns':cols},indent=2)+'\n')
 (p/'synth_config.json').write_text(json.dumps(dict(implementation=parent,error_table=str(p/'table.npy'),node_ids=nodes,compensation_columns=cols,target_evm_db=-57.8,max_gates=2),indent=2)+'\n')
 (p/'export_config.json').write_text(json.dumps(dict(implementation=parent,error_table=str(p/'table.npy'),synthesis_result=str(p/'synth.json')),indent=2)+'\n')
print('created',list(trials))
