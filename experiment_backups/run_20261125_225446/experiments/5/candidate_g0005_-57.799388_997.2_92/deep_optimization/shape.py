"""Inspect actual partial-product and compressed-column shapes."""
import importlib.util
import sys
from pathlib import Path
sys.path.insert(0, '/home/guoliang/open_question_solver')
p = Path('/home/guoliang/multiplier/experiments/5/candidate_g0005_0000/deep_optimization/general_v1.py')
s = importlib.util.spec_from_file_location('trial', p)
m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
class Shape(m.Candidate):
    def _product_columns(self,*args):
        cols=super()._product_columns(*args)
        print('before',[(i,len(b), [(j,self.nodes[x].kind,x) for j,x in enumerate(b)] if i in (4,5,6) else []) for i,b in enumerate(cols)])
        return cols
    def _compress_columns(self):
        super()._compress_columns()
        print('after',[(i,[('ZERO' if x==self._zero else 'ONE' if x==self._one else self.nodes[x].kind) for x in b]) for i,b in enumerate(self._columns)])
Shape()._build_circuit()
