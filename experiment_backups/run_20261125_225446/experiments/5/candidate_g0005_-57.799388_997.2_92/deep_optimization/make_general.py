"""Produce readable consolidated general-pass experiment from immutable handoff."""
from pathlib import Path
src = Path('/home/guoliang/multiplier/experiments/5/candidate_g0005_0000/partial_product_candidate.py').read_text()
start = src.index('    def _product_columns_before_compensation_previous(')
end = src.index('\ndef build_circuit():', start)
src = src[:start] + '''    def _product_columns(self, a, b, c, d, zero, one):
        """Preserve the handoff deletion/compensation layout and slot order."""
        columns = self._product_columns_before_compensation(a, b, c, d, zero, one)
        del columns[3][1]
        del columns[3][0]
        # G = (d0 & c3) XOR (d1 & (d0 | ~c2)).
        columns[4].append(self._mux_xor(d[1], d[0], d[1], self._not(c[2]),
                                         self._and(d[0], c[3])))
        del columns[4][3]
        columns[4].append(d[1])
        del columns[4][6]
        del columns[4][5]
        columns[5].append(self._or(d[0], d[1]))
        del columns[5][6]
        del columns[4][4]
        # Previous OR(x,ZERO) cells were non-folded identity buffers.
        columns[4].append(self._not(d[0]))
        columns[5].append(d[0])
        return columns
''' + src[end:]
root = Path('/home/guoliang/multiplier/experiments/5/candidate_g0005_0000/deep_optimization')
(root / 'general_v1.py').write_text(src)
