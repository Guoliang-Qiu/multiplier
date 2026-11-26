from pathlib import Path
root=Path(__file__).resolve().parent
src=(root/'general_baseline.py').read_text()
for name,old,new in [('or','self._or(','self._or_absorb('),('and','self._and(','self._and_absorb('),('both','self._or(','self._or_absorb(')]:
 if name=='both':
  trial=src.replace('self._or(','self._or_absorb(').replace('self._and(','self._and_absorb(')
 else: trial=src.replace(old,new)
 (root/f'absorb_{name}.py').write_text(trial)
# Rewrite sign row as a select: active && XNOR(q7,m) currently optimal
# Use an exact ripple implementation with half-adder dispatch only for true sums.
a=src.index('    def _build_outputs(self):')
b=src.index('    def _product_columns(self,',a)
trial=src[:a]+'''    def _build_outputs(self):
        """Use inherited constant-aware adders while preserving low-bit OR."""
        carry = self._zero
        outputs = []
        for col, bucket in enumerate(self._columns):
            if not bucket:
                total, carry = carry, self._zero
            elif len(bucket) == 1 and col < 7 and carry != self._zero:
                total, carry = self._or(bucket[0], carry), self._and(bucket[0], carry)
            elif len(bucket) == 1:
                total, carry = self._ha(bucket[0], carry)
            else:
                total, carry = self._add3(bucket[0], bucket[1], carry)
            outputs.append(total)
        self.output_ids = [self._zero] * 6 + outputs[6:18] + [outputs[17]]

'''+src[b:]
(root/'output_ha.py').write_text(trial)
