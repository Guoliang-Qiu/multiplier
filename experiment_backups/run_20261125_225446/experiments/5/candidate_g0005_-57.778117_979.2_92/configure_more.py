"""Create a second, three-slot deletion trial using the retained low-column signals."""
import json
from pathlib import Path
root = Path('/home/guoliang/multiplier/experiments/5/candidate_g0005_0002')
for name, nodes in [('three_simple', [152, 538]), ('three_shared', [466, 405])]:
    folder = root / name
    folder.mkdir(exist_ok=True)
    cfg = {'implementation': str(root / 'parent.py'), 'stimulus_file': '/home/guoliang/multiplier/stimulus.npy', 'removed_slots': [[4, 0], [4, 2], [4, 3]], 'node_ids': nodes, 'compensation_columns': [4, 5]}
    (folder / 'screen.json').write_text(json.dumps({k: cfg[k] for k in ('implementation', 'stimulus_file', 'removed_slots', 'node_ids')}, indent=2))
    (folder / 'table_config.json').write_text(json.dumps(cfg, indent=2))
    (folder / 'synthesis_config.json').write_text(json.dumps({'implementation': cfg['implementation'], 'error_table': str(folder / 'table.npy'), 'node_ids': nodes, 'compensation_columns': [4, 5], 'target_evm_db': -57.75, 'max_gates': 2}, indent=2))
    (folder / 'export_config.json').write_text(json.dumps({'implementation': cfg['implementation'], 'error_table': str(folder / 'table.npy'), 'synthesis_result': str(folder / 'synthesis.json')}, indent=2))
