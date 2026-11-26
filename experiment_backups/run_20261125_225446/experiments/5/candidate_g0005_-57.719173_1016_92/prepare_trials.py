"""Write trial configs using the immutable parent and external stimulus."""
from pathlib import Path
import json
root=Path('/home/guoliang/multiplier/experiments/5/candidate_g0005_0007')
parent=str(root/'parent.py'); stimulus='/home/guoliang/multiplier/stimulus.npy'
trials={
 'single_signal': ([[4,0]],[91],[4]),
 'single_factors': ([[4,0]],[89,90],[4]),
 'pair_compact': ([[4,0],[4,1]],[91,149],[4,5]),
 'pair_shared': ([[4,0],[4,1]],[89,90,149],[4,5]),
 'pair_observe_input': ([[4,0],[4,1]],[2,3,11,12],[4,5]),
 'pair_onebit': ([[4,0],[4,1]],[91,149],[5]),
 'pair_onebit_shared': ([[4,0],[4,1]],[89,90,149],[5]),
 'single_five': ([[5,0]],[94],[5]),
 'triple_onebit': ([[4,0],[4,1],[4,2]],[91,149,228],[5]),
 'triple_twobit': ([[4,0],[4,1],[4,2]],[91,149,228],[4,5]),
}
for name,(slots,nodes,cols) in trials.items():
 d=root/name; d.mkdir(exist_ok=True)
 base=dict(implementation=parent,stimulus_file=stimulus,removed_slots=slots,node_ids=nodes)
 for filename,data in [('screen.json',base),('table_config.json',dict(base,compensation_columns=cols)),('synthesis_config.json',dict(implementation=parent,error_table=str(d/'table.npy'),node_ids=nodes,compensation_columns=cols,target_evm_db=-57.7)),('export_config.json',dict(implementation=parent,error_table=str(d/'table.npy'),synthesis_result=str(d/'synthesis.json')))]:
  (d/filename).write_text(json.dumps(data,indent=2)+'\n')
