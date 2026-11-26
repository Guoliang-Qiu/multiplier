from pathlib import Path
p=Path(__file__).resolve().parent
s=(p.parent/'partial_product_candidate.py').read_text()
variants={
'fa_xor': '''    def _fa(self, a, b, cin):
        pair = self._xor(a, b)
        return self._xor(pair, cin), self._or(self._and(a, b), self._and(pair, cin))
''',
'fa_majority': '''    def _fa(self, a, b, cin):
        ab = self._and(a, b)
        ao = self._or(a, b)
        return self._xor(self._xor(a, b), cin), self._or(ab, self._and(ao, cin))
''',
'fa_mixed': '''    def _fa(self, a, b, cin):
        ac = self._and(a, cin)
        ao = self._or(a, cin)
        xn = self._or(ac, self._not(ao))
        bc = self._or(b, xn)
        return self._xor(b, self._not(xn)), self._and(ao, bc)
''',
'fa_nand': '''    def _fa(self, a, b, cin):
        ac = self._and(a, cin)
        ao = self._or(a, cin)
        xn = self._or(ac, self._not(ao))
        bc = self._or(b, xn)
        return self._and(self._not(self._and(b, xn)), bc), self._and(ao, bc)
''',
'product_xor_native': '''    def _xor(self, a, b):
        return self._gate('XOR', a, b)
''',
'output_short': '''    def _build_outputs(self):
        all_columns = self._columns
        zero, one = self._zero, self._one
        carry = None
        outputs = []
        for col, bucket in enumerate(all_columns[:18]):
            bucket = bucket or [zero]
            if carry is None:
                outputs.append(bucket[0] if len(bucket) == 1 else self._xor(bucket[0], bucket[1]))
                if len(bucket) > 1:
                    carry = self._and(bucket[0], bucket[1])
            elif len(bucket) == 1 and bucket[0] == zero:
                outputs.append(carry)
                carry = zero
            elif len(bucket) == 1 and bucket[0] == one:
                outputs.append(self._not(carry))
            elif len(bucket) == 1:
                outputs.append(self._or(bucket[0], carry) if col < 7 else self._xor(bucket[0], carry))
                carry = self._and(bucket[0], carry)
            else:
                total, carry = self._add3(bucket[0], bucket[1], carry)
                outputs.append(total)
        self.output_ids = [zero] * 6 + outputs[6:18] + [outputs[17]]
''',
}
for name, block in variants.items():
    text=s
    if name=='product_xor_native':
        start=text.index('    def _xor(self, a, b):'); end=text.index('    def _one_product_columns(',start)
        text=text[:start]+block+'\n'+text[end:]
    elif name=='output_short':
        start=text.index('    def _build_outputs(self):');end=text.index('    def xor_operands(',start)
        text=text[:start]+block+'\n'+text[end:]
    else:text=text.replace('    def _build_outputs(self):',block+'\n    def _build_outputs(self):',1)
    (p/(name+'.py')).write_text(text)
