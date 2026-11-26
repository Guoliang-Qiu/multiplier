from pathlib import Path
import subprocess
r=Path(__file__).resolve().parent
p=(r/'shared_xors.py').read_text()
changes={
'booth_digit_xor':("generated_one = self._xor(generated_m, low)","generated_one = self._gate('XOR', generated_m, low)"),
'booth_two_xor':("self._xor(h, generated_m)","self._gate('XOR', h, generated_m)"),
'product_xor':("self._xor(q[2 * step + 1], self._bit(m, k, zero))","self._gate('XOR', q[2 * step + 1], self._bit(m, k, zero))"),
'input_correction_xor':("self._xor(b[1], a[4])","self._gate('XOR', b[1], a[4])"),
'sign_xor':("self._xor(q[7], m[k])","self._gate('XOR', q[7], m[k])"),
'output_half_xor':("self._xor(bucket[0], bucket[1])","self._gate('XOR', bucket[0], bucket[1])"),
'output_ripple_xor':("self._xor(bucket[0], carry)","self._gate('XOR', bucket[0], carry)"),
'fa_xor':("        return super()._and(a, b)\n\n    def _product_columns", "        return super()._and(a, b)\n\n    def _fa(self, a, b, cin):\n        axb = self._xor(a, b)\n        return self._xor(axb, cin), self._or(self._and(a, b), self._and(axb, cin))\n\n    def _product_columns"),
'fa_native':("        return super()._and(a, b)\n\n    def _product_columns", "        return super()._and(a, b)\n\n    def _fa(self, a, b, cin):\n        axb = self._gate('XOR', a, b)\n        return self._gate('XOR', axb, cin), self._or(self._and(a, b), self._and(axb, cin))\n\n    def _product_columns"),
}
for name,(old,new) in changes.items():
 if name in ('product_xor','input_correction_xor','sign_xor'):
  continue
 assert p.count(old)==1,(name,p.count(old))
 t=p.replace(old,new)
 path=r/(name+'.py');path.write_text(t)
 o=subprocess.run(['python','/home/guoliang/multiplier/gate_cost.py',str(path)],capture_output=True,text=True)
 print(name,o.returncode,o.stdout.strip(),o.stderr.strip(),flush=True)
