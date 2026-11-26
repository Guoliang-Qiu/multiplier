"""Generate readable experimental variants of the immutable handoff."""
from pathlib import Path
src = Path('/home/guoliang/multiplier/experiments/2/candidate_g0002_0006/partial_product_candidate.py').read_text()
root = Path('/home/guoliang/multiplier/experiments/2/candidate_g0002_0006/deep_optimization')
variants = {}
variants['xor_primitive'] = src.replace('        both = self._and(a, b)\n        either = self._or(a, b)\n        return self._and(either, self._not(both))', '        return self._gate("XOR", a, b)')
variants['xor_primitive_fa'] = variants['xor_primitive'].replace('    def _one_product_columns(', '''    def _fa(self, a, b, cin):
        """Carry uses the existing parity node instead of an XNOR network."""
        parity = self._xor(a, b)
        return self._xor(parity, cin), self._or(self._and(a, b), self._and(parity, cin))

    def _one_product_columns(''')
variants['xor_booth_only'] = src.replace('        both = self._and(a, b)\n        either = self._or(a, b)\n        return self._and(either, self._not(both))', '''        if self._in_booth:
            return self._gate("XOR", a, b)
        both = self._and(a, b)
        either = self._or(a, b)
        return self._and(either, self._not(both))''').replace('        cols: list[list[int]] = [[] for _ in range(OUT_WIDTH)]', '        self._in_booth = True\n        cols: list[list[int]] = [[] for _ in range(OUT_WIDTH)]').replace('        return cols\n\n    def _product_columns_before_compensation', '        self._in_booth = False\n        return cols\n\n    def _product_columns_before_compensation')
variants['xor_sop'] = src.replace('        both = self._and(a, b)\n        either = self._or(a, b)\n        return self._and(either, self._not(both))', '        return self._or(self._and(a, self._not(b)), self._and(self._not(a), b))')
variants['xor_nand'] = src.replace('        both = self._and(a, b)\n        either = self._or(a, b)\n        return self._and(either, self._not(both))', '        both = self._and(a, b)\n        return self._or(self._and(a, self._not(both)), self._and(b, self._not(both)))')
variants['mux_more'] = src.replace('if step in (1, 2) and 3 <= k <= 8 and k < q_bits_of_step - 1:', 'if step in (0, 1, 2, 3) and 3 <= k <= 8 and k < q_bits_of_step - 1:')
variants['mux_all'] = src.replace('if step in (1, 2) and 3 <= k <= 8 and k < q_bits_of_step - 1:', 'if step in (0, 1, 2, 3) and 3 <= k <= 8:')
variants['mux_more_refcompress'] = variants['mux_more'].replace('if col == 3 and compressor_index <= 1:', 'if False:')
variants['mux_more_xor_sop'] = variants['mux_more'].replace('        both = self._and(a, b)\n        either = self._or(a, b)\n        return self._and(either, self._not(both))', '        return self._or(self._and(a, self._not(b)), self._and(self._not(a), b))')
variants['mux_more_signfactor'] = variants['mux_more'].replace('                        val = self._or(self._and(generated_one, get_xor(k)), self._and(two, get_xor(k - 1)))', '''                        if k == 9:
                            val = self._and(self._or(generated_one, two), get_xor(8))
                        else:
                            val = self._or(self._and(generated_one, get_xor(k)), self._and(two, get_xor(k - 1)))''')
for name, text in variants.items():
    text = text.replace('        if q[0] == self.input_ids[9]:\n            cols[2][:] = [zero, one]\n        else:\n            cols[2][:] = [zero, one]', '        cols[2][:] = [zero, one]')
    (root / (name + '.py')).write_text(text)
