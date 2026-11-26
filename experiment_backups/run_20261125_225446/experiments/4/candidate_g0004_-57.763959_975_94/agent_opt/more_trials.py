from pathlib import Path
import subprocess
r=Path(__file__).resolve().parent
p=Path('/home/guoliang/multiplier/generations/4/candidate_g0004_-57.763959_970.2_92.py').read_text()
variants={
'native_xor_all':[("        both = self._and(a, b)\n        either = self._or(a, b)\n        return self._and(either, self._not(both))", "        return self._gate('XOR', a, b)")],
'fa_xor':[("        return super()._and(a, b)\n\n    def _product_columns", "        return super()._and(a, b)\n\n    def _fa(self, a, b, cin):\n        axb = self._xor(a, b)\n        return self._xor(axb, cin), self._or(self._and(a, b), self._and(axb, cin))\n\n    def _product_columns")],
'fa_xor_native':[("        return super()._and(a, b)\n\n    def _product_columns", "        return super()._and(a, b)\n\n    def _fa(self, a, b, cin):\n        axb = self._gate('XOR', a, b)\n        return self._gate('XOR', axb, cin), self._or(self._and(a, b), self._and(axb, cin))\n\n    def _product_columns")],
'xor_alt':[("        both = self._and(a, b)\n        either = self._or(a, b)\n        return self._and(either, self._not(both))", "        return self._or(self._and(a, self._not(b)), self._and(self._not(a), b))")],
'xor_xnor':[("        both = self._and(a, b)\n        either = self._or(a, b)\n        return self._and(either, self._not(both))", "        return self._not(self._or(self._and(a, b), self._not(self._or(a, b))))")],
}
for name, subs in variants.items():
 t=p
 for a,b in subs:
  assert t.count(a)==1,(name,a)
  t=t.replace(a,b)
 path=r/(name+'.py');path.write_text(t)
 o=subprocess.run(['python','/home/guoliang/multiplier/gate_cost.py',str(path)],capture_output=True,text=True)
 print(name,o.returncode,o.stdout.strip(),o.stderr.strip(),flush=True)
