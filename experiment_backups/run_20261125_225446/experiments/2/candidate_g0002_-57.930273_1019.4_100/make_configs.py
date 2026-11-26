import json
from pathlib import Path
root=Path('/home/guoliang/multiplier/experiments/2/candidate_g0002_0006')
implementation=str(root/'parent.py')
stimulus='/home/guoliang/multiplier/stimulus.npy'
trials={
 'd4a_direct': ([[4,1]],[152],[4]),
 'd4a_factors': ([[4,1]],[150,151],[4]),
 'd4a_shared': ([[4,1]],[110,4,5],[4]),
 'd5mux_direct': ([[5,1]],[163],[5]),
 'd5mux_compact': ([[5,1]],[110,116,162,5],[5]),
 'd5mux_full': ([[5,1]],[110,116,162,5,4],[5]),
 'd5pair_direct': ([[5,1],[5,4]],[163,479],[5,6]),
 'd5pair_compact': ([[5,1],[5,4]],[110,116,162,426,432,478],[5,6]),
}
for name,(removed,nodes,cols) in trials.items():
 p=root/name;p.mkdir(exist_ok=True)
 base=dict(implementation=implementation,stimulus_file=stimulus,removed_slots=removed,node_ids=nodes)
 (p/'screen.json').write_text(json.dumps(base,indent=2)+'\n')
 (p/'table_config.json').write_text(json.dumps(dict(base,compensation_columns=cols),indent=2)+'\n')
 (p/'synth_config.json').write_text(json.dumps(dict(implementation=implementation,error_table=str(p/'table.npy'),node_ids=nodes,compensation_columns=cols,target_evm_db=-57.8),indent=2)+'\n')
 (p/'export_config.json').write_text(json.dumps(dict(implementation=implementation,error_table=str(p/'table.npy'),synthesis_result=str(p/'synth.json')),indent=2)+'\n')
