"""Low-column partial-product fusion in a signed tap-two multiplier.

Parent (verified, recoverable): ``generations/0/candidate_g0000_0006.py``
= this file before the mutation, at weighted cost 1114 / evm_db -58.42313
(two qgl Booth partial-product cones, a shared 3:2 compressor matrix whose
parity/majority outputs share a seven-cost AND/OR/NOT network, compensation
ONEs in ``COMP_COLS``).  The parent was preserved before the experiment and is
byte-identical to the read-only seed above, so it can be restored if this trial
is rejected.

--------------------------------------------------------------------------
Mutation: partial-product fusion in the column-4 region of both product cones
--------------------------------------------------------------------------

Selected partial products (per product cone, identical for ``a*b`` and ``c*d``)

* ``P_A`` -- the Booth step-0 partial product that lands in raw column 4
  (``k = 4`` term of step 0, i.e. ``(one & (q1^m4)) | (two & (q1^m3))`` with
  ``one = q0``, ``two = ~q0 & q1``).
* ``P_B`` -- the Booth step-2 partial product that lands in raw column 4
  (the step-2 ``c`` term, ``(one & m0) | d_1`` with ``one = q4^q3``).
* Their combined arithmetic weight is ``2 * 2^4 = 32`` raw units, i.e. at or
  below raw bit 6 (64), the Q4.7 rounding boundary; the whole three-entry
  column-4 group weighs 48 <= 64.

Local input bits / partitions

* ``P_A`` is determined by the Booth selector bits ``q0, q1`` and the
  multiplicand bits ``m3, m4``; ``P_B`` by ``q1..q4`` and ``m0, m1``.
* The two already-computed predicates ``(P_A, P_B)`` partition the complete
  legal input space into ``2^2 = 4`` partitions (40.77% / 21.88% / 24.92% /
  12.43% of all tap2 samples).  The pattern is a partition label only.

Original exact compressor being replaced

* In the parent the three column-4 partial products of each cone were reduced
  by the exact seven-cost 3:2 compressor ``_fa`` (parity + majority) and the
  surviving column-4 pair then met the column-4 final-adder half adder, whose
  carry is the only column-4 signal that reaches the observable region.  All
  column-4 sum bits are unobservable: output bits 0..5 are hard-wired to ZERO,
  so columns 0..5 are observable only through the carry they inject into
  column 6.  Both ``P_A`` and ``P_B`` were generated independently and consumed
  by that exact compressor.

Candidate fused output columns

* One fused bit returns to the current column (column 4).  The carry-like term
  into column 5 is the constant 0, so no second gate is spent.

Partitioned error-cost table (complete-circuit squared error, real units^2,
compensation +32, all other mutations of this candidate included)

  partition (P_A,P_B) | fused value 0   16    32    48      (16 = 2^4)
  --------------------+------------------------------------
  (0,0)  40.77%       |          104736 116328 139329 182821
  (0,1)  21.88%       |          107772 104736 110675 124904
  (1,0)  24.92%       |          109271 104736 110657 125565
  (1,1)  12.43%       |          112781 105316 104736 106902

  The exact choice (value 32 on the (1,1) partition, i.e. a half adder) costs
  4 weighted gates; the OR fusion (value 16) costs 1 gate and adds only 580
  squared error.  Values 0 and 48 are strictly worse, so the per-partition
  optimum under the cost model is ``P_A | P_B``.

Synthesized fusion subcircuit (exact synthesis, AND/OR/NOT, NOT free)

* Chosen cell: ``fused = OR(P_A, P_B)`` -- exactly 1 weighted gate (the exact
  synthesizer returns a single OR and no cheaper realization exists).
* Rejected exact cell: ``(P_A ^ P_B, P_A & P_B)`` (column-4 / column-5 outputs)
  needs at least 4 weighted gates: the exact synthesizer proves UNSAT at 3.

Everything else in this mutation

1. ``PROD_CUT_A = PROD_CUT_B = 4`` guard-prunes every partial product of both
   cones below column 4 (the eight column-2/column-3 partial products).  This is
   the partial-product removal that pays for the mutation: 1114 -> 1037 weighted
   gates, and the +16 compensation ONE in column 4 is absorbed for free by the
   constant-aware compressor (evm_db -58.18331 at that point).
2. The step-1 partial product that lands in column 4 (the middle entry of the
   column-4 group) is removed as well, and the compensation constant moves to
   column 5 (+32): 1037 -> 1014 weighted gates, evm_db -57.70920.
3. ``P_A`` and ``P_B`` are fused at generation time into ``OR(P_A, P_B)``:
   1014 -> 1005 weighted gates, evm_db -57.64234.
4. The parent's final-adder shortcut (OR instead of XOR for the sum of a
   single-entry low-column bucket) is withdrawn: with the fused column-4 group
   the first single-entry bucket is column 6, i.e. the rounding bit itself, and
   the shortcut would cost about 2.4 dB.  Everything else -- downstream
   carry-save compression, the final adder carry chain, sign handling, the high
   columns and the ``COMP_COLS`` Booth corrections -- is untouched.

Why the complete candidate benefits

* Weighted output-reachable cost 1114 -> 1005 (-109) with evm_db
  -58.42313 -> -57.64234.  The measured total squared error is 105316 against
  the runtime budget 106347 at -57.6 dB, so the runtime constraint holds with
  margin, and the point dominates the parent on cost while staying inside the
  constraint (the parent is preserved and can be restored if this trial is
  rejected).
* Measured with the unmodified ``eval.py`` / ``gate_cost.py``:
  cost 1005 (AND 553, OR 452, XOR 0, NOT 261), evm_db -57.64234,
  mae 0.26685, rmse 0.31661, max_abs_error 0.921875.
"""
from __future__ import annotations

from multiplier.circuit import MultiplierCircuit, OUT_WIDTH, OUT_TOTAL, WIDTH


class Candidate(MultiplierCircuit):
    PROD_CUT_A = 4
    PROD_CUT_B = 4
    COMP_COLS = (10, 11, 13, 15)
    ROUND_COLS: tuple[int, ...] = (5,)
    _USE_ABSORPTION = True

    def _xor(self, a, b):
        both = self._and(a, b)
        either = self._or(a, b)
        return self._and(either, self._not(both))

    def _product_columns(
        self, q_bits, m_bits, zero, one_const, cut,
    ):
        """Single qgl dual-approx product's 18 column lists (low ``cut`` pruned).

        ``cut`` is the per-core column cutoff; partial-product / sign / extra bits
        landing in columns < ``cut`` are guard-pruned (never node-deleted), so the
        zero-filled low columns fall out of the carry-save and CPA compaction.

        Local mutation inside the generator (identical for both product cones):

        * the step-1 partial product that lands in column 4 is no longer placed
          (partial-product removal);
        * the step-0 column-4 partial product (``P_A``) and the step-2 column-4
          partial product (``P_B``) are no longer placed separately: they are fused
          at generation time into the single column-4 signal ``OR(P_A, P_B)``,
          which replaces the exact 3:2 compressor that used to reduce them.  The
          fused bit returns to the current column; no carry-like term is generated.
        """
        columns: list[list[int]] = [[] for _ in range(OUT_WIDTH)]
        num_steps = (WIDTH + 1) // 2

        x_and = self._not(self._and(m_bits[0], m_bits[1]))
        x_or = self._not(self._or(m_bits[0], m_bits[1]))
        d = []

        fused_step0_col4 = None
        fused_step2_col4 = None

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

            def place(col: int, node: int) -> None:
                if col < cut:
                    return
                columns[col].append(node)

            mk_xor_list = []
            if two != zero:
                for k in range(2):
                    mk_xor_list.append(None)
                for k in range(2, 9):
                    mk_xor_list.append(self._xor(q_bits[2 * step + 1], self._bit(m_bits, k, zero)))

            def get_xor(col: int):
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

            if step == 2:
                fused_step2_col4 = c
            else:
                place(2 * step, c)
            place(2 * step + 1, b)
            if step != 1:
                place(2 * step + 2, a)
            else:
                pass

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
                if step == 0 and k == 4:
                    fused_step0_col4 = val
                else:
                    place(2 * step + k, val)

        if fused_step0_col4 is not None and fused_step2_col4 is not None:
            place(4, self._or(fused_step2_col4, fused_step0_col4))

        return columns

    def _build_circuit(self, layout_only=False, columns=None):
        a, b, x, d, zero, one = self.setup()
        all_columns = [[] for _ in range(OUT_TOTAL)]
        for builder, left, right, cut in (
            (self._product_columns, a, b, self.PROD_CUT_A),
            (self._product_columns, x, d, self.PROD_CUT_B),
        ):
            product = builder(right, left, zero, one, cut)
            for col in range(OUT_WIDTH): all_columns[col].extend(product[col])
        for col in self.COMP_COLS + self.ROUND_COLS: all_columns[col].append(one)

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
                if col + 1 < OUT_TOTAL: all_columns[col + 1].append(carry)

        carry = None
        outputs = []
        for col, bucket in enumerate(all_columns):
            bucket = bucket or [zero]
            if carry is None:
                outputs.append(bucket[0] if len(bucket) == 1 else self._xor(bucket[0], bucket[1]))
                if len(bucket) > 1: carry = self._and(bucket[0], bucket[1])
            elif len(bucket) == 1 and bucket[0] == zero:
                outputs.append(carry); carry = zero
            elif len(bucket) == 1 and bucket[0] == one:
                outputs.append(self._not(carry))
            elif len(bucket) == 1:
                outputs.append(self._xor(bucket[0], carry))
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
