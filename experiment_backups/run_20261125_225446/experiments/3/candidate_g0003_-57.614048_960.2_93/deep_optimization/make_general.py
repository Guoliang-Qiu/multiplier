"""Generate equivalence-oriented variants from immutable handoff source."""
from pathlib import Path
src=Path('/home/guoliang/multiplier/experiments/3/candidate_g0003_0008/partial_product_candidate.py').read_text()
out=Path('/home/guoliang/multiplier/experiments/3/candidate_g0003_0008/deep_optimization')
variants={}
old='            active = self._or(pos, neg)'
assert src.count(old)==1
variants['active_xor']=src.replace(old,'            active = self._xor(q[8], q[7])')
start=src.index('    def xor_operands(self, n):')
end=src.index('    def _product_columns(self, a, b, c, d, zero, one):',start)
variants['native_and']=src[:start]+src[end:]
variants['both']=variants['active_xor'][:variants['active_xor'].index('    def xor_operands(self, n):')]+variants['active_xor'][variants['active_xor'].index('    def _product_columns(self, a, b, c, d, zero, one):'):]
old='        return self._and_absorb(either, self._not(both))'
variants['native_xor']=src.replace(old,'        return super()._xor(a, b)')
old='        return super()._gate(kind, *inputs, absorption=absorption or self._USE_ABSORPTION)'
variants['native_absorption']=src.replace(old,'        return super()._gate(kind, *inputs, absorption=absorption)')
for name,text in variants.items():
    (out/(name+'.py')).write_text(text)
