"""Count exact compressor shortcut opportunities after B's changed columns."""
import importlib.util,sys
from pathlib import Path
p=Path('/home/guoliang/multiplier/experiments/3/candidate_g0003_0010/fused_low.py')
s=importlib.util.spec_from_file_location('t',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class Inspect(m.Candidate):
 def _add3(self,x,y,z):
  if len({x,y,z})<3:
   print('repeated add3', x,y,z)
  for a,b in ((x,y),(x,z),(y,z)):
   if self.nodes[a].kind=='NOT' and self.nodes[a].inputs[0]==b or self.nodes[b].kind=='NOT' and self.nodes[b].inputs[0]==a:
    print('complement add3',x,y,z)
  return super()._add3(x,y,z)
Inspect()._build_circuit()
