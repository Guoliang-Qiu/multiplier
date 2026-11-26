import json
from pathlib import Path
p=Path('/home/guoliang/multiplier/experiments/2/candidate_g0002_0006/d4pair_shared');p.mkdir(exist_ok=True)
i='/home/guoliang/multiplier/experiments/2/candidate_g0002_0006/parent.py'; s='/home/guoliang/multiplier/stimulus.npy'
b=dict(implementation=i,stimulus_file=s,removed_slots=[[4,1],[4,4]],node_ids=[110,426])
for name,conf in [('screen.json',b),('table_config.json',dict(b,compensation_columns=[5])),('synth_config.json',dict(implementation=i,error_table=str(p/'table.npy'),node_ids=b['node_ids'],compensation_columns=[5],target_evm_db=-57.8,max_gates=0)),('export_config.json',dict(implementation=i,error_table=str(p/'table.npy'),synthesis_result=str(p/'synth.json')))]:
 (p/name).write_text(json.dumps(conf,indent=2)+'\n')
