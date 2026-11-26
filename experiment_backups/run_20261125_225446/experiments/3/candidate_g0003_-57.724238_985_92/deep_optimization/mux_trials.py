from pathlib import Path
root=Path(__file__).resolve().parent
src=(root/'general_baseline.py').read_text()
a=src.index('    def _xor(self, a, b):')
b=src.index('    def _one_product_columns',a)
method='''    def _xor(self, a, b):
        """Fuse a two-product OR operand into a five-input MUX_XOR cell."""
        for e, node in ((b, a), (a, b)):
            outer = self.nodes[node]
            if outer.kind == "OR":
                left, right = (self.nodes[v] for v in outer.inputs)
                if left.kind == right.kind == "AND":
                    return self._mux_xor(*left.inputs, *right.inputs, e)
        both = self._and(a, b)
        either = self._or(a, b)
        return self._and(either, self._not(both))

'''
(root/'mux_fuse.py').write_text(src[:a]+method+src[b:])
# MUX_XOR for XOR(operand, single AND) with the second product tied to zero
method2='''    def _xor(self, a, b):
        """Fuse either AND or two-product OR into the XOR operation."""
        for e, node in ((b, a), (a, b)):
            outer = self.nodes[node]
            if outer.kind == "AND":
                return self._mux_xor(*outer.inputs, self._zero, self._zero, e)
            if outer.kind == "OR":
                left, right = (self.nodes[v] for v in outer.inputs)
                if left.kind == right.kind == "AND":
                    return self._mux_xor(*left.inputs, *right.inputs, e)
        both = self._and(a, b)
        either = self._or(a, b)
        return self._and(either, self._not(both))

'''
(root/'mux_fuse_and.py').write_text(src[:a]+method2+src[b:])
# targeted G mapped to MUX_XOR directly, rather than generic xor dispatch
(root/'mux_g.py').write_text(src.replace('self._xor(d[1], self._and(c[4], d[0]))','self._mux_xor(c[4], d[0], zero, zero, d[1])'))
