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

from multiplier.circuit import Circuit

WIDTH = 9
OUT_WIDTH = 18
OUT_TOTAL = 19
PROD_CUT_A = 4
PROD_CUT_B = 4
COMP_COLS = (10, 11, 13, 15)
ROUND_COLS: tuple[int, ...] = ()


def _gate(c: Circuit, kind: str, *inputs: int) -> int:
    """Constant-fold and share structurally identical Boolean gates."""
    zero, one = c._local_constants
    if kind == "NOT":
        source = inputs[0]
        if source == zero: return one
        if source == one: return zero
        node = c.nodes[source]
        if node.kind == "NOT": return node.inputs[0]
    else:
        a, b = inputs
        if a == b: return zero if kind == "XOR" else a
        if kind == "AND":
            if zero in inputs: return zero
            if one in inputs: return b if a == one else a
        elif kind == "OR":
            if one in inputs: return one
            if zero in inputs: return b if a == zero else a
        elif kind == "XOR":
            if zero in inputs: return b if a == zero else a
            if one in inputs: return _not(c, b if a == one else a)
        # Boolean absorption removes redundant cones without changing any
        # truth table: x|(x&y)=x and x&(x|y)=x.  This is especially useful
        # in the factored Booth and compressor boundaries.
        if kind == "OR":
            for operand, other in ((a, b), (b, a)):
                on = c.nodes[other]
                if on.kind == "AND" and operand in on.inputs:
                    return operand
        elif kind == "AND":
            for operand, other in ((a, b), (b, a)):
                on = c.nodes[other]
                if on.kind == "OR" and operand in on.inputs:
                    return operand
        na, nb = c.nodes[a], c.nodes[b]
        if ((na.kind == "NOT" and na.inputs[0] == b) or
                (nb.kind == "NOT" and nb.inputs[0] == a)):
            return zero if kind == "AND" else one
        if inputs[1] < inputs[0]: inputs = (inputs[1], inputs[0])
    key = (kind, inputs)
    node = c._local_gate_cache.get(key)
    if node is None:
        node = c.add(kind, *inputs)
        c._local_gate_cache[key] = node
    return node


def _and(c, a, b): return _gate(c, "AND", a, b)
def _or(c, a, b): return _gate(c, "OR", a, b)
def _xor(c, a, b):
    """Exact XOR resynthesis that can share cached AND/OR predicates."""
    both = _and(c, a, b)
    either = _or(c, a, b)
    return _and(c, either, _not(c, both))
def _not(c, a): return _gate(c, "NOT", a)


def _fa(c, a, b, cin):
    """Exact joint parity/majority network (seven weighted unit gates).

    Derived by exact multi-output synthesis over {AND, OR, NOT} for the joint
    (sum, carry) table of a full adder.  Because the external model prices NOT at zero, the weighted cost is the AND/OR count only.
    """
    ac = _and(c, a, cin)
    aoc = _or(c, a, cin)
    xn = _or(c, ac, _not(c, aoc))
    b_or_xn = _or(c, b, xn)
    total = _or(c, _not(c, b_or_xn), _and(c, b, xn))
    carry = _and(c, aoc, b_or_xn)
    return total, carry


def _ha(c, a, b):
    """Exact joint half adder: carry=a&b; sum=(a|b)&~carry."""
    carry = _and(c, a, b)
    total = _and(c, _or(c, a, b), _not(c, carry))
    return total, carry


def _add3(c, x, y, z, zero, one):
    consts = [n for n in (x, y, z) if n in (zero, one)]
    reals = [n for n in (x, y, z) if n not in (zero, one)]
    if not consts: return _fa(c, x, y, z)
    if len(consts) == 1:
        a, b = reals
        if one in consts:
            carry = _or(c, a, b)
            return _or(c, _and(c, a, b), _not(c, carry)), carry
        return _ha(c, a, b)
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


def _product_columns(c, q, m, zero, one_const, cut):
    columns = [[] for _ in range(OUT_WIDTH)]
    pp_0_4 = pp_1_2 = common = pp_2_and = None

    def place(col, node):
        if col >= cut: columns[col].append(node)

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
            # Exact joint Booth recoder, seven weighted units.  Exact
            # multi-output synthesis over {AND, OR, NOT} for the joint
            # (one, two, negative) table returns 5 AND + 2 OR + 2 NOT, and the
            # shared ``ml_or``/``~ml_and`` nodes replace the two XOR cones the
            # parent built through ``_xor``.  Bit-identical on all 8 states:
            #   one = (middle|low) & ~(middle&low)  = middle ^ low
            #   two = ~(h&(middle|low)) & (h|(middle&low))
            #                                       = ~one & (h ^ middle)
            #   negative = h & ~(middle&low)
            ml_or = _or(c, middle, low)
            ml_and = _and(c, middle, low)
            n_ml_and = _not(c, ml_and)
            one = _and(c, ml_or, n_ml_and)
            two = _and(c, _not(c, _and(c, h, ml_or)), _or(c, h, ml_and))
            negative = _and(c, h, n_ml_and)

        q_width = 9 if step == 4 else 10
        xors = []
        if two != zero:
            xors = [_xor(c, q[2 * step + 1], _bit(m, k, zero)) for k in range(9)]

        def get_xor(k): return xors[min(k, len(xors) - 1)]

        if step >= 3:
            if two == zero:
                m0 = _bit(m, 0, zero)
                value = _or(c, _and(c, one, m0), _and(c, negative, _not(c, m0)))
            else:
                value = _or(c, _and(c, one, get_xor(0)), _and(c, two, q[2 * step + 1]))
            place(2 * step, value)
            place(2 * step, negative)

        # Row-activity signal one|two, reused by the factored top mux below.
        # Steps 0-2 already build an equivalent node; step 3 builds one lazily.
        activity = None
        if step == 0:
            pp_0_4 = _or(c, q[1], q[0])
            activity = pp_0_4  # q0 | (~q0 & q1) == q0 | q1 == one | two
            place(5, _or(c, _and(c, one, get_xor(5)), _and(c, two, _not(c, m[4]))))
        elif step == 1:
            pp_1_2 = _or(c, one, two)
            activity = pp_1_2
            place(5, _or(c, _and(c, one, get_xor(3)), _and(c, two, get_xor(2))))
        elif step == 2:
            place(5, _or(c, _and(c, one, get_xor(1)),
                         _and(c, two, _or(c, q[5], m[0]))))
            activity = _or(c, one, two)
            common = _and(c, activity, _and(c, q[5], _not(c, m[0])))
            pp_2_and = _and(c, one, m[0])

        for k in range(max(1, 6 - step * 2), q_width):
            if two == zero:
                mk = _bit(m, k, zero)
                value = _or(c, _and(c, one, mk), _and(c, negative, _not(c, mk)))
                if k == q_width - 1: value = _not(c, value)
            elif k == q_width - 1:
                # Top mux: get_xor clamps both terms to xors[8], i.e.
                # (one&x8) | (two&x8) == (one|two) & x8; reuse the row
                # activity signal instead of rebuilding both ANDs.
                if activity is None: activity = _or(c, one, two)
                value = _not(c, _and(c, activity, get_xor(k)))
            else:
                value = _or(c, _and(c, one, get_xor(k)), _and(c, two, get_xor(k - 1)))
            place(2 * step + k, value)

    ab = _and(c, pp_0_4, pp_1_2)
    carry = _or(c, common, ab)
    total = _and(c, _or(c, common, _or(c, _not(c, ab), pp_2_and)),
                 _or(c, pp_0_4, pp_1_2))
    place(4, total)
    place(5, carry)
    return columns


def build_circuit():
    c = Circuit(output_width=OUT_TOTAL)
    zero, one = c.add("ZERO"), c.add("ONE")
    c._local_constants = (zero, one)
    c._local_gate_cache = {}
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
    # Local exact cone optimization: outputs 0--5 are discarded, so preserve
    # only their carry path below while leaving all parent partial products and
    # higher-column behavior unchanged.

    c._partial_product_columns = [list(bucket) for bucket in columns]
    for col in range(OUT_TOTAL):
        while len(columns[col]) >= 3:
            total, carry = _add3(c, columns[col].pop(), columns[col].pop(), columns[col].pop(), zero, one)
            columns[col].append(total)
            if col + 1 < OUT_TOTAL: columns[col + 1].append(carry)

    carry = None
    outputs = []
    for col, bucket in enumerate(columns):
        bucket = bucket or [zero]
        if col < 6:
            # These six sum bits are discarded by Q4.7 quantization.  Compute
            # only the exact ripple carry, including constant-aware cases.
            outputs.append(zero)
            if carry is None:
                if len(bucket) > 1:
                    carry = _and(c, bucket[0], bucket[1])
            elif len(bucket) == 1 and bucket[0] == zero:
                carry = zero
            elif len(bucket) == 1 and bucket[0] == one:
                pass  # carry-out of 1 + carry is carry
            elif len(bucket) == 1:
                carry = _and(c, bucket[0], carry)
            else:
                a0, a1 = bucket[0], bucket[1]
                # Exact majority without either parity XOR used by _fa.
                carry = _or(c, _and(c, a0, a1),
                            _and(c, carry, _or(c, a0, a1)))
            continue
        if carry is None:
            if len(bucket) == 1:
                outputs.append(bucket[0])
            else:
                total, carry = _ha(c, bucket[0], bucket[1])
                outputs.append(total)
        elif len(bucket) == 1 and bucket[0] == zero:
            outputs.append(carry); carry = zero
        elif len(bucket) == 1 and bucket[0] == one:
            outputs.append(_not(c, carry))
        elif len(bucket) == 1:
            total, carry = _ha(c, bucket[0], carry)
            outputs.append(total)
        else:
            total, carry = _add3(c, bucket[0], bucket[1], carry, zero, one)
            outputs.append(total)
    c.output_ids = outputs[:18] + [outputs[17]]
    return c


def build_partial_product_layout():
    c = build_circuit()
    return c, c._partial_product_columns


def build_circuit_from_columns(circuit, columns):
    from multiplier.placement import rebuild_columns
    return rebuild_columns(circuit, columns)
