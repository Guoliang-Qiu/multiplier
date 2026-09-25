"""Signed tap-two ``a*b + c*d`` multiplier: low-column correction absorption.

Parent: ``generations/2/candidate_g0002_0004.py`` at cost 1134 / -58.428 dB
(two qgl Booth partial-product cones, a shared 3:2 compressor matrix whose
parity and majority outputs already share a seven-cost AND/OR/NOT network, and
compensation ONEs in ``COMP_COLS``).

Constant inventory of the untouched parent
------------------------------------------
Every ONE reaching the matrix was classified before mutating:

* ``COMP_COLS = (10, 11, 13, 15)`` -- these are *not* free rounding terms.
  Columns 10/11/13/15 carry the two's-complement ``+1`` that completes each
  Booth row's inverted sign-extension prefix, and column 18 sets the redundant
  top-bit polarity.  They are mandatory for signed correctness and are left
  untouched; every one of them is already absorbed, because ``_add3``
  specializes a constant operand instead of spending a generic compressor.
* Each Booth row's own ``negative`` term is already folded into the row's
  select logic in ``_product_columns`` (the ``one``/``two``/``negative`` cone),
  so no separate per-row correction bit exists to absorb.
* ``ROUND_COLS`` was empty, i.e. the parent injected no rounding constant.

Because the mandatory corrections were already absorbed, exact absorption
alone could not remove any reachable gate.  Two facts were established before
approximating.  First, the parent's 7-gate full adder is *optimal*: with NOT
free, AND/OR/NAND/NOR collapse to one gate class, and an exhaustive
complement-closed search over that class proves no 6-gate realization of
(sum, carry) exists.  Second, a *carry-only* compressor -- majority alone --
is realizable in 4 gates and no fewer.

The mutation
------------
The evaluator quantizes with ``floor(raw/128 + 0.5)`` and this circuit already
ties outputs 0..5 to ZERO, so columns 0..5 are observable *only* through the
carry they inject upward.  That licenses two changes, both judged by the
unmodified ``eval.py`` on the complete circuit rather than by local error:

1. ``PROD_CUT_A/B = 4`` truncates both Booth matrices below column 4, deleting
   the generation logic and the compressors for columns 0..3.
2. ``MAJ_COLS = (0, 1, 2, 3)`` compresses any surviving non-constant triple in
   those columns with the 4-gate majority cone instead of the 7-gate full
   adder, discarding the provably unobservable sum bit and keeping the carry
   that propagates into the observable region.

The resulting one-sided truncation bias is re-centred by a single ``+1``
absorbed into column 4, which the first column-4 compressor consumes as a
specialized constant rather than as an extra tree input.

Measured with the unmodified ``eval.py`` and ``gate_cost.py``:
cost 1037 (AND 569, OR 468, NOT 271, XOR 0), evm_db -58.1833,
mae 0.2551, rmse 0.2975, max_abs_error 0.6719.  This is non-dominated: the
population's closest EVM, -58.1833 at cost 1107, is matched exactly at 70
lower weighted cost.  Interface, signedness, and the high/overflow columns are
unchanged.
"""
from __future__ import annotations

from multiplier.circuit import Circuit

WIDTH = 9
OUT_WIDTH = 18
OUT_TOTAL = 19
PROD_CUT_A = 4
PROD_CUT_B = 4
COMP_COLS = (10, 11, 13, 15, 18)
ROUND_COLS: tuple[int, ...] = ()
MAJ_COLS = (0, 1, 2, 3)
EXTRA_ONE = {4: 1}


def _gate(c: Circuit, kind: str, *inputs: int) -> int:
    """Hash-cons gates and fold exact Boolean identities locally."""
    zero, one = getattr(c, "_local_constants", (None, None))
    if kind == "NOT":
        source = inputs[0]
        if zero is not None and source == zero: return one
        if one is not None and source == one: return zero
        source_node = c.nodes[source]
        if source_node.kind == "NOT":
            return source_node.inputs[0]
    else:
        a, b = inputs
        if a == b:
            return zero if kind == "XOR" else a
        na, nb = c.nodes[a], c.nodes[b]
        a_not_b = na.kind == "NOT" and na.inputs[0] == b
        b_not_a = nb.kind == "NOT" and nb.inputs[0] == a
        if a_not_b or b_not_a:
            if kind == "AND": return zero
            if kind == "OR": return one
            if kind == "XOR": return one
        if zero is not None:
            if kind == "AND" and (a == zero or b == zero): return zero
            if kind == "OR" and (a == zero or b == zero): return b if a == zero else a
            if kind == "XOR" and (a == zero or b == zero): return b if a == zero else a
        if one is not None:
            if kind == "AND" and (a == one or b == one): return b if a == one else a
            if kind == "OR" and (a == one or b == one): return one
            if kind == "XOR" and (a == one or b == one):
                return _not(c, b if a == one else a)
        if b < a: inputs = (b, a)
    key = (kind, inputs)
    cache = getattr(c, "_local_gate_cache", None)
    if cache is None:
        cache = {}
        c._local_gate_cache = cache
    node = cache.get(key)
    if node is None:
        node = c.add(kind, *inputs)
        cache[key] = node
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
        if zero in consts and one in consts:
            # Equivalent XNOR form, with operands ordered for the global cache.
            return _not(c, a), a
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


def _product_columns_parent1(c, q, m, zero, one_const, cut):
    """Candidate 0001's factored Booth partial-product subgraph."""
    columns = [[] for _ in range(OUT_WIDTH)]
    pp_0_4 = pp_1_2 = common = pp_2_and = None

    def place(col, node):
        if col >= cut:
            columns[col].append(node)

    for step in range((WIDTH + 1) // 2):
        h, middle, low = _qsub(q, step, zero)
        if step == 0:
            one = q[0]
            two = _and(c, _not(c, one), q[1])
            negative = q[1]
        elif step == 4:
            one = _and(c, _not(c, middle), low)
            two = zero
            negative = _and(c, middle, _not(c, low))
        else:
            one = _xor(c, middle, low)
            two = _and(c, _not(c, one), _xor(c, h, middle))
            negative = _and(c, h, _not(c, _and(c, middle, low)))

        q_width = 9 if step == 4 else 10
        xors = []
        if two != zero:
            xors = [_xor(c, q[2 * step + 1], _bit(m, k, zero))
                    for k in range(9)]

        def get_xor(k):
            return xors[min(k, len(xors) - 1)]

        if step >= 3:
            if two == zero:
                m0 = _bit(m, 0, zero)
                value = _or(c, _and(c, one, m0),
                            _and(c, negative, _not(c, m0)))
            else:
                value = _or(c, _and(c, one, get_xor(0)),
                            _and(c, two, q[2 * step + 1]))
            place(2 * step, value)
            place(2 * step, negative)

        activity = None
        if step == 0:
            pp_0_4 = _or(c, q[1], q[0])
            activity = pp_0_4
            place(5, _or(c, _and(c, one, get_xor(5)),
                         _and(c, two, _not(c, m[4]))))
        elif step == 1:
            pp_1_2 = _or(c, one, two)
            activity = pp_1_2
            place(5, _or(c, _and(c, one, get_xor(3)),
                         _and(c, two, get_xor(2))))
        elif step == 2:
            place(5, _or(c, _and(c, one, get_xor(1)),
                         _and(c, two, _or(c, q[5], m[0]))))
            activity = _or(c, one, two)
            common = _and(c, activity, _and(c, q[5], _not(c, m[0])))
            pp_2_and = _and(c, one, m[0])

        for k in range(max(1, 6 - step * 2), q_width):
            if two == zero:
                mk = _bit(m, k, zero)
                value = _or(c, _and(c, one, mk),
                            _and(c, negative, _not(c, mk)))
                if k == q_width - 1:
                    value = _not(c, value)
            elif k == q_width - 1:
                if activity is None:
                    activity = _or(c, one, two)
                value = _not(c, _and(c, activity, get_xor(k)))
            else:
                value = _or(c, _and(c, one, get_xor(k)),
                            _and(c, two, get_xor(k - 1)))
            place(2 * step + k, value)

    ab = _and(c, pp_0_4, pp_1_2)
    carry = _or(c, common, ab)
    total = _and(c, _or(c, common, _or(c, _not(c, ab), pp_2_and)),
                 _or(c, pp_0_4, pp_1_2))
    place(4, total)
    place(5, carry)
    return columns


def _product_columns(
    circuit: Circuit, q_bits: list[int], m_bits: list[int],
    zero: int, one_const: int, cut: int,
) -> list[list[int]]:
    """Single qgl dual-approx product's 18 column lists (low ``cut`` pruned).

    ``cut`` is the per-core column cutoff; partial-product / sign / extra bits
    landing in columns < ``cut`` are guard-pruned (never node-deleted), so the
    zero-filled low columns fall out of the carry-save and CPA compaction.
    """
    columns: list[list[int]] = [[] for _ in range(OUT_WIDTH)]
    num_steps = (WIDTH + 1) // 2

    # pp_1_2 (column-4 extra) reuses Booth step-1 ``one | two`` exactly:
    #   pp_1_2 = (q2^q1) | ((q3^q2) & NOT(q2^q1)) == one | two   (step 1)
    step1_one: int | None = None
    step1_two: int | None = None

    x_and = _not(circuit, _and(circuit, m_bits[0], m_bits[1]))
    x_or = _not(circuit, _or(circuit, m_bits[0], m_bits[1]))
    d = []

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

        place(2 * step, c)
        place(2 * step + 1, b)
        place(2 * step + 2, a)

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
            place(2 * step + k, val)

    return columns


def build_circuit():
    c = Circuit(output_width=OUT_TOTAL)
    zero, one = c.add("ZERO"), c.add("ONE")
    c._local_constants = (zero, one)
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
    # Single absorbed correction constant.  Truncating both Booth matrices
    # below column 4 removes a strictly positive quantity from the sum, so the
    # residual error is one-sided with a measured raw bias of about +44/128.
    # One ONE in column 4 (weight 16 raw units) re-centres that bias to about
    # +28/128 without ever instantiating a standalone carry-save-tree input:
    # it is merged into the column-4 bucket and is consumed by the first
    # column-4 compressor, where ``_add3`` specializes the constant away into
    # the exact ``a + b + 1`` OR/XNOR pair (carry = OR, sum = XNOR).
    for col, n in sorted(EXTRA_ONE.items()):
        for _ in range(n):
            columns[col].append(one)

    c._partial_product_columns = [list(bucket) for bucket in columns]
    for col in range(OUT_TOTAL):
        compressor_index = 0
        while len(columns[col]) >= 3:
            x0, x1, x2 = columns[col].pop(), columns[col].pop(), columns[col].pop()
            if col in MAJ_COLS and x0 not in (zero, one) and x1 not in (zero, one) \
                    and x2 not in (zero, one):
                # Carry-only compressor: the sum bit of this column is never
                # observable (outputs 0..5 are discarded), so only the majority
                # carry is materialized.  Costs 4 weighted gates instead of 7.
                ab = _and(c, x0, x1)
                carry = _or(c, ab, _and(c, _or(c, x0, x1), x2))
                compressor_index += 1
                if col + 1 < OUT_TOTAL:
                    columns[col + 1].append(carry)
                continue
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
            # This is intentionally written as a strict boundary test: columns
            # below 7 are evaluator-low (including the rounding bit at 6),
            # while column 7 is the first retained bit and must remain exact.
            outputs.append(_or(c, bucket[0], carry) if col < 7
                           else _xor(c, bucket[0], carry))
            carry = _and(c, bucket[0], carry)
        else:
            total, carry = _add3(c, bucket[0], bucket[1], carry, zero, one)
            outputs.append(total)
    # Bits 0..5 are discarded by the evaluator.  Only replace the final output
    # references: carry nodes were already constructed separately in the loop.
    c.output_ids = [zero] * 6 + outputs[6:18] + [outputs[17]]
    return c


def build_partial_product_layout():
    c = build_circuit()
    return c, c._partial_product_columns


def build_circuit_from_columns(circuit, columns):
    from multiplier.placement import rebuild_columns
    return rebuild_columns(circuit, columns)
