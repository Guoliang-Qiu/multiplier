"""Generate readable experimental variants from the protected B parent."""
from pathlib import Path
src = Path('/home/guoliang/multiplier/generations/3/candidate_g0003_-57.768547_1018_92.py').read_text()
out = Path('/home/guoliang/multiplier/experiments/3/candidate_g0003_0010')

def save(name, text):
    (out / (name + '.py')).write_text(text)

# Variant F: transfer A's cheap, deliberately biased low-weight column-four
# simplification while retaining B's asymmetric truncation and ordered G network.
old = '        columns[5].append(correction)\n        return columns'
assert src.count(old) == 1
save('fused_low', src.replace(old, '''        columns[5].append(correction)
        # Parent A's biased low-weight approximation: suppress one column-four
        # term but keep its constant correction in the original column.
        columns[4][0] = zero
        return columns'''))

# Exact factoring: A's sharing of the top Booth row via one shared sign guard.
old = '''                val = self._or(self._and(one, mk), self._and(negative, self._not(mk)))'''
new = '''                active = self._or(one, negative)
                    val = self._and(active, self._not(self._xor(q_bits[7], mk)))'''
assert src.count(old) == 1
save('top_guard', src.replace(old, new))

# A's half-adder-compatible OR low-sum implementation extends from bit 6 to 7.
old = '                if col <= 6:'
assert src.count(old) == 1
save('low_or7', src.replace(old, '                if col <= 7:'))

# Exact alternative one/two Booth digit Boolean factorization from A.
old = '''                two = self._or(self._and(self._and(m, low), self._not(h)),
                               self._and(self._not(self._or(m, low)), h))'''
new = '''                two = self._and(self._not(one), self._xor(h, m))'''
assert src.count(old) == 1
save('digit_factor', src.replace(old,new))

# Try A's approximate compressor with B's G and pruning.
old = '''        # The reference LIFO compressor is the required original stage.
        self._compress_columns_reference()'''
new = '''        # Transfer parent A's selective majority carry-only compressor in
        # low-weight columns, keeping the exact reference elsewhere.
        columns = self._columns
        for col in range(OUT_TOTAL):
            while len(columns[col]) >= 3:
                x, y, z = columns[col].pop(), columns[col].pop(), columns[col].pop()
                if col in (0, 1, 2, 3) and all(v not in (self._zero, self._one) for v in (x,y,z)):
                    xz = self._and(x,z)
                    y_or_xz = self._or(y,xz)
                    x_or_z = self._or(x,z)
                    carry = self._and(y_or_xz,x_or_z)
                    if col + 1 < OUT_TOTAL:
                        columns[col+1].append(carry)
                    continue
                total, carry = self._add3(x,y,z)
                columns[col].append(total)
                if col + 1 < OUT_TOTAL:
                    columns[col+1].append(carry)'''
assert src.count(old) == 1
save('majority', src.replace(old,new))
