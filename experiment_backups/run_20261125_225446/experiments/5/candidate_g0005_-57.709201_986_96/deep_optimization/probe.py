"""Inspect weighted column contents at each construction boundary."""
import importlib.util
import sys
sys.path.insert(0, '/home/guoliang/open_question_solver')
p = sys.argv[1]
spec = importlib.util.spec_from_file_location('probe', p)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
class Probe(m.Candidate):
    def _compress_columns(self):
        print('pre', self.partial_product_count)
        for i, col in enumerate(self._columns):
            print(i, len(col), [self.nodes[j].kind for j in col])
        super()._compress_columns()
        print('post',[(i,len(col)) for i,col in enumerate(self._columns)])
c=Probe()._build_circuit()
print(c.gatecost())
