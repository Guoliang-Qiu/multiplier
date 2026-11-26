"""Produce independently loadable equivalence-preserving general-pass variants."""
from pathlib import Path
p=Path('/home/guoliang/multiplier/experiments/2/candidate_g0002_0001/deep_optimization')
s=Path('/home/guoliang/multiplier/experiments/2/candidate_g0002_0001/partial_product_candidate.py').read_text()
variants={}
def change(name, old, new):
    assert old in s, name
    variants[name]=s.replace(old,new)
change('xor_primitive', '''        both = self._and(a, b)
        either = self._or(a, b)
        return self._and(either, self._not(both))''', '''        return self._gate("XOR", a, b)''')
change('compress_order', '''                    ac = self._and(x0, x2)
                    b_or_ac = self._or(x1, ac)
                    a_or_c = self._or(x0, x2)
                    carry = self._and(b_or_ac, a_or_c)
                    total = self._xor(b_or_ac, a_or_c)''', '''                    ac = self._and(x0, x2)
                    a_or_c = self._or(x0, x2)
                    carry = self._or(ac, self._and(x1, a_or_c))
                    total = self._xor(self._xor(x0, x2), x1)''')
change('booth_p', '''                p = self._or(self._and(q[2 * step + 1], x_and), self._and(self._not(q[2 * step + 1]), m[1]))''', '''                sign = q[2 * step + 1]
                p = self._or(m[1], self._and(sign, self._not(m[0])))''')
change('booth_b', '''                b = self._or(self._and(generated_one, self._and(p, self._not(generated_q))), self._and(two, m[0]))''', '''                b = self._or(self._and(generated_one, p), self._and(two, m[0]))''')
change('booth_d', '''                    d_tmp = self._and(self._not(self._and(q[2 * step], q[2 * step - 1])), generated_q)''', '''                    d_tmp = self._and(self._not(q[2 * step - 1]), generated_q)''')
change('last_out', '''        for col, bucket in enumerate(all_columns):''', '''        for col, bucket in enumerate(all_columns[:18]):''')
change('neg_shared', '''                        cell_neg = self._and(negative, self._or(generated_one, two))''', '''                        cell_neg = self._and(negative, self._or(generated_one, two))''')
for name, v in variants.items():
    (p / (name+'.py')).write_text(v)
