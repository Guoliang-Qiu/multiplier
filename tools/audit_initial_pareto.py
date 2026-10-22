"""Audit every initial solution using unchanged authoritative evaluation."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'tools' / 'initial_pareto_audit.json'


def main():
    rows = []
    env = dict(os.environ, TAP2_COPIES='8', OPENBLAS_NUM_THREADS='1')
    for path in sorted((ROOT / 'initial_solutions').glob('*.py')):
        row = {'file': str(path.relative_to(ROOT)),
               'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
        try:
            for tool in ('gate_cost.py', 'eval.py'):
                result = subprocess.run([sys.executable, tool, row['file']],
                    cwd=ROOT, env=env, capture_output=True, text=True, timeout=900)
                if result.returncode:
                    raise RuntimeError(result.stderr[-2000:])
                row.update(json.loads(result.stdout))
        except Exception as error:
            row['error'] = str(error)
        rows.append(row)
        OUT.write_text(json.dumps(rows, indent=2))
        print(row['file'], row.get('gate_cost'), row.get('evm_db'),
              row.get('error', ''), flush=True)
    good = [r for r in rows if 'evm_db' in r and 'error' not in r]
    for r in good:
        r['dominated_by'] = [s['file'] for s in good
            if s['gate_cost'] <= r['gate_cost'] and s['evm_db'] <= r['evm_db']
            and (s['gate_cost'] < r['gate_cost'] or s['evm_db'] < r['evm_db'])]
    OUT.write_text(json.dumps(rows, indent=2))
    lines = ['# Initial-solutions Pareto audit', '',
        'Scope: every Python candidate in `initial_solutions/`. '
        'Unmodified `gate_cost.py` and `eval.py`; TAP2_COPIES=8, seed 42. '
        'Both weighted cost and EVM dB are minimized. Equal points are co-frontier.', '',
        '| Candidate | Cost | EVM dB | Frontier |', '|---|---:|---:|:---:|']
    for r in sorted(good, key=lambda r:(r['gate_cost'], r['evm_db'])):
        lines.append(f"| {Path(r['file']).name} | {r['gate_cost']} | {r['evm_db']:.9f} | "
                     f"{'yes' if not r['dominated_by'] else 'no'} |")
    lines += ['', 'Errors:', *[f"- {r['file']}: {r['error']}" for r in rows if 'error' in r]]
    (ROOT / 'tools' / 'INITIAL_PARETO_AUDIT.md').write_text('\n'.join(lines)+'\n')


if __name__ == '__main__':
    main()
