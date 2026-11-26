import json
from pathlib import Path
root=Path('/home/guoliang/multiplier/experiments/1/candidate_g0001_0005')
p=root/'t08';p.mkdir(exist_ok=True)
base=dict(implementation=str(root/'parent.py'),stimulus_file='/home/guoliang/multiplier/stimulus.npy',removed_slots=[[4,0],[4,3],[4,5]],node_ids=[152,568,91])
for name,data in [('screen.json',base),('table_config.json',{**base,'compensation_columns':[4]}),('synth_config.json',dict(implementation=base['implementation'],error_table=str(p/'table.npy'),node_ids=base['node_ids'],compensation_columns=[4],target_evm_db=-57.8,max_gates=2)),('export_config.json',dict(implementation=base['implementation'],error_table=str(p/'table.npy'),synthesis_result=str(p/'synth.json')))]:
 (p/name).write_text(json.dumps(data,indent=2)+'\n')
