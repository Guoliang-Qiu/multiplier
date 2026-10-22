"""Standalone three-stage candidate; generic arithmetic is inherited from tap2."""
from __future__ import annotations
from multiplier.circuit.multiplier.tap2_9bit_multiplier import Circuit, MultiplierCircuit, WIDTH, OUT_WIDTH, OUT_TOTAL

class Candidate(MultiplierCircuit):
    _USE_ABSORPTION = False
    PROD_CUT_A = 2
    PROD_CUT_B = 2
    COMP_COLS = (10, 11, 13, 15, 18)
    ROUND_COLS: tuple[int, ...] = ()

    def _gate(self, kind, *inputs, absorption=False):
        return super()._gate(kind, *inputs, absorption=absorption or self._USE_ABSORPTION)

    @staticmethod
    def _bit(bits, index, zero):
        if index < 0:
            return zero
        return bits[min(index, len(bits) - 1)]

    @staticmethod
    def _qsub(q, step, zero):
        return (q[min(2 * step + 1, len(q) - 1)], q[2 * step], q[2 * step - 1] if step else zero)

    def _xor(self, a, b):
        both = self._and(a, b)
        either = self._or(a, b)
        return self._and(either, self._not(both))

    def _one_product_columns(self, q, m, zero, one, cut):
        cols: list[list[int]] = [[] for _ in range(OUT_WIDTH)]
        num_steps = (WIDTH + 1) // 2
        step1_one: int | None = None
        step1_two: int | None = None
        x_and = self._not(self._and(m[0], m[1]))
        x_or = self._not(self._or(m[0], m[1]))
        d = []
        for step in range(num_steps):
            h, generated_m, low = self._qsub(q, step, zero)
            if step == 0:
                generated_one = q[0]
            elif step == 4:
                generated_one = self._and(self._not(generated_m), low)
            else:
                generated_one = self._xor(generated_m, low)
            if step == 4:
                two = zero
                negative = self._and(generated_m, self._not(low))
            elif step == 0:
                two = self._and(self._not(generated_one), q[1])
                negative = q[1]
            else:
                two = self._and(self._not(generated_one), self._xor(h, generated_m))
                negative = q[2 * step + 1]
            q_bits_of_step = 9 if step == 4 else 10

            def place(col, node):
                if col < cut:
                    return
                cols[col].append(node)
            mk_xor_list = []
            if two != zero:
                for k in range(2):
                    mk_xor_list.append(None)
                for k in range(2, 9):
                    mk_xor_list.append(self._xor(q[2 * step + 1], self._bit(m, k, zero)))

            def get_xor(col):
                if col >= len(mk_xor_list):
                    return mk_xor_list[-1]
                return mk_xor_list[col]
            if two == zero:
                p = x_and
                generated_q = x_or
                a = self._or(self._and(generated_one, m[2]), self._and(negative, self._not(m[2])))
                b = self._or(self._and(generated_one, m[1]), self._and(negative, self._and(p, self._not(generated_q))))
                c = self._or(self._and(self._or(generated_one, negative), m[0]), d[-1])
                d_tmp = self._and(negative, generated_q)
            else:
                p = self._or(self._and(q[2 * step + 1], x_and), self._and(self._not(q[2 * step + 1]), m[1]))
                generated_q = self._and(q[2 * step + 1], x_or)
                a = self._or(self._and(generated_one, get_xor(2)), self._and(two, p))
                b = self._or(self._and(generated_one, self._and(p, self._not(generated_q))), self._and(two, m[0]))
                if step == 0:
                    c = self._and(generated_one, m[0])
                    d_tmp = generated_q
                else:
                    c = self._or(self._and(generated_one, m[0]), d[-1])
                    d_tmp = self._and(self._not(self._and(q[2 * step], q[2 * step - 1])), generated_q)
            d.append(d_tmp)
            place(2 * step, c)
            place(2 * step + 1, b)
            place(2 * step + 2, a)
            if two == zero:
                place(2 * step + 2, d_tmp)
            for k in range(3, q_bits_of_step):
                if two == zero:
                    mk = self._bit(m, k, zero)
                    val = self._or(self._and(generated_one, mk), self._and(negative, self._not(mk)))
                else:
                    val = self._or(self._and(generated_one, get_xor(k)), self._and(two, get_xor(k - 1)))
                if k == q_bits_of_step - 1:
                    val = self._not(val)
                place(2 * step + k, val)
        if q[0] == self.input_ids[9]:
            cols[2][:] = [zero, one]
        else:
            cols[2][:] = [zero, one]
        assert len(cols[3]) == 2
        node = self.nodes[cols[3][1]]
        assert node.kind == 'OR'
        cols[3][1] = node.inputs[0]
        return cols

    def _product_columns(self, a, b, c, d, zero, one):
        all_columns = [[] for _ in range(OUT_TOTAL)]
        for builder, left, right, cut in ((self._one_product_columns, a, b, self.PROD_CUT_A), (self._one_product_columns, c, d, self.PROD_CUT_B)):
            product = builder(right, left, zero, one, cut)
            for col in range(OUT_WIDTH):
                all_columns[col].extend(product[col])
        for col in self.COMP_COLS + self.ROUND_COLS:
            all_columns[col].append(one)
        return all_columns

    def _compress_columns(self):
        all_columns = self._columns
        zero, one = (self._zero, self._one)
        for col in range(OUT_TOTAL):
            compressor_index = 0
            while len(all_columns[col]) >= 3:
                x0, x1, x2 = (all_columns[col].pop(), all_columns[col].pop(), all_columns[col].pop())
                if col == 3 and compressor_index <= 1:
                    ac = self._and(x0, x2)
                    b_or_ac = self._or(x1, ac)
                    a_or_c = self._or(x0, x2)
                    carry = self._and(b_or_ac, a_or_c)
                    total = self._xor(b_or_ac, a_or_c)
                else:
                    total, carry = self._add3(x0, x1, x2)
                compressor_index += 1
                all_columns[col].append(total)
                if col + 1 < OUT_TOTAL:
                    all_columns[col + 1].append(carry)

    def _build_outputs(self):
        all_columns = self._columns
        zero, one = (self._zero, self._one)
        carry = None
        outputs = []
        for col, bucket in enumerate(all_columns):
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
                outputs.append(self._or(bucket[0], carry) if col <= 6 else self._xor(bucket[0], carry))
                carry = self._and(bucket[0], carry)
            else:
                total, carry = self._add3(bucket[0], bucket[1], carry)
                outputs.append(total)
        self.output_ids = [zero] * 6 + outputs[6:18] + [outputs[17]]

def build_circuit():
    return Candidate()._build_circuit()
