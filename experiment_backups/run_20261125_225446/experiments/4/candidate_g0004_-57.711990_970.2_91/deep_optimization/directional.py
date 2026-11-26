"""Evaluate several equivalent MUX_XOR placements after general baseline."""
import importlib.util, pathlib, sys, json, numpy as np
ROOT=pathlib.Path('/home/guoliang/multiplier')
DIR=ROOT/'experiments/4/candidate_g0004_0002/deep_optimization'
SOURCE=(DIR/'general_baseline.py').read_text()
sys.path[:0]=['/home/guoliang','/home/guoliang/open_question_solver']
def load(p,name):
 s=importlib.util.spec_from_file_location(name,p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); c=m.build_circuit(); c.validate(); return c
rows=np.load(ROOT/'stimulus.npy', mmap_mode='r')[::263].tolist()
ref=load(DIR/'general_baseline.py','ref').simulate_many(rows)
def trial(name, text):
 p=DIR/(name+'.py'); p.write_text(text)
 try:
  c=load(p,name); cost=c.gatecost(); out=c.simulate_many(rows)
  print(json.dumps(dict(name=name,cost=cost.total,pp=c.partial_product_count,counts=cost.counts,diffs=sum(x!=y for x,y in zip(out,ref)))),flush=True)
 except Exception as exc: print(name,type(exc).__name__,str(exc),flush=True)
old='if step in (1, 2) and 3 <= k <= 8 and k < q_bits_of_step - 1:'
assert old in SOURCE
trial('dir_step3',SOURCE.replace(old,'if step in (1, 2, 3) and 3 <= k <= 8 and k < q_bits_of_step - 1:'))
trial('dir_step0',SOURCE.replace(old,'if step in (0, 1, 2) and 3 <= k <= 8 and k < q_bits_of_step - 1:').replace('cell_neg = self._and(negative, self._not(self._and(m, low)))','cell_neg = negative if step == 0 else self._and(negative, self._not(self._and(m, low)))'))
trial('dir_step03',SOURCE.replace(old,'if step in (0, 1, 2, 3) and 3 <= k <= 8 and k < q_bits_of_step - 1:').replace('cell_neg = self._and(negative, self._not(self._and(m, low)))','cell_neg = negative if step == 0 else self._and(negative, self._not(self._and(m, low)))'))
# MUX_XOR common e=zero realizes OR-of-two-AND, but not necessarily cheaper.
old='val = self._or(self._and(one, get_xor(k)), self._and(two, get_xor(k - 1)))'
assert old in SOURCE
trial('dir_generic_mux',SOURCE.replace(old,'val = self._mux_xor(one, get_xor(k), two, get_xor(k - 1), zero)'))
# MUX_XOR for sign-digit ordinary selection (step 4), whose one and negative are disjoint.
old='val = self._or(self._and(one, mk), self._and(negative, self._not(mk)))'
assert old in SOURCE
trial('dir_high_digit_mux',SOURCE.replace(old,'val = self._mux_xor(one, mk, negative, self._not(mk), zero)'))
# Sweep focused low-digit subsets, preserving baseline's existing step-1/2 mapping.
for lo, hi in ((3,5),(3,6),(3,7),(4,8),(5,8),(6,8),(3,8)):
 t=SOURCE
 t=t.replace('if step in (1, 2) and 3 <= k <= 8 and k < q_bits_of_step - 1:',f'if (step in (1, 2) or (step == 0 and {lo} <= k <= {hi})) and 3 <= k <= 8 and k < q_bits_of_step - 1:')
 t=t.replace('cell_neg = self._and(negative, self._not(self._and(m, low)))','cell_neg = negative if step == 0 else self._and(negative, self._not(self._and(m, low)))')
 trial(f'dir_low_{lo}_{hi}',t)
