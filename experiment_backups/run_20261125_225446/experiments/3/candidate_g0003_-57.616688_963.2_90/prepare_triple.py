import json
from pathlib import Path
r=Path('/home/guoliang/multiplier/experiments/3/candidate_g0003_0002')
for name, ids, cols in [('triple_shared',[94,416,722],[5,6]),('triple_logic',[92,93,416,722],[5,6])]:
 d=r/name;d.mkdir(exist_ok=True)
 base={'implementation':str(r/'parent.py'),'stimulus_file':'/home/guoliang/multiplier/stimulus.npy','removed_slots':[[5,0],[5,6],[5,7]],'node_ids':ids}
 (d/'screen.json').write_text(json.dumps(base,indent=2)+'\n')
 (d/'table_config.json').write_text(json.dumps({**base,'compensation_columns':cols},indent=2)+'\n')
 (d/'synth_config.json').write_text(json.dumps({'implementation':base['implementation'],'error_table':str(d/'table.npy'),'node_ids':ids,'compensation_columns':cols,'target_evm_db':-57.61,'max_gates':4},indent=2)+'\n')
 (d/'export_config.json').write_text(json.dumps({'implementation':base['implementation'],'error_table':str(d/'table.npy'),'synthesis_result':str(d/'synthesis.json')},indent=2)+'\n')
