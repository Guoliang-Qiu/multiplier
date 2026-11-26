import json
from pathlib import Path
root=Path('/home/guoliang/multiplier/experiments/4/candidate_g0004_0002')
parent=str(root/'parent.py'); stimulus='/home/guoliang/multiplier/stimulus.npy'
trials=[('small',[ [4,1] ],[12,13],[4]),('shared',[[4,1]],[110,116],[4]),('direct',[[4,1]],[152],[4]),('medium',[[4,1]],[110,116,4],[4]),('pair',[[4,1],[4,2]],[110,116,424,430],[4,5]),('pair_small',[[4,1],[4,2]],[12,13,30,31],[4,5]),('pair_direct',[[4,1],[4,2]],[152,466],[4,5]),('one_two',[[4,2]],[424,430,22],[4,5]),('one_direct',[[4,2]],[466],[4]),('small_wide',[[4,1]],[12,13],[4,5]),('pair_wide',[[4,1],[4,2]],[110,116,424,430],[4,5,6]),('pair_one',[[4,1],[4,2]],[152,466],[4]),('pair_one_shared',[[4,1],[4,2]],[110,116,424,430],[4]),('triple_direct',[[4,1],[4,2],[4,3]],[152,466],[4,5]),('triple_compact',[[4,1],[4,2],[4,3]],[12,13,30,31],[4,5]),('quad_zero',[[4,0],[4,1],[4,2],[4,3]],[152,466],[4,5]),('quad_real',[[4,1],[4,2],[4,3],[4,4]],[152,466,405],[4,5,6])]
for name,slots,nodes,columns in trials:
 d=root/name;d.mkdir(exist_ok=True)
 config={'implementation':parent,'stimulus_file':stimulus,'removed_slots':slots,'node_ids':nodes}
 (d/'screen.json').write_text(json.dumps(config,indent=2)+'\n')
 (d/'table_config.json').write_text(json.dumps({**config,'compensation_columns':columns},indent=2)+'\n')
 (d/'synth_config.json').write_text(json.dumps({'implementation':parent,'error_table':str(d/'table.npy'),'node_ids':nodes,'compensation_columns':columns,'target_evm_db':-57.65},indent=2)+'\n')
 (d/'export_config.json').write_text(json.dumps({'implementation':parent,'error_table':str(d/'table.npy'),'synthesis_result':str(d/'synth.json')},indent=2)+'\n')
