"""Inspect complete output-adder structure and which columns feed output."""
import importlib.util
from pathlib import Path
p=Path('/home/guoliang/multiplier/experiments/3/candidate_g0003_0010/fused_low.py')
s=importlib.util.spec_from_file_location('t',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class Inspect(m.Candidate):
 def _build_outputs(self):
  for col, bucket in enumerate(self._columns):
   print(col,[(n,self.nodes[n].kind) for n in bucket])
  super()._build_outputs()
Inspect()._build_circuit()
