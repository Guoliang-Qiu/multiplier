"""Generate strictly workload-backed CLI configurations, one directory per trial."""
import json
from pathlib import Path
root=Path('/home/guoliang/multiplier/experiments/2/candidate_g0002_0007')
parent=str(root/'parent.py')
stim='/home/guoliang/multiplier/stimulus.npy'
trials={
 'a_shared': ([[4,3],[4,4]],[504],[5]),
 'b_retained': ([[4,3],[4,4]],[555],[5]),
 'c_boundary': ([[4,3],[4,4]],[435,448],[5]),
 'd_pair': ([[4,3],[4,4]],[414,415],[5]),
 'e_compact': ([[5,6],[4,4]],[416],[5]),
 'f_both': ([[4,3],[4,4]],[504,555],[4,5]),
 'g_shared': ([[4,3],[4,4]],[504,435],[5]),
 'h_direct': ([[4,3],[4,4]],[416],[5]),
 'i_two_cols': ([[4,3],[4,4]],[555],[4,5]),
 'j_three': ([[4,2],[4,3],[4,4]],[230,555],[4,5]),
 'k_three': ([[4,1],[4,3],[4,4]],[720,555],[4,5]),
}
for name,(slots,nodes,columns) in trials.items():
    directory=root/name
    directory.mkdir(exist_ok=True)
    cfg={'implementation':parent,'stimulus_file':stim,'removed_slots':slots,'node_ids':nodes}
    for file, extra in [('screen.json',{}),('table_config.json',{'compensation_columns':columns}),('synth_config.json',{'implementation':parent,'error_table':str(directory/'table.npy'),'node_ids':nodes,'compensation_columns':columns,'target_evm_db':-57.62}),('export_config.json',{'implementation':parent,'error_table':str(directory/'table.npy'),'synthesis_result':str(directory/'synthesis.json')})]:
        (directory/file).write_text(json.dumps(extra if file in ('synth_config.json','export_config.json') else {**cfg,**extra},indent=2)+'\n')
