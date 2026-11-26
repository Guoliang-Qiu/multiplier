import json
from pathlib import Path
base=Path('/home/guoliang/multiplier/experiments/4/candidate_g0004_0008')
parent=str(base/'parent.py');stimulus='/home/guoliang/multiplier/stimulus.npy'
for name,slots,nodes,columns in [
 ('c4p2_a0',[[4,2]],[2],[4]),
 ('c4p2_factor',[[4,2]],[179],[4]),
 ('c4p2_none',[[4,2]],[],[4]),
 ('c4p01_b0',[[4,0],[4,1]],[11],[4,5]),
]:
 d=base/('trial_'+name);d.mkdir(exist_ok=True)
 shared={'implementation':parent,'stimulus_file':stimulus,'removed_slots':slots,'node_ids':nodes}
 for filename,config in [('screen.json',shared),('table_config.json',{**shared,'compensation_columns':columns}),('synth_config.json',{'implementation':parent,'error_table':str(d/'table.npy'),'node_ids':nodes,'compensation_columns':columns,'target_evm_db':-57.68}),('export_config.json',{'implementation':parent,'error_table':str(d/'table.npy'),'synthesis_result':str(d/'synthesis.json')})]:
  (d/filename).write_text(json.dumps(config,indent=2)+'\n')
print('Prepared four trial directories')
