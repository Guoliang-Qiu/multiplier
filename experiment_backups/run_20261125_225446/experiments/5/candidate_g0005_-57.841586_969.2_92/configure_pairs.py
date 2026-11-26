import json
from pathlib import Path
r=Path('/home/guoliang/multiplier/experiments/5/candidate_g0005_0004')
trials={
 's41_42_compact': ([(4,1),(4,2)],[119,110,2,179],[4,4]),
 's41_42_small': ([(4,1),(4,2)],[119,110,2],[4,4]),
 's41_40_compact': ([(4,1),(4,0)],[119,110,11,55],[4,4]),
 's41_40_small': ([(4,1),(4,0)],[119,110,11],[4,4]),
}
for name,(slots,nodes,columns) in trials.items():
 p=r/name;p.mkdir(exist_ok=True)
 cfg={'implementation':str(r/'parent.py'),'stimulus_file':'/home/guoliang/multiplier/stimulus.npy','removed_slots':slots,'node_ids':nodes}
 for f,values in [('screen.json',cfg),('table_config.json',{**cfg,'compensation_columns':columns}),('synthesis_config.json',{'implementation':str(r/'parent.py'),'error_table':str(p/'table.npy'),'node_ids':nodes,'compensation_columns':columns,'target_evm_db':-57.7,'max_gates':7}),('export_config.json',{'implementation':str(r/'parent.py'),'error_table':str(p/'table.npy'),'synthesis_result':str(p/'synthesis.json')})]:
  (p/f).write_text(json.dumps(values,indent=2)+'\n')
