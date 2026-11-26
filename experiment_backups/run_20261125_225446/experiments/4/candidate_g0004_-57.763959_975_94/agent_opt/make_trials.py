from pathlib import Path
import subprocess

root = Path(__file__).resolve().parent
parent = Path('/home/guoliang/multiplier/generations/4/candidate_g0004_-57.763959_970.2_92.py').read_text()
old = '''                        # Zero digit has an all-zero row; preserve original Booth semantics.
                        cell_neg = self._and(negative, self._or(generated_one, two))
                        # Shared kit port order: (a, b, c, d, e).
                        val = self._gate("MUX_XOR", generated_one, self._bit(m, k, zero), two, self._bit(m, k - 1, zero), cell_neg)'''
variants = {
    'shared_xors': '''                        val = self._or(self._and(generated_one, get_xor(k)), self._and(two, get_xor(k - 1)))''',
    'native_xors': '''                        cell_neg = self._and(negative, self._or(generated_one, two))
                        val = self._gate('XOR', cell_neg, self._or(self._and(generated_one, self._bit(m, k, zero)), self._and(two, self._bit(m, k-1, zero))))''',
    'direct_nega': '''                        val = self._or(self._and(generated_one, self._gate('XOR', negative, self._bit(m, k, zero))), self._and(two, self._gate('XOR', negative, self._bit(m, k-1, zero))))''',
}
assert parent.count(old) == 1
variants.update({
 'xor_native_all': '''                        # Zero digit has an all-zero row; preserve original Booth semantics.
                        cell_neg = self._and(negative, self._or(generated_one, two))
                        # Shared kit port order: (a, b, c, d, e).
                        val = self._gate("MUX_XOR", generated_one, self._bit(m, k, zero), two, self._bit(m, k - 1, zero), cell_neg)''',
})
for name, replacement in variants.items():
    path = root / (name + '.py')
    path.write_text(parent.replace(old, replacement))
    result = subprocess.run(['python', '/home/guoliang/multiplier/gate_cost.py', str(path)], capture_output=True, text=True)
    print(name, result.returncode, result.stdout.strip(), result.stderr.strip(), flush=True)
