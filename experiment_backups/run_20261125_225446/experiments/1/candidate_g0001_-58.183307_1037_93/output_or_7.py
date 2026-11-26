"""Standalone three-stage candidate; generic arithmetic is inherited from tap2."""
from __future__ import annotations
from tools.circuit_kit.circuit.multiplier.tap2_9bit_multiplier import MultiplierCircuit, WIDTH, OUT_WIDTH, OUT_TOTAL

class Candidate(MultiplierCircuit):
    PROD_CUT_A = 4
    PROD_CUT_B = 3
    COMP_COLS = (10, 11, 13, 15)
    ROUND_COLS = ()


    def _mux_xor(self, a, b, c, d, e):
        # Gate-only realization of the inherited 5-port MUX_XOR functionality.
        return self._xor(self._or(self._and(a, b), self._and(c, d)), e)

    def _xor(self, a, b):
        # Parent A: shared AND/OR XNOR decomposition, cost 3 with reusable terms.
        both = self._and(a, b)
        either = self._or(a, b)
        return self._and(either, self._not(both))

    @staticmethod
    def _bit(bits, index, zero):
        if index < 0:
            return zero
        return bits[min(index, len(bits) - 1)]

    @staticmethod
    def _qsub(q, step, zero):
        return (q[min(2 * step + 1, len(q) - 1)], q[2 * step], q[2 * step - 1] if step else zero)

    def _one_product_columns(self, q_bits, m_bits, zero, cut):
        """Single qgl dual-approx product's 18 column lists (low ``cut`` pruned)."""
        columns: list[list[int]] = [[] for _ in range(OUT_WIDTH)]
        num_steps = (WIDTH + 1) // 2
        x_and = self._not(self._and(m_bits[0], m_bits[1]))
        x_or = self._not(self._or(m_bits[0], m_bits[1]))
        d = []
        for step in range(num_steps):
            h, m, low = self._qsub(q_bits, step, zero)
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

            def place(col, node):
                if col < cut:
                    return
                columns[col].append(node)
            mk_xor_list = []
            if two != zero:
                for k in range(2):
                    mk_xor_list.append(None)
                for k in range(2, 9):
                    mk_xor_list.append(self._xor(q_bits[2 * step + 1], self._bit(m_bits, k, zero)))

            def get_xor(col):
                if col >= len(mk_xor_list):
                    return mk_xor_list[-1]
                return mk_xor_list[col]
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
                # Digit selection is exclusive: move the negative toggle into
                # e of a MUX_XOR and avoid the dedicated bit-2 XOR.
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
                    mk = self._bit(m_bits, k, zero)
                    val = self._or(self._and(one, mk), self._and(negative, self._not(mk)))
                else:
                    if step in (0, 1, 2, 3) and 3 <= k <= 8 and k < q_bits_of_step - 1:
                        # For every non-top row, mutually exclusive Booth digits
                        # expose (one & bit[k]) | (two & bit[k-1]); sign
                        # correction toggles precisely the selected digit.
                        cell_neg = negative if step == 0 else self._and(negative, self._or(one, two))
                        # Shared kit port order: (a, b, c, d, e).
                        val = self._or(self._and(one, get_xor(k)),
                                       self._and(two, get_xor(k - 1)))
                    elif k == q_bits_of_step - 1 and step < 4:
                        # At the saturated top cell get_xor(9) == get_xor(8);
                        # factor the common XOR signal and reuse the sign guard.
                        val = self._and(self._or(one, two), get_xor(k - 1))
                    else:
                        val = self._or(self._and(one, get_xor(k)), self._and(two, get_xor(k - 1)))
                if k == q_bits_of_step - 1:
                    val = self._not(val)
                place(2 * step + k, val)
        return columns

    def _product_columns_before_compensation(self, a, b, c, d, zero, one):
        all_columns = [[] for _ in range(OUT_TOTAL)]
        for left, right, cut in ((a, b, self.PROD_CUT_A), (c, d, self.PROD_CUT_B)):
            product = self._one_product_columns(right, left, zero, cut)
            for col in range(OUT_WIDTH):
                all_columns[col].extend(product[col])
        for col in self.COMP_COLS + self.ROUND_COLS:
            all_columns[col].append(one)
        return all_columns

    def _compress_columns(self):
        # The inherited exact reference compression uses the same LIFO order.
        self._compress_columns_reference()

    def _build_outputs(self):
        all_columns = self._columns
        zero, one = (self._zero, self._one)
        carry = None
        outputs = []
        for col, bucket in enumerate(all_columns):
            bucket = bucket or [zero]
            if carry is None:
                outputs.append(bucket[0] if len(bucket) == 1 else self._ha(bucket[0], bucket[1])[0])
                if len(bucket) > 1:
                    carry = self._and(bucket[0], bucket[1])
            elif len(bucket) == 1 and bucket[0] == zero:
                outputs.append(carry)
                carry = zero
            elif len(bucket) == 1 and bucket[0] == one:
                outputs.append(self._not(carry))
            elif len(bucket) == 1:
                if col <= 7:
                    outputs.append(self._or(bucket[0], carry))
                    carry = self._and(bucket[0], carry)
                else:
                    total, carry = self._ha(bucket[0], carry)
                    outputs.append(total)
            else:
                total, carry = self._add3(bucket[0], bucket[1], carry)
                outputs.append(total)
        self.output_ids = [zero] * 6 + outputs[6:18] + [outputs[17]]

    def _product_columns_before_compensation_previous(self, a, b, c, d, zero, one):
        """Generate partial products, remove selected slots and append G(X)."""
        columns = self._product_columns_before_compensation(a, b, c, d, zero, one)
        del columns[3][1]
        del columns[3][0]
        # Reconstruct the observed pre-compression signal by its Boolean
        # definition, rather than fragile allocated node numbers.
        # Shannon factor: G=(D0&C3) XOR (D1&(D0|~C2));
        # MUX_XOR uses (a,b,c,d,e) with e XOR ((a&b)|(c&d)).
        g_0 = self._mux_xor(d[1], d[0], d[1], self._not(c[2]),
                            self._and(d[0], c[3]))
        # The D1 guard makes D1 & (C2 XOR D1) == D1 & ~C2.
        columns[4].append(g_0)
        return columns

    def _product_columns(self, a, b, c, d, zero, one):
        """Generate partial products, remove selected slots and append G(X)."""
        columns = self._product_columns_before_compensation_previous(a, b, c, d, zero, one)
        del columns[4][6]
        # The deleted slot is replaced by the explicit unit compensation bit.
        columns[4].append(one)
        return columns

def build_circuit():
    return Candidate()._build_circuit()
