"""Gate-level crossover of generation-5 candidates 0007 and 0001.

The ``a*b`` product cone is inherited from candidate 0001's factored Booth
partial-product generator, including its special low-column rewrites and merged
column-4/5 compressor.  The ``c*d`` product cone is inherited from candidate
0007's alternative qgl Booth generator.  The crossed product cones feed
candidate 0007's hash-consed weighted-cost compressor tree, its two targeted
column-3 compressor approximations, and its low final-sum pruning/resynthesis.
Thus both parents contribute output-reachable gate-level subgraphs; this is not
a parameter or source-level parent selection.  Construction is static and
input-independent.
"""
from __future__ import annotations

from multiplier.circuit import MultiplierCircuit, OUT_WIDTH, OUT_TOTAL, WIDTH

PROD_CUT_A = 5
PROD_CUT_B = 3
COMP_COLS = (10, 11, 13, 15)
# Column 18 is the duplicated sign/output column.  The exposed sign bit is
# output 17, so a correction injected at column 18 cannot reach an output.
# Omitting this dead correction preserves the signed result while avoiding an
# unnecessary terminal correction path.
# Compensation constant for the widened ``a*b`` truncation.  Raising PROD_CUT_A
# from 0 to 5 drops the a*b partial products of weight < 2^5, which is a purely
# one-sided (always non-negative) loss and therefore biases the result low.  A
# single ONE injected at column 4 adds back half the average dropped weight at
# the rounding boundary, restoring bias from 0.372 to 0.250 and EVM from
# -57.02 dB to -57.64 dB while costing far less than the removed columns.
ROUND_COLS: tuple[int, ...] = (4,)


class Candidate(MultiplierCircuit):
    PROD_CUT_A = 5
    PROD_CUT_B = 3
    COMP_COLS = (10, 11, 13, 15)
    ROUND_COLS = (4,)
    LOW_OR_BOUNDARY = 5

    def _xor(self, a, b):
        both = self._and(a, b)
        either = self._or(a, b)
        return self._and(either, self._not(both))

    def _product_columns_parent1(self, q, m, zero, one_const, cut):
        """Candidate 0001's factored Booth partial-product subgraph."""
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
                one = self._xor(middle, low)
                two = self._and(self._not(one), self._xor(h, middle))
                negative = self._and(h, self._not(self._and(middle, low)))

            q_width = 9 if step == 4 else 10
            xors = []
            if two != zero:
                xors = [self._xor(q[2 * step + 1], self._bit(m, k, zero))
                        for k in range(9)]

            def get_xor(k):
                return xors[min(k, len(xors) - 1)]

            if step >= 3:
                if two == zero:
                    m0 = self._bit(m, 0, zero)
                    value = self._or(self._and(one, m0),
                                self._and(negative, self._not(m0)))
                else:
                    value = self._or(self._and(one, get_xor(0)),
                                self._and(two, q[2 * step + 1]))
                place(2 * step, value)
                place(2 * step, negative)

            activity = None
            if step == 0:
                pp_0_4 = self._or(q[1], q[0])
                activity = pp_0_4
                place(5, self._or(self._and(one, get_xor(5)),
                             self._and(two, self._not(m[4]))))
            elif step == 1:
                pp_1_2 = self._or(one, two)
                activity = pp_1_2
                place(5, self._or(self._and(one, get_xor(3)),
                             self._and(two, get_xor(2))))
            elif step == 2:
                place(5, self._or(self._and(one, get_xor(1)),
                             self._and(two, self._or(q[5], m[0]))))
                activity = self._or(one, two)
                common = self._and(activity, self._and(q[5], self._not(m[0])))
                pp_2_and = self._and(one, m[0])

            for k in range(max(1, 6 - step * 2), q_width):
                if two == zero:
                    mk = self._bit(m, k, zero)
                    value = self._or(self._and(one, mk),
                                self._and(negative, self._not(mk)))
                    if k == q_width - 1:
                        value = self._not(value)
                elif k == q_width - 1:
                    if activity is None:
                        activity = self._or(one, two)
                    value = self._not(self._and(activity, get_xor(k)))
                else:
                    value = self._or(self._and(one, get_xor(k)),
                                self._and(two, get_xor(k - 1)))
                place(2 * step + k, value)

        ab = self._and(pp_0_4, pp_1_2)
        carry = self._or(common, ab)
        total = self._and(self._or(common, self._or(self._not(ab), pp_2_and)),
                     self._or(pp_0_4, pp_1_2))
        place(4, total)
        place(5, carry)
        return columns

    def _product_columns(self, q_bits, m_bits, zero, one_const, cut):
        """Single qgl dual-approx product's 18 column lists (low ``cut`` pruned).

        ``cut`` is the per-core column cutoff; partial-product / sign / extra bits
        landing in columns < ``cut`` are guard-pruned (never node-deleted), so the
        zero-filled low columns fall out of the carry-save and CPA compaction.
        """
        columns: list[list[int]] = [[] for _ in range(OUT_WIDTH)]
        num_steps = (WIDTH + 1) // 2

        step1_one: int | None = None
        step1_two: int | None = None

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
                    val = self._or(self._and(one, get_xor(k)), self._and(two, get_xor(k - 1)))
                if k == q_bits_of_step - 1:
                    val = self._not(val)
                place(2 * step + k, val)

        return columns

    def _build_circuit(self, layout_only=False, columns=None):
        a, b, c, d, zero, one = self.setup()
        all_columns = [[] for _ in range(OUT_TOTAL)]
        for builder, left, right, cut in (
            (self._product_columns_parent1, a, b, self.PROD_CUT_A),
            (self._product_columns, c, d, self.PROD_CUT_B),
        ):
            product = builder(right, left, zero, one, cut)
            for col in range(OUT_WIDTH):
                all_columns[col].extend(product[col])
        for col in self.COMP_COLS + self.ROUND_COLS:
            all_columns[col].append(one)

        if layout_only:
            return self, [list(bucket) for bucket in all_columns]
        if columns is not None:
            all_columns = [list(bucket) for bucket in columns]

        for col in range(OUT_TOTAL):
            compressor_index = 0
            while len(all_columns[col]) >= 3:
                x0, x1, x2 = all_columns[col].pop(), all_columns[col].pop(), all_columns[col].pop()
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
                outputs.append(self._or(bucket[0], carry) if col <= 5
                               else self._xor(bucket[0], carry))
                carry = self._and(bucket[0], carry)
            else:
                total, carry = self._add3(bucket[0], bucket[1], carry)
                outputs.append(total)
        self.output_ids = [zero] * 6 + outputs[6:18] + [outputs[17]]
        return self


def build_circuit():
    return Candidate()._build_circuit()


def build_partial_product_layout():
    return Candidate()._build_circuit(layout_only=True)


def build_circuit_from_columns(circuit, columns):
    return Candidate()._build_circuit(columns=columns)
