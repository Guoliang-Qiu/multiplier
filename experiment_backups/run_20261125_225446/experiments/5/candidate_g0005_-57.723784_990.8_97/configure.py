"""Generate scoped configs for independently tracked compensation experiments."""
import json
from pathlib import Path
root=Path('/home/guoliang/multiplier/experiments/5/candidate_g0005_0003')
implementation=str(root/'parent.py')
stimulus_file='/home/guoliang/multiplier/stimulus.npy'
trials={
 'col4_shared': ([[4,1],[4,4]], [101,399], [4,5]),
 'col4_strong': ([[4,1],[4,4]], [143,441], [4,5]),
 'col4_compact': ([[4,1],[4,4]], [11,29], [4,5]),
 'col4_one': ([[4,1],[4,4]], [143,441], [4]),
 'col4_one_compact': ([[4,1],[4,4]], [11,29], [4]),
 'col4_quad': ([[4,1],[4,2],[4,4],[4,5]], [143,441], [4,5]),
 'col4_quad_strong': ([[4,1],[4,2],[4,4],[4,5]], [143,216,441,514], [4,5,6]),
 'col4_triple': ([[4,1],[4,2],[4,4]], [143,441], [4,5]),
 'col4_triple_strong': ([[4,1],[4,2],[4,4]], [143,216,441], [4,5]),
 'col3_one': ([[3,0],[3,1]], [101,399], [3]),
 'col3_compact': ([[3,0],[3,1]], [101,399], [3,4]),
}
for name,(removed,node_ids,comp) in trials.items():
 d=root/name;d.mkdir(exist_ok=True)
 screen={'implementation':implementation,'stimulus_file':stimulus_file,'removed_slots':removed,'node_ids':node_ids}
 (d/'screen.json').write_text(json.dumps(screen,indent=2)+'\n')
 (d/'table_config.json').write_text(json.dumps({**screen,'compensation_columns':comp},indent=2)+'\n')
 (d/'synth_config.json').write_text(json.dumps({'implementation':implementation,'error_table':str(d/'table.npy'),'node_ids':node_ids,'compensation_columns':comp,'target_evm_db':-57.65},indent=2)+'\n')
 (d/'export_config.json').write_text(json.dumps({'implementation':implementation,'error_table':str(d/'table.npy'),'synthesis_result':str(d/'synthesis.json')},indent=2)+'\n')
