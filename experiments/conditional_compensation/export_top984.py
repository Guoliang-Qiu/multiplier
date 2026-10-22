"""Emit an independent source candidate with the proven k=2 top-row rewrite."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
import numpy as np
from multiplier.initial_solutions import candidate_dist_top_reuse988 as base


def main():
    root=Path(__file__).resolve().parents[2]
    src=(root/'initial_solutions/candidate_dist_top_reuse988.py').read_text()
    assert src.count('for k in range(3, 9):')==1
    text=src.replace('for k in range(3, 9):','for k in range(2, 9):')
    text=text.replace('"""Standalone three-stage candidate; generic arithmetic is inherited from tap2."""',
                      '"""984-cost exact top-row reuse, including the k=2 boundary term.\n\n'
                      'The k=0/1 terms have specialized correction semantics and are not rewritten.\n'
                      'Only tap2 is required; no candidate or experiment imports.\n"""')
    ns={'__name__':'top984'};exec(compile(text,'top984','exec'),ns)
    c=ns['build_circuit']();assert c.gatecost().total==984
    x=np.random.default_rng(984).integers(-256,256,(16384,4)).tolist()
    assert c.simulate_many(x)==base.build_circuit().simulate_many(x)
    (root/'initial_solutions/candidate_dist_top_reuse984.py').write_text(text)
    print('exported standalone 984; 16384/16384 raw outputs match')


if __name__=='__main__':main()
