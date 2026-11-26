from pathlib import Path
src=Path('/home/guoliang/multiplier/experiments/3/candidate_g0003_0000/partial_product_candidate.py').read_text()
start=src.index('    def _product_columns_before_compensation_previous(')
end=src.index('\ndef build_circuit():',start)
replacement='''    def _product_columns(self, a, b, c, d, zero, one):
        """Preserve handoff deletion, shifted row and its final G correction.

        Historical intermediate correction and deleted products are not present
        in the pre-compression layout; G uses named input bits, not node IDs.
        """
        columns = self._product_columns_before_compensation(a, b, c, d, zero, one)
        original = columns[4]
        shifted = original[0]
        columns[4] = [zero, original[1], original[4], original[6],
                      self._xor(d[1], self._and(c[4], d[0]))]
        columns[5].append(shifted)
        return columns
'''
src=src[:start]+replacement+src[end:]
root=Path('/home/guoliang/multiplier/experiments/3/candidate_g0003_0000/deep_optimization')
(root/'general_refactor.py').write_text(src)
(root/'native_xor.py').write_text(src.replace('''    def _xor(self, a, b):
        """Use a shared AND/OR XOR realization, tuned for current gate costs."""
        both = self._and(a, b)
        either = self._or(a, b)
        return self._and(either, self._not(both))

''',''))
