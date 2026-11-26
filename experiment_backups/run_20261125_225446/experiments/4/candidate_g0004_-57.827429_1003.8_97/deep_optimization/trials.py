"""Source transformations and complete-circuit checks for gate experiments."""
import importlib.util
from pathlib import Path
import numpy as np
ROOT = Path('/home/guoliang/multiplier')
DIR = ROOT/'experiments/4/candidate_g0004_0007/deep_optimization'
src = (ROOT/'experiments/4/candidate_g0004_0007/partial_product_candidate.py').read_text()
def load(path):
    spec = importlib.util.spec_from_file_location('candidate_trial', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.build_circuit()
samples = np.load(ROOT/'stimulus.npy', mmap_mode='r')
reference = load(ROOT/'experiments/4/candidate_g0004_0007/partial_product_candidate.py')
inputs = samples[::101].tolist()
raw = reference.simulate_many(inputs)
print('reference',reference.gatecost().total,reference.partial_product_count,flush=True)
def check(name,text):
    path = DIR/(name+'.py'); path.write_text(text)
    try:
        c=load(path)
        cost=c.gatecost().total
        vals=c.simulate_many(inputs)
        count=sum(x!=y for x,y in zip(vals,raw))
        print(name,cost,c.partial_product_count,'sample mismatches',count,flush=True)
    except Exception as exc:
        print(name,type(exc).__name__,str(exc),flush=True)
if __name__=='__main__':
    check('xor_native',src.replace('return self._and(either, self._not(both))','return self._gate("XOR", a, b)'))
    check('xor_alt',src.replace('return self._and(either, self._not(both))','return self._or(self._and(a, self._not(b)), self._and(self._not(a), b))'))
    check('fa_mixed',src.replace('    def _one_product_columns(', '''    def _fa(self, a, b, cin):
        """Alternative exact adder: reuse two-input parity for sum and carry."""
        p = self._xor(a, b)
        return self._xor(p, cin), self._or(self._and(a, b), self._and(p, cin))

    def _one_product_columns('''))
    check('special_xor',src.replace('total = self._xor(b_or_ac, a_or_c)','total = self._gate("XOR", b_or_ac, a_or_c)'))
    # Structural source lookup avoids brittle absolute DAG node IDs when gates shift.
    structural = src.replace('        del columns[4][4]\n        del columns[4][2]\n        del columns[4][1]', '        g_0, g_2 = columns[4][1], columns[4][2]\n        del columns[4][4]\n        del columns[4][2]\n        del columns[4][1]').replace('        g_0 = 143','        # g_0 is captured above').replace('        g_2 = 216','        # g_2 is captured above')
    check('structural',structural)
    check('struct_native',structural.replace('return self._and(either, self._not(both))','return self._gate("XOR", a, b)'))
    check('struct_alt',structural.replace('return self._and(either, self._not(both))','return self._or(self._and(a, self._not(b)), self._and(self._not(a), b))'))
    check('struct_unbuffer',structural.replace("self.add('OR', g_2, zero)", 'g_2').replace("self.add('OR', g_0, zero)", 'g_0'))
    check('step0_neg',structural.replace('cell_neg = self._and(negative, self._or(generated_one, two))','cell_neg = negative if step == 0 else self._and(negative, self._or(generated_one, two))'))
    check('output_absorb',structural.replace('outputs.append(self._or(bucket[0], carry) if col <= 6 else self._xor(bucket[0], carry))','outputs.append(self._or_absorb(bucket[0], carry) if col <= 6 else self._xor(bucket[0], carry))'))
    check('special_xor_guard',structural.replace('total = self._xor(b_or_ac, a_or_c)','total = self._and(self._or(b_or_ac, a_or_c), self._not(carry))'))
    check('booth_p_factor',structural.replace('p = self._or(self._and(q[2 * step + 1], x_and), self._and(self._not(q[2 * step + 1]), m[1]))','p = self._or(self._and(q[2 * step + 1], x_and), self._and(self._not(q[2 * step + 1]), m[1]))'))
    # Because generated_one and two are mutually exclusive, a MUX_XOR can implement two branches.
    check('step0_a_mux',structural.replace('a = self._or(self._and(generated_one, get_xor(2)), self._and(two, p))','a = self._mux_xor(generated_one, get_xor(2), two, p, zero)'))
