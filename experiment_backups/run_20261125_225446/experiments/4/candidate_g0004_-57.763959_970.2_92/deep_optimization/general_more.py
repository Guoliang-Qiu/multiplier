"""Additional equivalence-preserving structural comparisons for three stages."""
from pathlib import Path
import subprocess,sys
root=Path('/home/guoliang/multiplier')
here=Path(__file__).resolve().parent
src=(here/'g_simplified.py').read_text()
variants={}
variants['no_custom_and']=src[:src.index('    def xor_operands(')]+src[src.index('    def _product_columns(',src.index('    def xor_operands(')):]
variants['standard_col3']=src.replace('''                if col == 3 and compressor_index <= 1:''','''                if False and col == 3 and compressor_index <= 1:''')
variants['native_output_xor']=src.replace('''outputs.append(self._or(bucket[0], carry) if col < 7 else self._xor(bucket[0], carry))''','''outputs.append(self._or(bucket[0], carry) if col < 7 else self._gate('XOR', bucket[0], carry))''')
variants['fa_gate_xor']=src.replace('''    def _compress_columns(self):''','''    def _fa(self, a, b, cin):
        """Exact parity/majority gate sharing variant."""
        parity = self._gate('XOR', a, b)
        total = self._gate('XOR', parity, cin)
        carry = self._or(self._and(a, b), self._and(parity, cin))
        return total, carry

    def _compress_columns(self):''')
variants['mux_all_middle']=src.replace('step in (1, 2) and 3 <= k <= 8','step in (0, 1, 2, 3) and 3 <= k <= 8')
variants['mux_one_middle']=src.replace('step in (1, 2) and 3 <= k <= 8','step in (1,) and 3 <= k <= 8')
variants['mux_three_middle']=src.replace('step in (1, 2) and 3 <= k <= 8','step in (1, 2, 3) and 3 <= k <= 8')
variants['last_row_gate_xor']=src.replace('''self._not(self._xor(q[7], m[k]))''','''self._not(self._gate('XOR', q[7], m[k]))''')
variants['xor_minterms']=src.replace('''        both = self._and(a, b)
        either = self._or(a, b)
        return self._and(either, self._not(both))''','''        return self._or(self._and(a, self._not(b)), self._and(self._not(a), b))''')
for name,body in variants.items():
    p=here/(name+'.py');p.write_text(body)
    res=subprocess.run([sys.executable,str(root/'gate_cost.py'),str(p)],capture_output=True,text=True)
    print(name,res.returncode,res.stdout.strip(),res.stderr[-600:],flush=True)
