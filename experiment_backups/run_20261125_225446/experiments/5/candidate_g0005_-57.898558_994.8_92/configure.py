"""Create independent CLI configurations for low-column deletion observations."""
import json
from pathlib import Path
root=Path('/home/guoliang/multiplier/experiments/5/candidate_g0005_0008')
parent=str(root/'parent.py'); stimulus='/home/guoliang/multiplier/stimulus.npy'
trials={
 'single_inputs': ([[4,1]],[4,22],[4]),
 'single_shared': ([[4,1]],[73,76],[4]),
 'single_exact': ([[4,1]],[90],[4]),
 'pair_inputs': ([[4,0],[4,1]],[4,5,22,23],[4,5]),
 'pair_digit': ([[4,0],[4,1]],[11,43,73,76],[4,5]),
 'pair_direct': ([[4,0],[4,1]],[65,90],[4,5]),
 'single_other': ([[5,1]],[5,22],[5]),
}
for label,(slots,nodes,cols) in trials.items():
 d=root/label; d.mkdir(exist_ok=True)
 screen={'implementation':parent,'stimulus_file':stimulus,'removed_slots':slots,'node_ids':nodes}
 (d/'screen.json').write_text(json.dumps(screen,indent=2)+'\n')
 (d/'table_config.json').write_text(json.dumps({**screen,'compensation_columns':cols},indent=2)+'\n')
 (d/'synth_config.json').write_text(json.dumps({'implementation':parent,'error_table':str(d/'table.npy'),'node_ids':nodes,'compensation_columns':cols,'target_evm_db':-57.75},indent=2)+'\n')
 (d/'export_config.json').write_text(json.dumps({'implementation':parent,'error_table':str(d/'table.npy'),'synthesis_result':str(d/'synth.json')},indent=2)+'\n')
