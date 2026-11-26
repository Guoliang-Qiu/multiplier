"""Local reproducible gate-level source variants and stimulus equality checks."""
from pathlib import Path
import importlib.util
import subprocess
import sys
import numpy as np
ROOT = Path('/home/guoliang/multiplier')
HERE = Path(__file__).resolve().parent
SOURCE = (HERE.parent / 'partial_product_candidate.py').read_text()
STIM = ROOT / 'stimulus.npy'
def variant(name, text):
    path = HERE / (name + '.py')
    path.write_text(text)
    result = subprocess.run([sys.executable, str(ROOT/'gate_cost.py'), str(path)], capture_output=True, text=True, check=True)
    print(name, result.stdout.strip(), flush=True)
    return path
def load(path):
    spec = importlib.util.spec_from_file_location('trial_'+path.stem, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.build_circuit()
g = SOURCE.replace('''        # X refers to nodes in the original pre-compression prefix.
        g_0 = 29
        g_1 = 30
        g_2 = zero
        g_3 = one
        g_4 = self._gate('OR', g_0, g_1)
        # Match the fixed insertion buffers used by the error table.
        columns[4].append(self.add('OR', g_4, zero))''', '''        # G(X) is d[0] | d[1]; eliminate an unnecessary OR-with-zero buffer.
        columns[4].append(self._or(d[0], d[1]))''')
assert g != SOURCE
variant('g_simplified',g)
native = g.replace('''    def _xor(self, a, b):
        both = self._and(a, b)
        either = self._or(a, b)
        return self._and(either, self._not(both))

''', '')
assert native != g
variant('native_xor', native)
last = g.replace('''                new = self._and(active, self._not(self._xor(q[7], m[k])))''', '''                new = self._or(self._and(pos, m[k]), self._and(neg, self._not(m[k])))''')
variant('last_row_original',last)
fa = g.replace('''    def _compress_columns(self):''', '''    def _fa(self, a, b, cin):
        """Exact parity and majority realization to test shared Booth XOR cones."""
        parity = self._xor(a, b)
        total = self._xor(parity, cin)
        carry = self._or(self._and(a, b), self._and(parity, cin))
        return total, carry

    def _compress_columns(self):''')
variant('parity_fa',fa)
orig = load(HERE/'g_simplified.py')
inputs = np.load(STIM, allow_pickle=False)
reference = np.asarray(orig.simulate_many(inputs.tolist()), dtype=np.int64)
for name in ('native_xor','last_row_original','parity_fa'):
    circ = load(HERE/(name+'.py'))
    raw = np.asarray(circ.simulate_many(inputs.tolist()), dtype=np.int64)
    print('equivalence', name, bool(np.array_equal(raw,reference)), 'mismatches',int(np.count_nonzero(raw != reference)),flush=True)
