"""Prepare independent configurations for screening original column-four deletions."""
import json
from pathlib import Path
root=Path('/home/guoliang/multiplier/experiments/5/candidate_g0005_0001')
parent=str(root/'parent.py'); stimulus='/home/guoliang/multiplier/stimulus.npy'
trials={
 'pair_const': ([[4,0],[4,3]], [], [4,5]),
 'pair_shared': ([[4,0],[4,3]], [11,29], [4,5]),
 'pair_recode': ([[4,0],[4,3]], [11,43,29,341], [4,5]),
 'single_shared': ([[4,0]], [11,6], [4]),
 'single_recode': ([[4,0]], [89], [4]),
 'pair_input': ([[4,0],[4,3]], [6,24], [4,5]),
}
for name,(slots,ids,comp) in trials.items():
 d=root/name; d.mkdir(exist_ok=True)
 conf={'implementation':parent,'stimulus_file':stimulus,'removed_slots':slots,'node_ids':ids}
 (d/'screen.json').write_text(json.dumps(conf,indent=2)+'\n')
 (d/'table_config.json').write_text(json.dumps({**conf,'compensation_columns':comp},indent=2)+'\n')
 (d/'synth_config.json').write_text(json.dumps({'implementation':parent,'error_table':str(d/'table.npy'),'node_ids':ids,'compensation_columns':comp,'target_evm_db':-57.72},indent=2)+'\n')
 (d/'export_config.json').write_text(json.dumps({'implementation':parent,'error_table':str(d/'table.npy'),'synthesis_result':str(d/'synthesis.json')},indent=2)+'\n')
print('Prepared',list(trials))
