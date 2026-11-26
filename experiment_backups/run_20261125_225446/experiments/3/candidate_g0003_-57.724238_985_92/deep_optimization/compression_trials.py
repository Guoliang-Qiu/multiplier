from pathlib import Path
root=Path(__file__).resolve().parent
src=(root/'general_refactor.py').read_text()
a=src.index('    def _compress_columns(self):')
b=src.index('    def _build_outputs(self):',a)
base='''    def _compress_columns(self):
        """The handoff's special columns 0--3 are empty; use tap2's exact tree."""
        self._compress_columns_reference()

'''
src=src[:a]+base+src[b:]
(root/'general_baseline.py').write_text(src)
for name,order in [('reverse','all_columns[col].reverse()'),('sort','all_columns[col].sort()'),('sort_reverse','all_columns[col].sort(reverse=True)'),('const_first','all_columns[col].sort(key=lambda n: (n not in (self._zero, self._one), n))'),('const_last','all_columns[col].sort(key=lambda n: (n in (self._zero, self._one), n))')]:
 trial=src.replace('        self._compress_columns_reference()',f'''        for col in range(OUT_TOTAL):
            {order}
            while len(all_columns[col]) >= 3:
                x, y, z = (all_columns[col].pop(), all_columns[col].pop(), all_columns[col].pop())
                total, carry = self._add3(x, y, z)
                all_columns[col].append(total)
                if col + 1 < OUT_TOTAL:
                    all_columns[col + 1].append(carry)''').replace('        for col in range(OUT_TOTAL):\n            '+order,'        all_columns = self._columns\n        for col in range(OUT_TOTAL):\n            '+order)
 (root/f'compression_{name}.py').write_text(trial)
