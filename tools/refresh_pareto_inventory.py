"""Refresh retained-file status without rerunning unchanged full evaluations."""
import json
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / 'tools/initial_pareto_audit.json'
rows = json.loads(path.read_text())
for row in rows:
    row['retained'] = (ROOT / row['file']).exists()
    if row['retained']:
        row['current_sha256'] = hashlib.sha256((ROOT / row['file']).read_bytes()).hexdigest()
    row['status'] = ('retained_frontier' if row['retained'] else
                     'removed_dominated' if row.get('dominated_by') else 'removed_duplicate')
path.write_text(json.dumps(rows, indent=2) + '\n')
lines = ['# Current initial-solutions Pareto frontier', '',
         'All values remeasured after migration to the current three-stage MultiplierCircuit.',
         '`TAP2_COPIES=8`, `OPENBLAS_NUM_THREADS=1`, seed 42; 1,050,624 cases per candidate.',
         'Lower weighted cost and more negative EVM are better. Equal points are deduplicated.', '',
         '| Candidate | Gate cost | EVM dB |', '|---|---:|---:|']
for row in sorted((r for r in rows if r['retained']), key=lambda r:r['gate_cost']):
    assert not row.get('dominated_by'), row['file']
    lines.append(f"| `{Path(row['file']).name}` | {row['gate_cost']} | {row['evm_db']:.9f} |")
lines += ['', 'The JSON audit retains full measurements and dominators of removed candidates.',
          'Candidate layouts use the joint `_product_columns(a,b,c,d,zero,one)` interface;',
          'compression and output construction are separate `_compress_columns()` / `_build_outputs()` stages.',
          '`candidate_support/staged.py` preserves the former absorption policy and layout helpers.',
          '`finish_columns(circuit, columns)` reuses the supplied layout instance, never a second setup.']
(ROOT / 'tools/INITIAL_PARETO_AUDIT.md').write_text('\n'.join(lines) + '\n')
