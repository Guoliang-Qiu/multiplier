import json
from pathlib import Path
root=Path('/home/guoliang/multiplier/experiments/5/candidate_g0005_0004')
parent=str(root/'parent.py'); stimulus='/home/guoliang/multiplier/stimulus.npy'
trials={
 's51_compact': ([(5,1)],[110,119,5],[5]),
 's51_strong': ([(5,1)],[110,119,165,4,5],[5]),
 's50_compact': ([(5,0)],[11,55,43],[5]),
 's50_strong': ([(5,0)],[11,55,43,59],[5]),
 's41_compact': ([(4,1)],[119,110],[4]),
 's41_strong': ([(4,1)],[119,110,123],[4]),
 's40_compact': ([(4,0)],[11,55,43],[4]),
 's40_strong': ([(4,0)],[11,55,43,339],[4]),
}
for name,(slots,nodes,columns) in trials.items():
 p=root/name;p.mkdir(exist_ok=True)
 cfg={'implementation':parent,'stimulus_file':stimulus,'removed_slots':slots,'node_ids':nodes}
 (p/'screen.json').write_text(json.dumps(cfg,indent=2)+'\n')
 (p/'table_config.json').write_text(json.dumps({**cfg,'compensation_columns':columns},indent=2)+'\n')
 (p/'synthesis_config.json').write_text(json.dumps({'implementation':parent,'error_table':str(p/'table.npy'),'node_ids':nodes,'compensation_columns':columns,'target_evm_db':-57.7,'max_gates':5},indent=2)+'\n')
 (p/'export_config.json').write_text(json.dumps({'implementation':parent,'error_table':str(p/'table.npy'),'synthesis_result':str(p/'synthesis.json')},indent=2)+'\n')
