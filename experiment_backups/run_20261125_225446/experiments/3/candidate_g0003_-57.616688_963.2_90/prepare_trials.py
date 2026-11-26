import json
from pathlib import Path
root=Path('/home/guoliang/multiplier/experiments/3/candidate_g0003_0002')
p=str(root/'parent.py'); stimulus='/home/guoliang/multiplier/stimulus.npy'
trials={
 'buffer_pair_compact':([[5,6],[5,7]],[416,230,689],[5,6]),
 'buffer_pair_strong':([[5,6],[5,7]],[414,415,230,689],[5,6]),
 'buffer_pair_direct':([[5,6],[5,7]],[416,722],[5,6]),
 'col5_pair_compact':([[5,0],[5,6]],[92,93,416],[5,6]),
 'col5_pair_direct':([[5,0],[5,6]],[94,416],[5,6]),
 'col4_single_compact':([[4,0]],[119,153],[4]),
 'col4_single_direct':([[4,0]],[720],[4]),
}
for name,(slots,nodes,cols) in trials.items():
 d=root/name; d.mkdir(exist_ok=True)
 cfg={'implementation':p,'stimulus_file':stimulus,'removed_slots':slots,'node_ids':nodes}
 (d/'screen.json').write_text(json.dumps(cfg,indent=2)+'\n')
 (d/'table_config.json').write_text(json.dumps({**cfg,'compensation_columns':cols},indent=2)+'\n')
 (d/'synth_config.json').write_text(json.dumps({'implementation':p,'error_table':str(d/'table.npy'),'node_ids':nodes,'compensation_columns':cols,'target_evm_db':-57.61},indent=2)+'\n')
 (d/'export_config.json').write_text(json.dumps({'implementation':p,'error_table':str(d/'table.npy'),'synthesis_result':str(d/'synthesis.json')},indent=2)+'\n')
