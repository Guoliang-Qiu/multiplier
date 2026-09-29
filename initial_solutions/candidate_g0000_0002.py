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

# Generation-6 audit: exact synthesis of the local (P_A,P_B) table returns
# the one-gate OR used by the retained column-4 fusion. Neighboring static
# fusions and compensation placements were evaluated with the unmodified
# evaluator; cheaper trials failed the -57.5 dB constraint.

from multiplier.circuit import Circuit

WIDTH = 9
OUT_WIDTH = 18
OUT_TOTAL = 19
PROD_CUT_A = 4
PROD_CUT_B = 4
COMP_COLS = (10, 11, 13, 15)
# Compensation constant: one ONE leaf in column 5 adds +32 raw units and
# re-centres the one-sided bias of the removed low-column partial products.
ROUND_COLS: tuple[int, ...] = (5,)


def _gate(c: Circuit, kind: str, *inputs: int) -> int:
    """Hash-cons gates and fold identities involving the circuit constants."""
    zero = getattr(c, "_zero", None)
    one = getattr(c, "_one", None)
    if zero is not None and one is not None:
        if kind == "NOT":
            if inputs[0] == zero:
                return one
            if inputs[0] == one:
                return zero
            # NOT(NOT(x)) is x; the construction cache records the inverse.
            inverse = getattr(c, "_not_cache", {})
            prior = inverse.get(inputs[0])
            if prior is not None:
                return prior
        elif kind == "AND":
            a, b = inputs
            if a == zero or b == zero:
                return zero
            if a == one:
                return b
            if b == one:
                return a
            if a == b:
                return a
        elif kind == "OR":
            a, b = inputs
            if a == one or b == one:
                return one
            if a == zero:
                return b
            if b == zero:
                return a
            if a == b:
                return a
        elif kind == "XOR":
            a, b = inputs
            if a == b:
                return zero
            if a == zero:
                return b
            if b == zero:
                return a
            if a == one:
                return _not(c, b)
        # Exact absorption removes redundant output-reachable cones.
        if kind == "OR":
            for operand, other in ((a, b), (b, a)):
                node = c.nodes[other]
                if node.kind == "AND" and operand in node.inputs:
                    return operand
        elif kind == "AND":
            for operand, other in ((a, b), (b, a)):
                node = c.nodes[other]
                if node.kind == "OR" and operand in node.inputs:
                    return operand
    if kind in ("AND", "OR", "XOR") and inputs[1] < inputs[0]:
        inputs = (inputs[1], inputs[0])

    key = (kind, inputs)
    cache = getattr(c, "_local_gate_cache", None)
    if cache is None:
        cache = {}
        c._local_gate_cache = cache
    node = cache.get(key)
    if node is None:
        node = c.add(kind, *inputs)
        cache[key] = node
        if kind == "NOT":
            inverse = getattr(c, "_not_cache", None)
            if inverse is None:
                inverse = {}
                c._not_cache = inverse
            inverse[node] = inputs[0]
    return node


def _and(c, a, b): return _gate(c, "AND", a, b)
def _or(c, a, b): return _gate(c, "OR", a, b)
def _xor(c, a, b):
    """Exact weighted XOR: (a|b)&~(a&b), with global predicate sharing."""
    both = _and(c, a, b)
    either = _or(c, a, b)
    return _and(c, either, _not(c, both))
def _not(c, a): return _gate(c, "NOT", a)


def _fa(c, a, b, cin):
    """Exact seven-cost shared full adder.

    Exhaustive table proof over ``(a,b,cin)`` gives ``total=a^b^cin`` and
    ``carry=majority(a,b,cin)`` for all eight assignments.  The intermediate
    ``xn`` is XNOR(a,cin).  Sharing it with both outputs saves one weighted
    AND/OR gate at every non-constant matrix compressor; NOT remains free.
    The 3-input, 2-output table was also minimized with the exact local
    synthesizer over the AND/OR basis with free input/output complementation
    (six literal inputs, 56 don't-care rows): it is UNSAT at six gates, so this
    seven-gate realization is gate-count optimal for the jointly consumed pair.
    """
    ac = _and(c, a, cin)
    a_or_c = _or(c, a, cin)
    xn = _or(c, ac, _not(c, a_or_c))
    b_or_xn = _or(c, b, xn)
    total = _or(c, _not(c, b_or_xn), _and(c, b, xn))
    carry = _and(c, a_or_c, b_or_xn)
    return total, carry


def _add3(c, x, y, z, zero, one):
    consts = [n for n in (x, y, z) if n in (zero, one)]
    reals = [n for n in (x, y, z) if n not in (zero, one)]
    if not consts: return _fa(c, x, y, z)
    if len(consts) == 1:
        a, b = reals
        if one in consts:
            # Exact a+b+1: carry is OR and sum is XNOR via shared carry.
            carry = _or(c, a, b)
            return _or(c, _and(c, a, b), _not(c, carry)), carry
        # Exact a+b: share carry with the AND/OR/NOT parity form.
        carry = _and(c, a, b)
        return _and(c, _or(c, a, b), _not(c, carry)), carry
    if len(consts) == 2:
        a = reals[0]
        if zero in consts and one in consts: return _not(c, a), a
        if one in consts: return a, one
        return a, zero
    n = consts.count(one)
    return (one if n == 1 else zero), (one if n > 1 else zero)


def _bit(bits, index, zero):
    if index < 0: return zero
    return bits[index] if index < len(bits) else bits[-1]


def _qsub(q, step, zero):
    if step == 0: return q[1], q[0], zero
    if step == 1: return q[3], q[2], q[1]
    if step == 2: return q[5], q[4], q[3]
    if step == 3: return q[7], q[6], q[5]
    return q[8], q[8], q[7]


def _product_columns(
    circuit: Circuit, q_bits: list[int], m_bits: list[int],
    zero: int, one_const: int, cut: int,
) -> list[list[int]]:
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

    x_and = _not(circuit, _and(circuit, m_bits[0], m_bits[1]))
    x_or = _not(circuit, _or(circuit, m_bits[0], m_bits[1]))
    d = []

    # Held column-4 partial products of this cone (fused after the Booth loop).
    fused_step0_col4 = None      # P_A: step-0, k = 4
    fused_step2_col4 = None      # P_B: step-2 ``c`` term

    for step in range(num_steps):
        h, m, low = _qsub(q_bits, step, zero)
        if step == 0:
            # step 0: low == 0 so one = XOR(q0, 0) == q0 exactly.
            one = q_bits[0]
        elif step == 4:
            one = _and(circuit, _not(circuit, m), low)
        else:
            one = _xor(circuit, m, low)
        if step == 4:
            # last Booth step: h == m == q8 so ``two`` == ZERO (its subtree and
            # every AND(two,*) term are dropped), and
            # negative = q8 & NOT(q8 & q7) == q8 & NOT(q7)  (exact collapse).
            two = zero
            negative =  _and(circuit, m, _not(circuit, low))
        elif step == 0:
            # step 0: low == 0 so negative == q1 exactly, and
            # two = NOT(q0) & (q1 ^ q0) == NOT(q0) & q1  (exact collapse).
            two = _and(circuit, _not(circuit, one), q_bits[1])
            negative = q_bits[1]
        else:
            two = _and(circuit, _not(circuit, one), _xor(circuit, h, m))
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
                mk_xor_list.append(_xor(circuit, q_bits[2 * step + 1], _bit(m_bits, k, zero)))

        def get_xor(col: int):
            if col >= len(mk_xor_list):
                return mk_xor_list[-1]
            return mk_xor_list[col]

        if two == zero:
            p = x_and
            q = x_or

            a = _or(circuit, _and(circuit, one, m_bits[2]), _and(circuit, negative, _not(circuit, m_bits[2])))
            b = _or(circuit, _and(circuit, one, m_bits[1]), _and(circuit, negative, _and(circuit, p, _not(circuit, q))))
            c = _or(circuit, _and(circuit, _or(circuit, one, negative), m_bits[0]), d[-1])
            d_tmp = _and(circuit, negative, q)
        else:
            p = _or(circuit, _and(circuit, q_bits[2 * step + 1], x_and), _and(circuit, _not(circuit, q_bits[2 * step + 1]), m_bits[1]))
            q = _and(circuit, q_bits[2 * step + 1], x_or)

            a = _or(circuit, _and(circuit, one, get_xor(2)), _and(circuit, two, p))
            b = _or(circuit, _and(circuit, one, _and(circuit, p, _not(circuit, q))), _and(circuit, two, m_bits[0]))

            if step == 0:
                c = _and(circuit, one, m_bits[0])
                d_tmp = q
            else:
                c = _or(circuit, _and(circuit, one, m_bits[0]), d[-1])
                d_tmp = _and(circuit, _not(circuit, _and(circuit, q_bits[2 * step], q_bits[2 * step - 1])), q)

        d.append(d_tmp)

        if step == 2:
            # P_B: held for the generation-time column-4 fusion.
            fused_step2_col4 = c
        else:
            place(2 * step, c)
        place(2 * step + 1, b)
        if step != 1:
            place(2 * step + 2, a)
        else:
            # step 1's column-4 partial product is removed by this mutation.
            pass

        if two == zero:
            place(2 * step + 2, d_tmp)

        for k in range(3, q_bits_of_step):
            if two == zero:
                mk = _bit(m_bits, k, zero)
                val = _or(circuit, _and(circuit, one, mk), _and(circuit, negative, _not(circuit, mk)))
            else:
                val = _or(circuit, _and(circuit, one, get_xor(k)), _and(circuit, two, get_xor(k - 1)))
            if k == q_bits_of_step - 1:
                val = _not(circuit, val)
            if step == 0 and k == 4:
                # P_A: held for the generation-time column-4 fusion.
                fused_step0_col4 = val
            else:
                place(2 * step + k, val)

    if fused_step0_col4 is not None and fused_step2_col4 is not None:
        # Fused cell synthesised with the exact local synthesizer: a single OR
        # gate returns to the current column; the carry-like term into column 5
        # is the constant 0 (the exact two-output fusion would cost 4 gates).
        place(4, _or(circuit, fused_step2_col4, fused_step0_col4))

    return columns


def _build_circuit(_layout_only=False, _columns=None):
    c = Circuit(output_width=OUT_TOTAL)
    zero, one = c.add("ZERO"), c.add("ONE")
    c._zero, c._one = zero, one
    a = [c.add("IN_A") for _ in range(WIDTH)]
    b = [c.add("IN_B") for _ in range(WIDTH)]
    x = [c.add("IN_C") for _ in range(WIDTH)]
    d = [c.add("IN_D") for _ in range(WIDTH)]
    c.input_ids = a + b + x + d
    columns = [[] for _ in range(OUT_TOTAL)]
    # Use the qgl cone for both products as the feasible structural baseline;
    # the inherited mixed-cone crossover had excessive uncorrelated low error.
    for builder, left, right, cut in (
        (_product_columns, a, b, PROD_CUT_A),
        (_product_columns, x, d, PROD_CUT_B),
    ):
        product = builder(c, right, left, zero, one, cut)
        for col in range(OUT_WIDTH): columns[col].extend(product[col])
    for col in COMP_COLS + ROUND_COLS: columns[col].append(one)

    if _layout_only:
        return c, [list(bucket) for bucket in columns]
    if _columns is not None:
        columns = [list(bucket) for bucket in _columns]

    for col in range(OUT_TOTAL):
        compressor_index = 0
        while len(columns[col]) >= 3:
            x0, x1, x2 = columns[col].pop(), columns[col].pop(), columns[col].pop()
            if col == 3 and compressor_index <= 1:
                # Joint approximate truth table (x0,x1,x2 -> sum,carry):
                # exact parity/majority on 000..110; on 111 only, sum is
                # suppressed to zero while carry remains one.  This precise
                # occurrence consumes one of the first two column-3 triples.
                ac = _and(c, x0, x2)
                b_or_ac = _or(c, x1, ac)
                a_or_c = _or(c, x0, x2)
                carry = _and(c, b_or_ac, a_or_c)
                total = _xor(c, b_or_ac, a_or_c)
            else:
                total, carry = _add3(c, x0, x1, x2, zero, one)
            compressor_index += 1
            columns[col].append(total)
            if col + 1 < OUT_TOTAL: columns[col + 1].append(carry)

    carry = None
    outputs = []
    for col, bucket in enumerate(columns):
        bucket = bucket or [zero]
        if carry is None:
            outputs.append(bucket[0] if len(bucket) == 1 else _xor(c, bucket[0], bucket[1]))
            if len(bucket) > 1: carry = _and(c, bucket[0], bucket[1])
        elif len(bucket) == 1 and bucket[0] == zero:
            outputs.append(carry); carry = zero
        elif len(bucket) == 1 and bucket[0] == one:
            outputs.append(_not(c, carry))
        elif len(bucket) == 1:
            # Exact half-adder sum for every column.  The parent replaced the
            # sum of the (single-entry) low-column buckets by OR, which was
            # nearly free there; with the fused column-4 group the first
            # single-entry bucket is column 6, i.e. the rounding bit itself, so
            # that approximation now costs about 2.4 dB and is withdrawn.
            outputs.append(_xor(c, bucket[0], carry))
            carry = _and(c, bucket[0], carry)
        else:
            total, carry = _add3(c, bucket[0], bucket[1], carry, zero, one)
            outputs.append(total)
    # Bits 0..5 are discarded by the evaluator.  Only replace the final output
    # references: carry nodes were already constructed separately in the loop.
    c.output_ids = [zero] * 6 + outputs[6:18] + [outputs[17]]
    return c


def build_circuit(_layout_only=False):
    circuit = _build_circuit(_layout_only)
    if _layout_only:
        return circuit
    return circuit


def build_partial_product_layout():
    return build_circuit(_layout_only=True)


def build_circuit_from_columns(circuit, columns):
    return _build_circuit(_columns=columns)
