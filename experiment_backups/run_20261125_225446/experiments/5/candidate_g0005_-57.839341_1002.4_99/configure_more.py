"""Additional compact partial-product trials with shared control or row signals."""
import json
from pathlib import Path
root=Path('/home/guoliang/multiplier/experiments/5/candidate_g0005_0001')
parent=str(root/'parent.py'); stimulus='/home/guoliang/multiplier/stimulus.npy'
trials={
 'pair_rows5': ([[4,0],[4,3]], [89,387], [5]),
 'pair_rows45': ([[4,0],[4,3]], [89,387], [4,5]),
 'pair_shared5': ([[4,0],[4,3]], [11,29], [5]),
 'pair_recode45': ([[4,0],[4,3]], [11,43,29,341], [4,5]),
}
for name,(slots,ids,comp) in trials.items():
 d=root/name; d.mkdir(exist_ok=True)
 conf={'implementation':parent,'stimulus_file':stimulus,'removed_slots':slots,'node_ids':ids}
 for file,content in [('screen.json',conf),('table_config.json',{**conf,'compensation_columns':comp}),('synth_config.json',{'implementation':parent,'error_table':str(d/'table.npy'),'node_ids':ids,'compensation_columns':comp,'target_evm_db':-57.72,'max_gates':3}),('export_config.json',{'implementation':parent,'error_table':str(d/'table.npy'),'synthesis_result':str(d/'synthesis.json')})]:
  (d/file).write_text(json.dumps(content,indent=2)+'\n')
print('Prepared',list(trials))
