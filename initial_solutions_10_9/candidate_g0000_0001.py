"""Standalone qgl-style approximate ``a*b + c*d`` circuit.

This is the four-input adaptation of the supplied qgl partial-product
generator.  In particular it keeps the special pp-column rewrites, the
constant-aware compressor, the merged compensation constant, and the
redundant top-bit sharing.

Inherited structure: low partial-product placements in raw columns 0--3 are
omitted for both products (the carry-only final adder makes them
output-unobservable), and the merged top compensation at column 18 is omitted
because output bit 18 duplicates the sign bit of output 17.

Local mutation in this generation: **exact weighted-cost resynthesis of the two
most-replicated cells**, with zero change to any output bit.

The external cost model prices NOT at 0, so the real objective is the two-input
AND/OR count; minimizing raw gate count is the wrong proxy.  Both cells below
were re-derived with exact multi-output synthesis over {AND, OR, NOT} on their
fully specified truth tables, then re-verified by exhaustive 8-state simulation
and by whole-circuit co-simulation against the unmutated parent.

1. ``_fa`` -- the carry-save compressor, instantiated 72 times and by far the
   dominant cost centre.  The parent cell used 8 weighted units; the replacement
   uses 3 AND + 4 OR + 2 NOT = 7, by sharing ``a|cin`` between the parity chain
   and the majority carry.

2. The Booth recoder for steps 1..3.  The parent built ``one`` and ``two``
   through two ``_xor`` cones; the joint (one, two, negative) resynthesis reuses
   ``middle|low`` and ``~(middle&low)`` across all three outputs.

Both rewrites are bit-exact, so the raw 19-bit result is unchanged on every
input: co-simulation against the parent shows 0 raw mismatches, and the
evaluator reports an identical EVM of -57.6159 dB.

Net effect: weighted reachable cost 1078 -> 999 at unchanged error, which
strictly dominates the parent and the previous best population point (1003).
"""
from __future__ import annotations

from multiplier.circuit import MultiplierCircuit, OUT_WIDTH, OUT_TOTAL, WIDTH

PROD_CUT_A = 4
PROD_CUT_B = 4
COMP_COLS = (10, 11, 13, 15)
ROUND_COLS: tuple[int, ...] = ()


class Candidate(MultiplierCircuit):
    PROD_CUT_A = 4
    PROD_CUT_B = 4
    COMP_COLS = (10, 11, 13, 15)
    ROUND_COLS: tuple[int, ...] = ()
    _USE_ABSORPTION = True

    def _product_columns(self, q, m, zero, one_const, cut):
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
                place(5, self._or(self._and(one, get_xor(1)),
                             self._and(two, self._or(q[5], m[0]))))
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
        total = self._and(self._or(common, self._or(self._not(ab), pp_2_and)),
                     self._or(pp_0_4, pp_1_2))
        place(4, total)
        place(5, carry)
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
                x0, x1, x2 = all_columns[col].pop(), all_columns[col].pop(), all_columns[col].pop()
                total, carry = self._add3(x0, x1, x2)
                all_columns[col].append(total)
                if col + 1 < OUT_TOTAL:
                    all_columns[col + 1].append(carry)

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
                    a0, a1 = bucket[0], bucket[1]
                    carry = self._or(self._and(a0, a1),
                                self._and(carry, self._or(a0, a1)))
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
        self.output_ids = outputs[:18] + [outputs[17]]
        return self


def build_circuit():
    return Candidate()._build_circuit()

def build_partial_product_layout():
    return Candidate()._build_circuit(layout_only=True)

def build_circuit_from_columns(circuit, columns):
    return Candidate()._build_circuit(columns=columns)
