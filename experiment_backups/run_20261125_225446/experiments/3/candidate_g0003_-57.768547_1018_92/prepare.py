"""Prepare reproducible screening, table and synthesis configs for three X tradeoffs."""
import json
from pathlib import Path
root=Path('/home/guoliang/multiplier/experiments/3/candidate_g0003_0001')
parent=str(root/'parent.py'); stimulus='/home/guoliang/multiplier/stimulus.npy'
trials={'compact': ([11,55],[[4,0]],[4]), 'shared': ([11,55,43],[[4,0]],[4]), 'predictive': ([11,55,43,51],[[4,0]],[4]), 'exact_reactivated': ([91],[[4,0]],[4]), 'joint_compact': ([11,55],[[4,0],[5,0]],[4]), 'joint_shared': ([11,55,59],[[4,0],[5,0]],[4]), 'double': ([91,149],[[4,0],[4,1]],[4]), 'double_shared': ([55,110,117],[[4,0],[4,1]],[4]), 'double_two_bits': ([91,149],[[4,0],[4,1]],[4,4]), 'joint_two_bits': ([91,94],[[4,0],[5,0]],[4,5]), 'double_high': ([91,149],[[4,0],[4,1]],[5])}
for name,(nodes,slots,comp_cols) in trials.items():
 run=root/name;run.mkdir(exist_ok=True)
 basic={'implementation':parent,'stimulus_file':stimulus,'removed_slots':slots,'node_ids':nodes}
 for file,config in [('screen_config.json',basic),('table_config.json',{**basic,'compensation_columns':comp_cols}),('synth_config.json',{'implementation':parent,'error_table':str(run/'table.npy'),'node_ids':nodes,'compensation_columns':comp_cols,'target_evm_db':-57.65,'max_gates':3}),('export_config.json',{'implementation':parent,'error_table':str(run/'table.npy'),'synthesis_result':str(run/'synthesis.json')})]:
  (run/file).write_text(json.dumps(config,indent=2)+'\n')
