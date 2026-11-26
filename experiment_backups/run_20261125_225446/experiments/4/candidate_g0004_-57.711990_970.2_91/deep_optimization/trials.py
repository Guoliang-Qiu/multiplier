"""Evaluate scoped gate-level rewrites against external-stimulus raw samples."""
import importlib.util
import json
import pathlib
import sys
import numpy as np
ROOT = pathlib.Path('/home/guoliang/multiplier')
DIR = ROOT / 'experiments/4/candidate_g0004_0002/deep_optimization'
SOURCE = (DIR.parent / 'partial_product_candidate.py').read_text()
sys.path[:0] = ['/home/guoliang', '/home/guoliang/open_question_solver']
def load(path, label):
    spec = importlib.util.spec_from_file_location(label, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    c = mod.build_circuit()
    c.validate()
    return c
stim = np.load(ROOT / 'stimulus.npy', mmap_mode='r')
rows = stim[::263].tolist()
ref = load(DIR.parent / 'partial_product_candidate.py', 'handoff').simulate_many(rows)
def tryit(name, text):
    p = DIR / (name + '.py')
    p.write_text(text)
    try:
        c = load(p, name)
        cost = c.gatecost()
        outputs = c.simulate_many(rows)
        diffs = sum(a != b for a,b in zip(ref, outputs))
        print(json.dumps(dict(name=name, cost=cost.total, counts=cost.counts, pp=c.partial_product_count, sample_diffs=diffs)), flush=True)
    except Exception as e:
        print(name, type(e).__name__, str(e), flush=True)
start = SOURCE
tryit('trial_handoff', start)
xor_custom = '''    def _xor(self, a, b):
        both = self._and(a, b)
        either = self._or(a, b)
        return self._and(either, self._not(both))
'''
assert xor_custom in start
tryit('trial_native_xor', start.replace(xor_custom,''))
old_fa = '''                    ac = self._and(x0, x2)
                    b_or_ac = self._or(x1, ac)
                    a_or_c = self._or(x0, x2)
                    carry = self._and(b_or_ac, a_or_c)
                    total = self._xor(b_or_ac, a_or_c)'''
assert old_fa in start
new_fa = '''                    carry = self._or(self._and(x0, x2), self._and(x1, self._or(x0, x2)))
                    total = self._xor(self._xor(x0, x1), x2)'''
tryit('trial_compressor', start.replace(old_fa,new_fa))
old = 'val = self._or(self._and(one, mk), self._and(negative, self._not(mk)))'
new = 'val = self._and(self._or(one, negative), self._not(self._xor(negative, mk)))'
assert old in start
tryit('trial_sign_factoring',start.replace(old,new))
old='new = self._and(active, self._not(self._xor(q[7], m[k])))'
new='new = self._or(self._and(pos, m[k]), self._and(neg, self._not(m[k])))'
assert old in start
tryit('trial_sign_original',start.replace(old,new))
# Remove two genuine but redundant OR-with-zero gates; their outputs equal inputs.
tryit('trial_buffer_fold',start.replace("self.add('OR', g_6, zero)", 'g_6').replace("self.add('OR', g_5, zero)", 'g_5'))
# Alternative local Boolean forms of the final Booth correction and output adder.
old = 'self._and(self._not(one), self._xor(h, m))'
new = 'self._or(self._and(h, self._and(self._not(m), self._not(low))), self._and(self._not(h), self._and(m, low)))'
assert old in start
tryit('trial_two_factor',start.replace(old,new))
old='p = self._or(self._and(q_bits[2 * step + 1], x_and), self._and(self._not(q_bits[2 * step + 1]), m_bits[1]))'
new='p = self._and(self._or(q_bits[2 * step + 1], m_bits[1]), self._or(self._not(q_bits[2 * step + 1]), x_and))'
assert old in start
tryit('trial_p_factor',start.replace(old,new))
old='carry = self._and(bucket[0], carry)'
# Absorption-aware sharing already used, but compare direct complement form.
new='carry = self._not(self._or(self._not(bucket[0]), self._not(carry)))'
assert old in start
tryit('trial_output_demorgan',start.replace(old,new))
