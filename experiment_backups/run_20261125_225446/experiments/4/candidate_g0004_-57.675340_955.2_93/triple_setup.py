import json
from pathlib import Path
p=Path('/home/guoliang/multiplier/experiments/4/candidate_g0004_0005/triple')
p.mkdir(exist_ok=True)
parent='/home/guoliang/multiplier/experiments/4/candidate_g0004_0005/parent.py'
nodes=[94,165,417]
config=dict(implementation=parent,stimulus_file='/home/guoliang/multiplier/stimulus.npy',removed_slots=[[5,0],[5,1],[5,3]],node_ids=nodes)
(p/'screen.json').write_text(json.dumps(config,indent=2)+'\n')
(p/'table_config.json').write_text(json.dumps({**config,'compensation_columns':[5,6]},indent=2)+'\n')
(p/'synth_config.json').write_text(json.dumps(dict(implementation=parent,error_table=str(p/'table.npy'),node_ids=nodes,compensation_columns=[5,6],target_evm_db=-57.65,max_gates=6),indent=2)+'\n')
(p/'export_config.json').write_text(json.dumps(dict(implementation=parent,error_table=str(p/'table.npy'),synthesis_result=str(p/'synthesis.json')),indent=2)+'\n')
