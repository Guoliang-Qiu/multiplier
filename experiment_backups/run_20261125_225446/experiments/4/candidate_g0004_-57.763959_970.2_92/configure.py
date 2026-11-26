import json
from pathlib import Path
base=Path('/home/guoliang/multiplier/experiments/4/candidate_g0004_0008')
parent=str(base/'parent.py'); stimulus='/home/guoliang/multiplier/stimulus.npy'
trials={'none':[], 'a0':[2], 'factor':[179], 'both':[2,179], 'slot':[230]}
for name,nodes in trials.items():
 d=base/('trial_c4p2_'+name); d.mkdir(exist_ok=True)
 config={'implementation':parent,'stimulus_file':stimulus,'removed_slots':[[4,2]],'node_ids':nodes}
 (d/'screen.json').write_text(json.dumps(config,indent=2)+'\n')
print('Created',len(trials),'screen configurations')
