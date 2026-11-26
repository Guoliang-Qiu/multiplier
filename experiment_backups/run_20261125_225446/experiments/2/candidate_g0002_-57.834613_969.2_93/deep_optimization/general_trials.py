"""Construct and screen exact-rewrite trials against immutable handoff."""
import importlib.util
import json
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parent
BASE = ROOT.parent / 'partial_product_candidate.py'
SRC = BASE.read_text()

def module(path):
    spec = importlib.util.spec_from_file_location('trial_'+path.stem, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

xor = '''    def _xor(self, a, b):
        # Expose shared absorption context to tap2's gate cache.
        both = self._and(a, b)
        either = self._or(a, b)
        return self._and_absorb(either, self._not(both))

'''
and_override = SRC[SRC.index('    def xor_operands('):SRC.index('\ndef build_circuit():')]
variants = {}
variants['inherited_and'] = SRC.replace(and_override, '')
variants['inherited_xor'] = SRC.replace(xor, '')
variants['both_inherited'] = SRC.replace(xor, '').replace(and_override, '')
variants['direct_active'] = SRC.replace('active = self._or(pos, neg)', 'active = self._xor(q[8], q[7])')
variants['direct_active_and'] = variants['inherited_and'].replace('active = self._or(pos, neg)', 'active = self._xor(q[8], q[7])')
variants['mux_cell_factor'] = SRC.replace('self._gate("MUX_XOR", generated_one, self._bit(m, k, zero), two, self._bit(m, k - 1, zero), cell_neg)', 'self._mux_xor(generated_one, self._bit(m, k, zero), two, self._bit(m, k - 1, zero), cell_neg)')
variants['step4_mux'] = SRC.replace('new = self._and(active, self._not(self._xor(q[7], m[k])))', 'new = self._or(self._and(pos, m[k]), self._and(neg, self._not(m[k])))')
variants['absorption_off'] = SRC.replace('_USE_ABSORPTION = True', '_USE_ABSORPTION = False')
variants['fa_swap'] = SRC.replace('total, carry = self._add3(x0, x1, x2)', 'total, carry = self._add3(x0, x2, x1)')
variants['fa_swap2'] = SRC.replace('total, carry = self._add3(x0, x1, x2)', 'total, carry = self._add3(x1, x2, x0)')
fa = '''    def _fa(self, a, b, cin):
        # Exact parity and majority using a shared propagate.
        propagate = self._xor(a, b)
        return self._xor(propagate, cin), self._or(self._and(a, b), self._and(propagate, cin))

'''
variants['propagate_fa'] = SRC.replace('    def _one_product_columns(', fa+'    def _one_product_columns(')
fa2 = '''    def _fa(self, a, b, cin):
        carry = self._or(self._and(a, b), self._and(cin, self._or(a, b)))
        return self._xor(self._xor(a, b), cin), carry

'''
variants['majority_fa'] = SRC.replace('    def _one_product_columns(', fa2+'    def _one_product_columns(')
variants['special_carry'] = SRC.replace('carry = self._and(x1_or_x0x2, x0_or_x2)', 'carry = self._or(x0x2, self._and(x1, x0_or_x2))')
variants['direct_xor_output'] = SRC.replace('outputs.append(self._or(bucket[0], carry) if col < 7 else self._xor(bucket[0], carry))', 'outputs.append(self._or(bucket[0], carry) if col < 7 else super()._xor(bucket[0], carry))')

stim = np.load('/home/guoliang/multiplier/stimulus.npy')
print('stim shape', stim.shape, flush=True)
inputs = stim[:2048].tolist()
reference = module(BASE).build_circuit().simulate_many(inputs)
for name, src in variants.items():
    path = ROOT / (name+'.py')
    path.write_text(src)
    try:
        circ = module(path).build_circuit()
        circ.validate()
        cost = circ.gatecost().total
        equal = circ.simulate_many(inputs) == reference
        print(json.dumps({'name':name,'cost':cost,'slots':circ.partial_product_count,'equal_2048':equal}), flush=True)
    except Exception as exc:
        print(name,'FAIL',repr(exc),flush=True)
