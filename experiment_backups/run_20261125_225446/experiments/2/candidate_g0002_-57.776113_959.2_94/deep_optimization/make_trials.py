"""Create independent equivalence-preserving trial source variants from immutable handoff."""
from pathlib import Path
base = Path('/home/guoliang/multiplier/experiments/2/candidate_g0002_0002')
out = base/'deep_optimization'
s = (base/'partial_product_candidate.py').read_text()
xor_start = s.index('    def _xor(self, a, b):')
xor_end = s.index('    def _one_product_columns', xor_start)
and_start = s.index('    def xor_operands(self, n):')
and_end = s.index('    def _product_columns(self,', and_start)
gate_start = s.index('    def _gate(self, kind, *inputs, absorption=False):')
gate_end = s.index('    @staticmethod\n    def _bit',gate_start)
variants = {
 'native_xor': s[:xor_start]+s[xor_end:],
 'native_and': s[:and_start]+s[and_end:],
 'native_both': s[:xor_start]+s[xor_end:and_start]+s[and_end:],
 'native_gate': s[:gate_start]+s[gate_end:],
 'native_all': s[:gate_start]+s[gate_end:xor_start]+s[xor_end:and_start]+s[and_end:],
}
for key, code in variants.items():
 (out/(key+'.py')).write_text(code)
