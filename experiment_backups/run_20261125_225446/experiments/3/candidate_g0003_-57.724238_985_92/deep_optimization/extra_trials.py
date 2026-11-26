from pathlib import Path
root=Path(__file__).resolve().parent
src=(root/'general_refactor.py').read_text()
start=src.index('        for m, q in ((a, b), (c, d)):')
end=src.index('        return all_columns',start)
(root/'no_sign_factoring.py').write_text(src[:start]+src[end:])
# A locally equivalent correction has an XNOR / NAND implementation.
(root/'correction_xnor.py').write_text(src.replace('self._xor(d[1], self._and(c[4], d[0]))','self._not(self._or(self._and(d[1], self._and(c[4], d[0])), self._not(self._or(d[1], self._and(c[4], d[0])))))'))
# Replace the shared XOR realization by a polarity-dual SOP.
a=src.index('    def _xor(self, a, b):')
b=src.index('    def _one_product_columns',a)
(root/'xor_sop.py').write_text(src[:a]+'''    def _xor(self, a, b):
        """Use complementary pairwise products, sharing negated operands."""
        return self._or(self._and(a, self._not(b)), self._and(self._not(a), b))

'''+src[b:])
