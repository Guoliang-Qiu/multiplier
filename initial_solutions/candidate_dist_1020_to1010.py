"""Standalone three-stage candidate; generic arithmetic is inherited from tap2."""
from __future__ import annotations
from multiplier.circuit.multiplier.tap2_9bit_multiplier import Circuit, MultiplierCircuit, WIDTH, OUT_WIDTH, OUT_TOTAL

class Candidate(MultiplierCircuit):
    _USE_ABSORPTION = True
    PROD_CUT_A = 4
    PROD_CUT_B = 4
    COMP_COLS = (10, 11, 13, 15, 18)
    ROUND_COLS: tuple[int, ...] = ()
    MAJ_COLS = (0, 1, 2, 3)
    EXTRA_ONE = {4: 1}
    SIDE_MASK = 3

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

            def place(col, generated_node):
                if col < cut:
                    return
                cols[col].append(generated_node)
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
        assert len(cols[4]) == 3 and self.nodes[cols[4][2]].kind == 'OR'
        cols[4][2] = self.nodes[cols[4][2]].inputs[1]
        if q[0] == self.input_ids[27]:
            generated_node = self.nodes[cols[4][1]]
            assert generated_node.kind == 'OR'
            cols[4][1] = generated_node.inputs[0]
        side = 1 if q[0] == self.input_ids[9] else 2
        if self.SIDE_MASK & side:
            node = self.nodes[cols[4][0]]
            assert node.kind == 'OR'
            cols[4][0] = node.inputs[0]
        return cols

    def _product_columns(self, a, b, c, d, zero, one):
        all_columns = [[] for _ in range(OUT_TOTAL)]
        for builder, left, right, cut in ((self._one_product_columns, a, b, self.PROD_CUT_A), (self._one_product_columns, c, d, self.PROD_CUT_B)):
            product = builder(right, left, zero, one, cut)
            for col in range(OUT_WIDTH):
                all_columns[col].extend(product[col])
        for col in self.COMP_COLS + self.ROUND_COLS:
            all_columns[col].append(one)
        for col, n in sorted(self.EXTRA_ONE.items()):
            for _ in range(n):
                all_columns[col].append(one)
        return all_columns

    def _compress_columns(self):
        all_columns = self._columns
        zero, one = (self._zero, self._one)
        for col in range(OUT_TOTAL):
            compressor_index = 0
            while len(all_columns[col]) >= 3:
                x0, x1, x2 = (all_columns[col].pop(), all_columns[col].pop(), all_columns[col].pop())
                if col in self.MAJ_COLS and x0 not in (zero, one) and (x1 not in (zero, one)) and (x2 not in (zero, one)):
                    x0x2 = self._and(x0, x2)
                    x1_or_x0x2 = self._or(x1, x0x2)
                    x0_or_x2 = self._or(x0, x2)
                    carry = self._and(x1_or_x0x2, x0_or_x2)
                    compressor_index += 1
                    if col + 1 < OUT_TOTAL:
                        all_columns[col + 1].append(carry)
                    continue
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
                outputs.append(self._or(bucket[0], carry) if col < 7 else self._xor(bucket[0], carry))
                carry = self._and(bucket[0], carry)
            else:
                total, carry = self._add3(bucket[0], bucket[1], carry)
                outputs.append(total)
        self.output_ids = [zero] * 6 + outputs[6:18] + [outputs[17]]

    def xor_operands(self, n):
        node = self.nodes[n]
        if node.kind != 'AND':
            return None
        for a, b in (node.inputs, node.inputs[::-1]):
            na, nb = (self.nodes[a], self.nodes[b])
            if na.kind == 'OR' and nb.kind == 'NOT':
                inner = self.nodes[nb.inputs[0]]
                if inner.kind == 'AND' and set(inner.inputs) == set(na.inputs):
                    return na.inputs
        return None

    def _and(self, a, b):
        for n, x in ((a, b), (b, a)):
            node = self.nodes[n]
            if node.kind != 'NOT':
                continue
            ml = self.xor_operands(node.inputs[0])
            hm = self.xor_operands(x)
            if not ml or not hm:
                continue
            overlap = set(ml) & set(hm)
            if len(overlap) != 1:
                continue
            mid = next(iter(overlap))
            low = next((i for i in ml if i != mid))
            high = next((i for i in hm if i != mid))
            if not all((self.nodes[i].kind in ('IN_B', 'IN_D') for i in (low, mid, high))):
                continue
            union = self._or(mid, low)
            intersection = super()._and(mid, low)
            return super()._and(self._not(super()._and(high, union)), self._or(high, intersection))
        return super()._and(a, b)

def build_circuit():
    return Candidate()._build_circuit()
