"""Standalone qgl-style approximate ``a*b + c*d`` circuit.

This is the four-input adaptation of the supplied qgl partial-product
generator.  In particular it keeps the special pp-column rewrites, the
constant-aware compressor, the merged compensation constant, and the
redundant top-bit sharing.

Local mutations:

* Hash-cons structurally identical gates (including commuted binary operands)
  during construction.  This shares repeated Booth-control and partial-product
  subexpressions without changing their Boolean functions.
* Resynthesize the two low CPA half-adders in columns 4 and 5 by replacing
  their weighted-cost-3 XOR sum gates with OR gates while retaining their exact
  AND carry gates.  Each replacement differs only for local input ``11`` and
  can add respectively 16 or 32 raw Q4.14 units; both lie below the Q4.7 output
  quantum.  The complete-circuit effect is checked by the authoritative
  evaluator rather than inferred from this local bound.
* Jointly resynthesize each non-constant three-input compressor's exact parity
  and majority outputs with a shared 8-gate AND/OR/NOT network found by exact
  truth-table synthesis.  It removes both cost-3 XORs while preserving the
  compressor truth table exactly.
* Jointly resynthesize the two-input-plus-ONE compressor case.  Exact synthesis
  gives carry = a OR b and sum = (a AND b) OR NOT(carry), costing three
  weighted units instead of the prior XNOR-plus-OR cost of four.
"""
from __future__ import annotations

from multiplier.circuit import MultiplierCircuit, OUT_WIDTH, OUT_TOTAL, WIDTH

PROD_CUT_A = 3
PROD_CUT_B = 0
COMP_COLS = (10, 11, 13, 15, 18)
ROUND_COLS: tuple[int, ...] = ()


class Candidate(MultiplierCircuit):
    PROD_CUT_A = 3
    PROD_CUT_B = 0
    COMP_COLS = (10, 11, 13, 15, 18)
    ROUND_COLS = ()
    _USE_ABSORPTION = True

    def _xor(self, a, b):
        both = self._and(a, b)
        either = self._or(a, b)
        return self._and(either, self._not(both))

    def _product_columns(self, q_bits, m_bits, zero, one_const, cut):
        """Single qgl dual-approx product's 18 column lists (low ``cut`` pruned)."""
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
        for left, right, cut in ((a, b, self.PROD_CUT_A), (c, d, self.PROD_CUT_B)):
            product = self._product_columns(right, left, zero, one, cut)
            for col in range(OUT_WIDTH):
                all_columns[col].extend(product[col])
        for col in self.COMP_COLS + self.ROUND_COLS:
            all_columns[col].append(one)

        if layout_only:
            return self, [list(bucket) for bucket in all_columns]
        if columns is not None:
            all_columns = [list(bucket) for bucket in columns]

        for col in range(OUT_TOTAL):
            while len(all_columns[col]) >= 3:
                total, carry = self._add3(all_columns[col].pop(), all_columns[col].pop(), all_columns[col].pop())
                all_columns[col].append(total)
                if col + 1 < OUT_TOTAL:
                    all_columns[col + 1].append(carry)

        carry = None
        outputs = []
        for col, bucket in enumerate(all_columns):
            bucket = bucket or [zero]
            if col < 6:
                outputs.append(zero)
                if len(bucket) > 1:
                    lo, hi = bucket[0], bucket[1]
                    if carry is None:
                        carry = self._and(lo, hi)
                    else:
                        carry = self._or(self._and(lo, hi), self._and(carry, self._or(lo, hi)))
                elif carry is not None:
                    carry = self._and(bucket[0], carry)
                continue
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
                outputs.append(self._xor(bucket[0], carry))
                carry = self._and(bucket[0], carry)
            else:
                total, carry = self._add3(bucket[0], bucket[1], carry)
                outputs.append(total)
        self.output_ids = outputs[:18] + [outputs[17]]
        return self


def build_circuit():
    return Candidate()._build_circuit()

def build_partial_product_layout():
    return Candidate()._build_circuit(layout_only=True)

def build_circuit_from_columns(circuit, columns):
    return Candidate()._build_circuit(columns=columns)
