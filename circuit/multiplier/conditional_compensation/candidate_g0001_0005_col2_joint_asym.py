"""Standalone three-stage adaptation of the col2 joint-asymmetric candidate.

Source: /home/guoli/multiplier/initial_solutions/
candidate_g0001_0005_col2_joint_asym.py and its sparse/0005 ancestors.
Preserves construction order, zero slots, approximate compressors and outputs.
No imports from the original candidate modules are required.
"""
from multiplier.circuit.multiplier.tap2_9bit_multiplier import (
    MultiplierCircuit, OUT_TOTAL, OUT_WIDTH, WIDTH,
)


class Candidate(MultiplierCircuit):
    PROD_CUT_A = 2
    PROD_CUT_B = 2
    COMP_COLS = (10, 11, 13, 15, 18)
    ROUND_COLS = ()

    def _xor(self, a, b):
        both = self._and(a, b)
        either = self._or(a, b)
        return self._and(either, self._not(both))

    def _product_columns(self, a, b, c, d, zero, one):
        """Return one joint layout, including the asymmetric CD compensation."""
        columns = [[] for _ in range(OUT_TOTAL)]
        for left, right, cut, cd_side in (
            (a, b, self.PROD_CUT_A, False),
            (c, d, self.PROD_CUT_B, True),
        ):
            product = self._one_product_columns(right, left, zero, cut)
            assert len(product[2]) == 2
            # Preserve bucket positions: the special compressors depend on order.
            product[2][0] = zero
            if cd_side:
                product[2][1] = one
            for col in range(OUT_WIDTH):
                columns[col].extend(product[col])
        for col in self.COMP_COLS + self.ROUND_COLS:
            columns[col].append(one)
        return columns

    def _one_product_columns(self, q_bits, m_bits, zero, cut):
        columns = [[] for _ in range(OUT_WIDTH)]
        x_and = self._not(self._and(m_bits[0], m_bits[1]))
        x_or = self._not(self._or(m_bits[0], m_bits[1]))
        d = []

        def place(col, node):
            if col >= cut:
                columns[col].append(node)

        for step in range((WIDTH + 1) // 2):
            # Booth window, high bit first, with top sign extension.
            h = q_bits[min(2 * step + 1, WIDTH - 1)]
            m = q_bits[2 * step]
            low = q_bits[2 * step - 1] if step else zero
            if step == 0:
                one = q_bits[0]
            elif step == 4:
                one = self._and(self._not(m), low)
            else:
                one = self._xor(m, low)
            if step == 4:
                two = zero
                negative = self._and(m, self._not(low))
            elif step == 0:
                two = self._and(self._not(one), q_bits[1])
                negative = q_bits[1]
            else:
                two = self._and(self._not(one), self._xor(h, m))
                negative = q_bits[2 * step + 1]

            q_bits_of_step = 9 if step == 4 else 10
            mk_xor_list = []
            if two != zero:
                mk_xor_list.extend([None, None])
                for k in range(2, 9):
                    mk_xor_list.append(self._xor(q_bits[2 * step + 1], m_bits[k]))

            def get_xor(col):
                return mk_xor_list[min(col, len(mk_xor_list) - 1)]

            if two == zero:
                p = x_and
                q = x_or
                a = self._or(self._and(one, m_bits[2]), self._and(negative, self._not(m_bits[2])))
                b = self._or(self._and(one, m_bits[1]), self._and(negative, self._and(p, self._not(q))))
                c = self._or(self._and(self._or(one, negative), m_bits[0]), d[-1])
                d_tmp = self._and(negative, q)
            else:
                p = self._or(self._and(q_bits[2 * step + 1], x_and), self._and(self._not(q_bits[2 * step + 1]), m_bits[1]))
                q = self._and(q_bits[2 * step + 1], x_or)
                a = self._or(self._and(one, get_xor(2)), self._and(two, p))
                b = self._or(self._and(one, self._and(p, self._not(q))), self._and(two, m_bits[0]))
                if step == 0:
                    c = self._and(one, m_bits[0])
                    d_tmp = q
                else:
                    c = self._or(self._and(one, m_bits[0]), d[-1])
                    d_tmp = self._and(self._not(self._and(q_bits[2 * step], q_bits[2 * step - 1])), q)
            d.append(d_tmp)
            place(2 * step, c)
            place(2 * step + 1, b)
            place(2 * step + 2, a)
            if two == zero:
                place(2 * step + 2, d_tmp)
            for k in range(3, q_bits_of_step):
                if two == zero:
                    mk = m_bits[min(k, WIDTH - 1)]
                    val = self._or(self._and(one, mk), self._and(negative, self._not(mk)))
                else:
                    val = self._or(self._and(one, get_xor(k)), self._and(two, get_xor(k - 1)))
                if k == q_bits_of_step - 1:
                    val = self._not(val)
                place(2 * step + k, val)
        return columns

    def _compress_columns(self):
        for col in range(OUT_TOTAL):
            compressor_index = 0
            while len(self._columns[col]) >= 3:
                x0, x1, x2 = (self._columns[col].pop() for _ in range(3))
                if col == 3 and compressor_index <= 1:
                    ac = self._and(x0, x2)
                    b_or_ac = self._or(x1, ac)
                    a_or_c = self._or(x0, x2)
                    carry = self._and(b_or_ac, a_or_c)
                    total = self._xor(b_or_ac, a_or_c)
                else:
                    total, carry = self._add3(x0, x1, x2)
                compressor_index += 1
                self._columns[col].append(total)
                if col + 1 < OUT_TOTAL:
                    self._columns[col + 1].append(carry)

    def _build_outputs(self):
        zero, one = self._zero, self._one
        carry = None
        outputs = []
        for col, bucket in enumerate(self._columns):
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
                outputs.append(self._or(bucket[0], carry) if col <= 6
                               else self._xor(bucket[0], carry))
                carry = self._and(bucket[0], carry)
            else:
                total, carry = self._add3(bucket[0], bucket[1], carry)
                outputs.append(total)
        self.output_ids = [zero] * 6 + outputs[6:18] + [outputs[17]]


def build_circuit():
    return Candidate()._build_circuit()
