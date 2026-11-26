import json
from pathlib import Path
root=Path('/home/guoliang/multiplier/experiments/2/candidate_g0002_0002');parent=str(root/'parent.py');stimulus='/home/guoliang/multiplier/stimulus.npy'
for name,slots,nodes,cols in [('ab_first',[[4,0]],[11,2,12],[4]),('ab_second',[[4,1]],[110,119,2],[4]),('cd_first',[[4,3]],[29,20,30],[4]),('cd_last',[[4,5]],[20,31,32],[4]),('pair_exact',[[4,0],[4,3]],[685,414],[4,5])]:
 p=root/name;p.mkdir(exist_ok=True); cfg=dict(implementation=parent,stimulus_file=stimulus,removed_slots=slots,node_ids=nodes)
 for file,d in [('screen.json',cfg),('table_config.json',{**cfg,'compensation_columns':cols}),('synthesis_config.json',dict(implementation=parent,error_table=str(p/'table.npy'),node_ids=nodes,compensation_columns=cols,target_evm_db=-57.65,max_gates=2)),('export_config.json',dict(implementation=parent,error_table=str(p/'table.npy'),synthesis_result=str(p/'synthesis.json')))]: (p/file).write_text(json.dumps(d,indent=2)+'\n')
