import json
from pathlib import Path
r=Path('/home/guoliang/multiplier/experiments/2/candidate_g0002_0006');i=str(r/'parent.py');s='/home/guoliang/multiplier/stimulus.npy'
for name,removed,nodes,cols in [('d4pair_direct',[[4,1],[4,4]],[152,468],[4,5]),('d5pair_fused',[[5,1],[5,4]],[163,479],[5,5,6])]:
 p=r/name;p.mkdir(exist_ok=True)
 b=dict(implementation=i,stimulus_file=s,removed_slots=removed,node_ids=nodes)
 for n,v in {'screen.json':b,'table_config.json':dict(b,compensation_columns=cols),'synth_config.json':dict(implementation=i,error_table=str(p/'table.npy'),node_ids=nodes,compensation_columns=cols,target_evm_db=-57.8,max_gates=2),'export_config.json':dict(implementation=i,error_table=str(p/'table.npy'),synthesis_result=str(p/'synth.json'))}.items():
  (p/n).write_text(json.dumps(v,indent=2)+'\n')
