import json
from pathlib import Path
base=Path('/home/guoliang/multiplier/experiments/4/candidate_g0004_0008'); parent=str(base/'parent.py');stimulus='/home/guoliang/multiplier/stimulus.npy'
for name,slots,nodes,columns in [('c4p0_b0',[[4,0]],[11],[4]),('c4p1_b0',[[4,1]],[11],[4]),('c4p3_cd',[[4,3]],[29,30],[4]),('c5p6_cd',[[5,6]],[29,30],[5])]:
 d=base/('trial_'+name);d.mkdir(exist_ok=True)
 common={'implementation':parent,'stimulus_file':stimulus,'removed_slots':slots,'node_ids':nodes}
 for file,obj in [('screen.json',common),('table_config.json',{**common,'compensation_columns':columns}),('synth_config.json',{'implementation':parent,'error_table':str(d/'table.npy'),'node_ids':nodes,'compensation_columns':columns,'target_evm_db':-57.68,'max_gates':2}),('export_config.json',{'implementation':parent,'error_table':str(d/'table.npy'),'synthesis_result':str(d/'synthesis.json')})]:
  (d/file).write_text(json.dumps(obj,indent=2)+'\n')
