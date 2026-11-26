import json
from pathlib import Path
base=Path('/home/guoliang/multiplier/experiments/1/candidate_g0001_0003')
parent=str(base/'parent.py'); stim='/home/guoliang/multiplier/stimulus.npy'
trials={
 'col4_compact': ([[4,0],[4,2]],[11,12,5,29,30,24],[4,5]),
 'col4_strong': ([[4,0],[4,2]],[152,538],[4,5]),
 'col4_shared': ([[4,0],[4,2]],[11,12,5,29,30,24,25,31],[4,5]),
 'col5_compact': ([[5,6]],[11,12,5,6],[5]),
 'col5_strong': ([[5,6]],[667],[5]),
 'pair_sparse': ([[4,0],[5,6]],[152,667],[4]),
 'col4_single': ([[4,0]],[152],[4]),
 'col4_other': ([[4,2]],[538],[4]),
 'col4_weak': ([[4,4]],[405],[4]),
 'col4_triple': ([[4,0],[4,2],[4,4]],[152,538,405],[4,5]),
 'col4_pair_other': ([[4,2],[4,4]],[538,405],[4]),
 'col4_pair_constant': ([[4,2],[4,3]],[538,152],[4]),
}
for name,(slots,nodes,columns) in trials.items():
 path=base/name; path.mkdir(exist_ok=True)
 config={'implementation':parent,'stimulus_file':stim,'removed_slots':slots,'node_ids':nodes}
 (path/'screen.json').write_text(json.dumps(config,indent=2)+'\n')
 (path/'table_config.json').write_text(json.dumps({**config,'compensation_columns':columns},indent=2)+'\n')
 (path/'synth_config.json').write_text(json.dumps({'implementation':parent,'error_table':str(path/'table.npy'),'node_ids':nodes,'compensation_columns':columns,'target_evm_db':-57.7},indent=2)+'\n')
 (path/'export_config.json').write_text(json.dumps({'implementation':parent,'error_table':str(path/'table.npy'),'synthesis_result':str(path/'synthesis.json')},indent=2)+'\n')
