"""Generate isolated conditional-compensation trial configs for the parent."""
import json
from pathlib import Path
root = Path('/home/guoliang/multiplier/experiments/5/candidate_g0005_0002')
base = {'implementation': str(root / 'parent.py'), 'stimulus_file': '/home/guoliang/multiplier/stimulus.npy', 'removed_slots': [[4, 0], [4, 2]]}
trials = {
    'shared': ([466, 405], [4, 5]),
    'compact': ([152, 538], [4, 5]),
    'mixed': ([152, 405], [4, 5]),
}
for name, (nodes, cols) in trials.items():
    folder = root / name
    folder.mkdir(exist_ok=True)
    cfg = {**base, 'node_ids': nodes, 'compensation_columns': cols}
    (folder / 'screen.json').write_text(json.dumps({k: cfg[k] for k in ('implementation', 'stimulus_file', 'removed_slots', 'node_ids')}, indent=2))
    (folder / 'table_config.json').write_text(json.dumps(cfg, indent=2))
    (folder / 'synthesis_config.json').write_text(json.dumps({'implementation': cfg['implementation'], 'error_table': str(folder / 'table.npy'), 'node_ids': nodes, 'compensation_columns': cols, 'target_evm_db': -57.75}, indent=2))
    (folder / 'export_config.json').write_text(json.dumps({'implementation': cfg['implementation'], 'error_table': str(folder / 'table.npy'), 'synthesis_result': str(folder / 'synthesis.json')}, indent=2))
