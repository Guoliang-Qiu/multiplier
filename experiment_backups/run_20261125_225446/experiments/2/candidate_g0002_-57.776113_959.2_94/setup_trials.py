import json
from pathlib import Path
root=Path('/home/guoliang/multiplier/experiments/2/candidate_g0002_0002')
parent=str(root/'parent.py'); stimulus='/home/guoliang/multiplier/stimulus.npy'
trials=[('compact',[[4,0],[4,3]],[11,29],[4]),('shared',[[4,0],[4,3]],[89,412],[4]),('rich',[[4,0],[4,3]],[11,12,29,30],[4]),('single',[[4,3]],[20,29],[4])]
for name,slots,nodes,cols in trials:
 p=root/name;p.mkdir(exist_ok=True)
 cfg={'implementation':parent,'stimulus_file':stimulus,'removed_slots':slots,'node_ids':nodes}
 (p/'screen.json').write_text(json.dumps(cfg,indent=2)+'\n')
 (p/'table_config.json').write_text(json.dumps({**cfg,'compensation_columns':cols},indent=2)+'\n')
 (p/'synthesis_config.json').write_text(json.dumps({'implementation':parent,'error_table':str(p/'table.npy'),'node_ids':nodes,'compensation_columns':cols,'target_evm_db':-57.65,'max_gates':2},indent=2)+'\n')
 (p/'export_config.json').write_text(json.dumps({'implementation':parent,'error_table':str(p/'table.npy'),'synthesis_result':str(p/'synthesis.json')},indent=2)+'\n')
