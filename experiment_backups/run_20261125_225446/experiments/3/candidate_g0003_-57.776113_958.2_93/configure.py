import json
from pathlib import Path
root=Path('/home/guoliang/multiplier/experiments/3/candidate_g0003_0005')
parent=str(root/'parent.py')
trials={'t1_exact':([[4,4]],[20,507],[4]),'t2_one':([[4,4]],[507],[4]),'t3_other':([[4,4]],[20],[4]),'t4_or':([[5,5]],[555,556],[5]),'t5_or_one':([[5,5]],[555],[5]),'t6_zero_or':([[4,3],[5,5]],[555,556],[5]),'t7_zero_and_or':([[4,3],[4,4],[5,5]],[20,507,555,556],[4,5]),'t8_joint_one':([[4,4],[5,5]],[20,507,555,556],[4])}
for name,(removed,nodes,cols) in trials.items():
 d=root/name;d.mkdir(exist_ok=True)
 common=dict(implementation=parent,stimulus_file='/home/guoliang/multiplier/stimulus.npy',removed_slots=removed,node_ids=nodes)
 for file,data in [('screen.json',common),('table_config.json',dict(common,compensation_columns=cols)),('synthesis_config.json',dict(implementation=parent,error_table=str(d/'table.npy'),node_ids=nodes,compensation_columns=cols,target_evm_db=-57.65)),('export_config.json',dict(implementation=parent,error_table=str(d/'table.npy'),synthesis_result=str(d/'synthesis.json')))]:
  (d/file).write_text(json.dumps(data,indent=2)+'\n')
