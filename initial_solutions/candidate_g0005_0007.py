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
* Replace every remaining XOR with its exact weighted-cost-equivalent
  ``(a|b)&~(a&b)`` form.  Global hash-consing can share the OR/AND predicates
  with neighboring Booth and adder logic, reducing whole-DAG weighted cost
  without changing any local truth table.
* Jointly specialize every constant-input two-signal compressor.  For ZERO,
  carry ``a&b`` is shared by the exact sum ``(a|b)&~carry``; for ONE,
  carry ``a|b`` is shared by the exact sum ``(a&b)|~carry``.  Each fully
  specified two-output cell uses three unit-cost gates instead of a cost-3 XOR
  plus its carry gate.
* Prune only the private final-sum cones for raw bits 0 through 5 by driving
  those discarded outputs with ZERO.  Their independently constructed ripple
  carries remain reachable, preserving bit 6 and all retained output bits.
* Mutate the first two specifically indexed column-3 compressors as joint
  two-output cones.  Their carries remain exact majority, while their sums
  change only for the fully specified local state ``111`` (parity 1 -> 0).
  Each five-node shared AND/OR/XOR realization costs seven under repository
  weights, one less than its exact eight-cost cone; these sites are below the
  previously exhausted column-4 and column-5 approximation sites.
"""
from __future__ import annotations

from multiplier.circuit import Circuit

WIDTH = 9
OUT_WIDTH = 18
OUT_TOTAL = 19
PROD_CUT_A = 0
PROD_CUT_B = 0
COMP_COLS = (10, 11, 13, 15, 18)
ROUND_COLS: tuple[int, ...] = ()


def _gate(c: Circuit, kind: str, *inputs: int) -> int:
    """Hash-cons identical local gates while constructing the static DAG."""
    cache = getattr(c, "_local_gate_cache", None)
    if cache is None:
        cache = {}
        c._local_gate_cache = cache
    if kind in ("AND", "OR", "XOR") and inputs[1] < inputs[0]:
        inputs = (inputs[1], inputs[0])
    key = (kind, inputs)
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
    """Exact joint sum/carry realization optimized for weighted gate cost.

    The conventional realization costs 9 (two XORs plus three cheap gates).
    Exact synthesis over AND/OR/NOT found this 8-cost shared realization.
    """
    ac = _and(c, a, cin)
    abc = _and(c, b, ac)
    a_or_c = _or(c, a, cin)
    b_a_or_c = _and(c, b, a_or_c)
    carry = _or(c, ac, b_a_or_c)
    total = _and(c, _or(c, b, a_or_c), _or(c, abc, _not(c, carry)))
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
    a = [c.add("IN_A") for _ in range(WIDTH)]
    b = [c.add("IN_B") for _ in range(WIDTH)]
    x = [c.add("IN_C") for _ in range(WIDTH)]
    d = [c.add("IN_D") for _ in range(WIDTH)]
    c.input_ids = a + b + x + d
    columns = [[] for _ in range(OUT_TOTAL)]
    for left, right, cut in ((a, b, PROD_CUT_A), (x, d, PROD_CUT_B)):
        product = _product_columns(c, right, left, zero, one, cut)
        for col in range(OUT_WIDTH): columns[col].extend(product[col])
    for col in COMP_COLS + ROUND_COLS: columns[col].append(one)

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
            # Local low-significance half-adder resynthesis: preserve the exact
            # carry into column 6, but use OR for the column-5 sum.  Relative
            # to XOR this changes only input 11 (sum 0->1), a +32 raw-unit
            # perturbation, while replacing a weighted-cost-3 XOR by one OR.
            outputs.append(_or(c, bucket[0], carry) if col <= 6
                           else _xor(c, bucket[0], carry))
            carry = _and(c, bucket[0], carry)
        else:
            total, carry = _add3(c, bucket[0], bucket[1], carry, zero, one)
            outputs.append(total)
    # Bits 0..5 are discarded by the evaluator.  Only replace the final output
    # references: carry nodes were already constructed separately in the loop.
    c.output_ids = [zero] * 6 + outputs[6:18] + [outputs[17]]
    return c
