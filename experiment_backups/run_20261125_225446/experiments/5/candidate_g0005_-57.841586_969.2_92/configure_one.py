import json
from pathlib import Path
r=Path('/home/guoliang/multiplier/experiments/5/candidate_g0005_0004');p=r/'s41_42_one';p.mkdir(exist_ok=True)
slots=[[4,1],[4,2]];nodes=[119,110,2,179];cols=[4]
cfg={'implementation':str(r/'parent.py'),'stimulus_file':'/home/guoliang/multiplier/stimulus.npy','removed_slots':slots,'node_ids':nodes}
for f,v in [('screen.json',cfg),('table_config.json',{**cfg,'compensation_columns':cols}),('synthesis_config.json',{'implementation':str(r/'parent.py'),'error_table':str(p/'table.npy'),'node_ids':nodes,'compensation_columns':cols,'target_evm_db':-57.7,'max_gates':2}),('export_config.json',{'implementation':str(r/'parent.py'),'error_table':str(p/'table.npy'),'synthesis_result':str(p/'synthesis.json')})]: (p/f).write_text(json.dumps(v,indent=2)+'\n')
