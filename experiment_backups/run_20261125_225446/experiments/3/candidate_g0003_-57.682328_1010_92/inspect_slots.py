"""Inspect B partial-product slots before compressor consumes their columns."""
import importlib.util
from pathlib import Path
p=Path('/home/guoliang/multiplier/experiments/3/candidate_g0003_0010/fused_low.py')
spec=importlib.util.spec_from_file_location('trial',p)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Inspect(m.Candidate):
    def _compress_columns(self):
        for col in range(3,9):
            print(col,[(i, self.nodes[n].kind, n) for i,n in enumerate(self._columns[col])])
        super()._compress_columns()
Inspect()._build_circuit()
