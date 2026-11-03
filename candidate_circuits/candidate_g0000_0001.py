"""Standalone three-stage candidate; generic arithmetic is inherited from tap2."""
from __future__ import annotations
from multiplier.circuit.multiplier.tap2_9bit_multiplier import Circuit, MultiplierCircuit, WIDTH, OUT_WIDTH, OUT_TOTAL

class Candidate(MultiplierCircuit):
    _USE_ABSORPTION = True
    PROD_CUT_A = 4
    PROD_CUT_B = 4
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

    def _one_product_columns(self, q, m, zero, one_const, cut):
        columns = [[] for _ in range(OUT_WIDTH)]
        pp_0_4 = pp_1_2 = common = pp_2_and = None

        def place(col, node):
            if col >= cut:
                columns[col].append(node)
        for step in range((WIDTH + 1) // 2):
            h, middle, low = self._qsub(q, step, zero)
            if step == 0:
                one = q[0]
                two = self._and(self._not(one), q[1])
                negative = q[1]
            elif step == 4:
                one = self._and(self._not(middle), low)
                two = zero
                negative = self._and(middle, self._not(low))
            else:
                ml_or = self._or(middle, low)
                ml_and = self._and(middle, low)
                n_ml_and = self._not(ml_and)
                one = self._and(ml_or, n_ml_and)
                two = self._and(self._not(self._and(h, ml_or)), self._or(h, ml_and))
                negative = self._and(h, n_ml_and)
            q_width = 9 if step == 4 else 10
            xors = []
            if two != zero:
                xors = [self._xor(q[2 * step + 1], self._bit(m, k, zero)) for k in range(9)]

            def get_xor(k):
                return xors[min(k, len(xors) - 1)]
            if step >= 3:
                if two == zero:
                    m0 = self._bit(m, 0, zero)
                    value = self._or(self._and(one, m0), self._and(negative, self._not(m0)))
                else:
                    value = self._or(self._and(one, get_xor(0)), self._and(two, q[2 * step + 1]))
                place(2 * step, value)
                place(2 * step, negative)
            activity = None
            if step == 0:
                pp_0_4 = self._or(q[1], q[0])
                activity = pp_0_4
                place(5, self._or(self._and(one, get_xor(5)), self._and(two, self._not(m[4]))))
            elif step == 1:
                pp_1_2 = self._or(one, two)
                activity = pp_1_2
                place(5, self._or(self._and(one, get_xor(3)), self._and(two, get_xor(2))))
            elif step == 2:
                place(5, self._or(self._and(one, get_xor(1)), self._and(two, self._or(q[5], m[0]))))
                activity = self._or(one, two)
                common = self._and(activity, self._and(q[5], self._not(m[0])))
                pp_2_and = self._and(one, m[0])
            for k in range(max(1, 6 - step * 2), q_width):
                if two == zero:
                    mk = self._bit(m, k, zero)
                    value = self._or(self._and(one, mk), self._and(negative, self._not(mk)))
                    if k == q_width - 1:
                        value = self._not(value)
                elif k == q_width - 1:
                    if activity is None:
                        activity = self._or(one, two)
                    value = self._not(self._and(activity, get_xor(k)))
                else:
                    value = self._or(self._and(one, get_xor(k)), self._and(two, get_xor(k - 1)))
                place(2 * step + k, value)
        ab = self._and(pp_0_4, pp_1_2)
        carry = self._or(common, ab)
        total = self._and(self._or(common, self._or(self._not(ab), pp_2_and)), self._or(pp_0_4, pp_1_2))
        place(4, total)
        place(5, carry)
        return columns

    def _product_columns(self, a, b, c, d, zero, one):
        all_columns = [[] for _ in range(OUT_TOTAL)]
        for left, right, cut in ((a, b, self.PROD_CUT_A), (c, d, self.PROD_CUT_B)):
            product = self._one_product_columns(right, left, zero, one, cut)
            for col in range(OUT_WIDTH):
                all_columns[col].extend(product[col])
        for col in self.COMP_COLS + self.ROUND_COLS:
            all_columns[col].append(one)
        return all_columns

    def _compress_columns(self):
        all_columns = self._columns
        zero, one = (self._zero, self._one)
        for col in range(OUT_TOTAL):
            while len(all_columns[col]) >= 3:
                x0, x1, x2 = (all_columns[col].pop(), all_columns[col].pop(), all_columns[col].pop())
                total, carry = self._add3(x0, x1, x2)
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
            if col < 6:
                outputs.append(zero)
                if carry is None:
                    if len(bucket) > 1:
                        carry = self._and(bucket[0], bucket[1])
                elif len(bucket) == 1 and bucket[0] == zero:
                    carry = zero
                elif len(bucket) == 1 and bucket[0] == one:
                    pass
                elif len(bucket) == 1:
                    carry = self._and(bucket[0], carry)
                else:
                    a0, a1 = (bucket[0], bucket[1])
                    carry = self._or(self._and(a0, a1), self._and(carry, self._or(a0, a1)))
                continue
            if carry is None:
                if len(bucket) == 1:
                    outputs.append(bucket[0])
                else:
                    total, carry = self._ha(bucket[0], bucket[1])
                    outputs.append(total)
            elif len(bucket) == 1 and bucket[0] == zero:
                outputs.append(carry)
                carry = zero
            elif len(bucket) == 1 and bucket[0] == one:
                outputs.append(self._not(carry))
            elif len(bucket) == 1:
                total, carry = self._ha(bucket[0], carry)
                outputs.append(total)
            else:
                total, carry = self._add3(bucket[0], bucket[1], carry)
                outputs.append(total)
        self.output_ids = outputs

def build_circuit():
    return Candidate()._build_circuit()
