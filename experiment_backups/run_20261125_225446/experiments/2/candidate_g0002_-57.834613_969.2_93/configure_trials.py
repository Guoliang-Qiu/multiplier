"""Generate reproducible conditional-compensation trial configuration files."""
import json
from pathlib import Path
ROOT = Path('/home/guoliang/multiplier')
BASE = ROOT / 'experiments/2/candidate_g0002_0005'
IMPLEMENTATION = str(BASE / 'parent.py')
STIMULUS = str(ROOT / 'stimulus.npy')
SLOTS = [[5, 0], [5, 3]]
TRIALS = {
    'shared_buses': (SLOTS, [11, 29], [5, 5]),
    'shared_cones': (SLOTS, [92, 415], [5, 5]),
    'branch_cones': (SLOTS, [93, 416], [5, 5]),
    'four_buses': (SLOTS, [11, 29, 12, 30], [5, 5]),
    'single_one': ([[5, 0]], [92, 93], [5]),
    'single_two': ([[5, 3]], [415, 416], [5]),
    'pair_four': ([[4, 2], [4, 5]], [229, 552], [4, 4]),
}
for name, (slots, nodes, columns) in TRIALS.items():
    directory = BASE / name
    directory.mkdir(parents=True, exist_ok=True)
    screen = dict(implementation=IMPLEMENTATION, stimulus_file=STIMULUS,
                  removed_slots=slots, node_ids=nodes)
    (directory / 'screen.json').write_text(json.dumps(screen, indent=2) + '\n')
    (directory / 'table_config.json').write_text(json.dumps(
        dict(screen, compensation_columns=columns), indent=2) + '\n')
    (directory / 'synth_config.json').write_text(json.dumps(dict(
        implementation=IMPLEMENTATION, error_table=str(directory / 'table.npy'),
        node_ids=nodes, compensation_columns=columns,
        target_evm_db=-57.65, max_gates=2), indent=2) + '\n')
    (directory / 'export_config.json').write_text(json.dumps(dict(
        implementation=IMPLEMENTATION, error_table=str(directory / 'table.npy'),
        synthesis_result=str(directory / 'synthesis.json')), indent=2) + '\n')
