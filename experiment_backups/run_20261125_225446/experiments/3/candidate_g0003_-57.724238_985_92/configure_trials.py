import json
from pathlib import Path
root=Path('/home/guoliang/multiplier/experiments/3/candidate_g0003_0000')
parent=str(root/'parent.py'); stimulus='/home/guoliang/multiplier/stimulus.npy'
trials={
 't1_shared': ([[4,1],[4,4]],[152,739],[4,5]),
 't2_inputs': ([[4,1],[4,4]],[3,4,12,13,24,29,30],[4,5]),
 't3_other': ([[4,1],[4,4]],[152,24,29,30],[4,5]),
 't4_compact': ([[4,2],[4,4]],[486,739],[4,5]),
 't5_single': ([[4,4]],[24,29,30],[4]),
 't6_or': ([[4,1],[4,4]],[152,739],[4]),
 't7_three': ([[4,1],[4,2],[4,4]],[152,486,739],[4,5]),
 't8_direct': ([[4,4]],[739],[4]),
}
for name,(removed,nodes,cols) in trials.items():
 p=root/name;p.mkdir(exist_ok=True)
 base={'implementation':parent,'stimulus_file':stimulus,'removed_slots':removed,'node_ids':nodes}
 for filename,config in [('screen.json',base),('table_config.json',{**base,'compensation_columns':cols}),('synth_config.json',{'implementation':parent,'error_table':str(p/'table.npy'),'node_ids':nodes,'compensation_columns':cols,'target_evm_db':-57.7}),('export_config.json',{'implementation':parent,'error_table':str(p/'table.npy'),'synthesis_result':str(p/'synthesis.json')})]:
  (p/filename).write_text(json.dumps(config,indent=2)+'\n')
