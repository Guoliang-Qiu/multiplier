"""Standalone three-stage candidate; generic arithmetic is inherited from tap2."""
from __future__ import annotations
from multiplier.circuit.multiplier.tap2_9bit_multiplier import Circuit, MultiplierCircuit, WIDTH, OUT_WIDTH, OUT_TOTAL
OUT_WIDTH = 19

class Candidate(MultiplierCircuit):
    _USE_ABSORPTION = True

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

    def _product_columns(self, a, b, c, d, zero, one):
        columns = [[] for _ in range(OUT_WIDTH)]
        self._add_product(columns, a, b, zero, one)
        self._add_product(columns, c, d, zero, one)
        return columns

    def _add_product(self, columns, multiplicand, multiplier, zero, one):
        """Emit a complete exact product with the optimized column-builder style."""
        groups = (WIDTH + 1) // 2

        def place(column, node):
            columns[column].append(node)
        for group in range(groups):
            offset = 2 * group
            high, middle, low = self._qsub(multiplier, group, zero)
            top = False
            if top:
                one_sel = self._xor(middle, low)
                two_sel = None
                negative = middle
            else:
                middle_or_low = self._or(middle, low)
                middle_and_low = self._and(middle, low)
                not_middle_and_low = self._not(middle_and_low)
                one_sel = self._and(middle_or_low, not_middle_and_low)
                two_sel = self._and(self._not(self._and(high, middle_or_low)), self._or(high, middle_and_low))
                negative = high
            for source in range(WIDTH + 1):
                x = self._bit(multiplicand, source, zero)
                if two_sel is None or source == 0:
                    magnitude = self._and(x, one_sel)
                else:
                    y = self._bit(multiplicand, source - 1, zero)
                    magnitude = self._or(self._and(x, one_sel), self._and(y, two_sel))
                value = self._xor(magnitude, negative)
                if source == WIDTH and (not top):
                    value = self._not(value)
                place(offset + source, value)
            place(offset, negative)
        compensation = -sum((1 << 2 * group + WIDTH for group in range(groups) if 2 * group + WIDTH < OUT_WIDTH - 1)) & (1 << OUT_WIDTH) - 1
        for column in range(OUT_WIDTH):
            if compensation >> column & 1:
                columns[column].append(one)

    def _compress_columns(self):
        columns = self._columns
        zero = next((i for i, node in enumerate(self.nodes) if node.kind == 'ZERO'))
        one = next((i for i, node in enumerate(self.nodes) if node.kind == 'ONE'))
        for column in range(OUT_WIDTH):
            while len(columns[column]) >= 3:
                x = columns[column].pop()
                y = columns[column].pop()
                z = columns[column].pop()
                total, carry = self._add3(x, y, z)
                columns[column].append(total)
                if column + 1 < OUT_WIDTH:
                    columns[column + 1].append(carry)

    def _build_outputs(self):
        columns = self._columns
        zero, one = (self._zero, self._one)
        carry = None
        outputs = []
        for bucket in columns:
            bucket = bucket or [zero]
            if carry is None:
                if len(bucket) == 1:
                    outputs.append(bucket[0])
                else:
                    outputs.append(self._xor(bucket[0], bucket[1]))
                    carry = self._and(bucket[0], bucket[1])
            elif len(bucket) == 1:
                outputs.append(self._xor(bucket[0], carry))
                carry = self._and(bucket[0], carry)
            else:
                total, carry = self._add3(bucket[0], bucket[1], carry)
                outputs.append(total)
        self.output_ids = outputs

def build_circuit():
    return Candidate()._build_circuit()
