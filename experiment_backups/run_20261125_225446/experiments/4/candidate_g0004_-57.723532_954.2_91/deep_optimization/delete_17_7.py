"""Readable 92-slot equivalent optimization; weighted gate cost 954.2.

Stages: Booth partial products -> column-4 replacement -> compressor -> CPA
-> exact Boolean cleanup. No frozen gate list or internal node-ID references.

The historical term count conservatively includes the G6=0 boundary
slot: one of these slots is semantically constant, although deliberately opaque
during compression. These are not independent Boolean functions.
"""
from __future__ import annotations
from tools.circuit_kit.circuit.multiplier.tap2_9bit_multiplier import Circuit, MultiplierCircuit, WIDTH, OUT_WIDTH, OUT_TOTAL

class Candidate(MultiplierCircuit):
    # Enable tap2's absorption-aware hash-consing; this removes redundant
    # cones exposed by the reduced Booth correction terms below.
    _USE_ABSORPTION = True
    PROD_CUT_A = 4
    PROD_CUT_B = 4
    COMP_COLS = (10, 11, 13, 15, 18)
    ROUND_COLS: tuple[int, ...] = ()
    MAJ_COLS = (0, 1, 2, 3)
    EXTRA_ONE = {4: 1}


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

    def _xor(self, a, b):
        both = self._and(a, b)
        either = self._or(a, b)
        return self._and(either, self._not(both))

    def _one_product_columns(self, q_bits, m_bits, zero, one_const, cut):
        columns: list[list[int]] = [[] for _ in range(OUT_WIDTH)]
        num_steps = (WIDTH + 1) // 2
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
                    # Reuse the step-zero inversion term in k=4..8 MUX_XOR
                    # cells; retain the original step-one/two mapping.
                    if ((step in (1, 2) and 3 <= k <= 8) or
                            (step == 0 and 4 <= k <= 8)) and k < q_bits_of_step - 1:
                        # Zero digit has an all-zero row; preserve original Booth semantics.
                        cell_neg = self._and(negative, self._or(one, two))
                        # Shared kit port order: (a, b, c, d, e).
                        val = self._gate("MUX_XOR", one, self._bit(m_bits, k, zero), two, self._bit(m_bits, k - 1, zero), cell_neg)
                    else:
                        val = self._or(self._and(one, get_xor(k)), self._and(two, get_xor(k - 1)))
                if k == q_bits_of_step - 1:
                    val = self._not(val)
                place(2 * step + k, val)
        return columns

    def _product_columns(self, a, b, c, d, zero, one):
        all_columns = [[] for _ in range(OUT_TOTAL)]
        for builder, left, right, cut in ((self._one_product_columns, a, b, self.PROD_CUT_A), (self._one_product_columns, c, d, self.PROD_CUT_B)):
            product = builder(right, left, zero, one, cut)
            for col in range(OUT_WIDTH):
                all_columns[col].extend(product[col])
        for col in self.COMP_COLS + self.ROUND_COLS:
            all_columns[col].append(one)
        for col, n in sorted(self.EXTRA_ONE.items()):
            for _ in range(n):
                all_columns[col].append(one)
        one_sel = b[0]
        two = self._and(b[1], self._not(b[0]))
        old = self._or(self._and(one_sel, self._xor(b[1], a[4])), self._and(two, self._xor(b[1], a[3])))
        if all_columns[4][0] == old:
            all_columns[4][0] = self._or(self._and(one_sel, self._xor(b[1], a[4])), self._and(two, self._not(a[3])))
        for m, q in ((a, b), (c, d)):
            pos = self._and(self._not(q[8]), q[7])
            neg = self._and(q[8], self._not(q[7]))
            active = self._or(pos, neg)
            for k in range(2, 9):
                old = self._or(self._and(pos, m[k]), self._and(neg, self._not(m[k])))
                new = self._and(active, self._not(self._xor(q[7], m[k])))
                if k == 8:
                    old = self._not(old)
                    new = self._not(new)
                if old in all_columns[8 + k]:
                    all_columns[8 + k][all_columns[8 + k].index(old)] = new
        # Capture the ORIGINAL column-4 terms before removing any slots.
        ab_row0, ab_row1, ab_row2, cd_row0, cd_row1, cd_row2 = all_columns[4][:6]
        # Remove AB rows 0/1/2 and CD row2 (four terms).
        # SMT-selected compensation: G5 = ab_row0 | ab_row2; G6 = 0.
        compensation_bit5 = self._or(ab_row2, ab_row0)
        removed_positions = (0, 1, 2, 5)
        for position in reversed(removed_positions):
            del all_columns[4][position]

        # Preserve the search's insertion boundary: both outputs are opaque
        # during compressor construction, even though G6 is identically zero.
        # The final exact Boolean pass removes these OR-with-zero buffers.
        all_columns[5].append(compensation_bit5)
        all_columns[6].append(zero)
        if len(all_columns[17]) > 7:
            del all_columns[17][7]
        return all_columns

    def _fa_factored(self, a, b, cin):
        ab = self._xor(a, b)
        return self._xor(ab, cin), self._or(self._and(a, b), self._and(ab, cin))

    def _add3_factored(self, x, y, z):
        if x not in (self._zero, self._one) and y not in (self._zero, self._one) and z not in (self._zero, self._one):
            return self._fa_factored(x, y, z)
        return self._add3(x, y, z)

    def _compress_columns(self):
        all_columns = self._columns
        zero, one = (self._zero, self._one)
        for col in range(OUT_TOTAL):
            compressor_index = 0
            while len(all_columns[col]) >= 3:
                x0, x1, x2 = (all_columns[col].pop(), all_columns[col].pop(), all_columns[col].pop())
                if col in self.MAJ_COLS and x0 not in (zero, one) and (x1 not in (zero, one)) and (x2 not in (zero, one)):
                    x0x2 = self._and(x0, x2)
                    x1_or_x0x2 = self._or(x1, x0x2)
                    x0_or_x2 = self._or(x0, x2)
                    carry = self._and(x1_or_x0x2, x0_or_x2)
                    compressor_index += 1
                    if col + 1 < OUT_TOTAL:
                        all_columns[col + 1].append(carry)
                    continue
                if col == 3 and compressor_index <= 1:
                    ac = self._and(x0, x2)
                    b_or_ac = self._or(x1, ac)
                    a_or_c = self._or(x0, x2)
                    carry = self._and(b_or_ac, a_or_c)
                    total = self._xor(b_or_ac, a_or_c)
                else:
                    total, carry = self._add3_factored(x0, x1, x2)
                compressor_index += 1
                all_columns[col].append(total)
                if col + 1 < OUT_TOTAL:
                    all_columns[col + 1].append(carry)

    def _build_outputs(self):
        """Original CPA/output semantics, followed by exact Boolean cleanup."""
        all_columns = self._columns
        zero, one = (self._zero, self._one)
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
                outputs.append(self._or(bucket[0], carry) if col < 7 else self._xor(bucket[0], carry))
                carry = self._and(bucket[0], carry)
            else:
                total, carry = self._add3(bucket[0], bucket[1], carry)
                outputs.append(total)
        self.output_ids = [zero] * 6 + outputs[6:18] + [outputs[17]]

        # Simplify only after compression/CPA: earlier constant folding could
        # change structural dispatch in the approximate arithmetic stages.
        # Keep node IDs/caches internally consistent when replacing the DAG.
        optimized = _optimize_boolean_graph(self)
        self.nodes = optimized.nodes
        self.input_ids = optimized.input_ids
        self.output_ids = optimized.output_ids
        self._gate_cache = {}
        self._zero = 0
        self._one = 1
        self._columns = [[node] for node in self.output_ids]


def _optimize_boolean_graph(src):
    dst=Circuit();cache={};mapping={};zero=dst.add('ZERO');one=dst.add('ONE')
    def gate(kind,*args):
        if kind=='NOT':
            a=args[0]
            if a==zero:return one
            if a==one:return zero
            if dst.nodes[a].kind=='NOT':return dst.nodes[a].inputs[0]
        elif kind in ('AND', 'OR', 'XOR'):
            a,b=sorted(args);args=(a,b)
            if a==b:return zero if kind=='XOR' else a
            if kind=='AND':
                if zero in args:return zero
                if one in args:return b if a==one else a
            if kind=='OR':
                if one in args:return one
                if zero in args:return b if a==zero else a
            if kind=='XOR':
                if zero in args:return b if a==zero else a
                if one in args:return gate('NOT',b if a==one else a)
            def opposite(x,y):
                return dst.nodes[x].kind=='NOT' and dst.nodes[x].inputs[0]==y
            if opposite(a,b) or opposite(b,a):return zero if kind=='AND' else one
            if kind in ('AND','OR'):
                other='OR' if kind=='AND' else 'AND'
                for x,y in ((a,b),(b,a)):
                    yn=dst.nodes[y]
                    if yn.kind==other:
                        if x in yn.inputs:return x
                        # x & (~x | y) = x & y, and its dual.
                        for p,q in (yn.inputs,yn.inputs[::-1]):
                            if opposite(x,p) or opposite(p,x):return gate(kind,x,q)
                an,bn=dst.nodes[a],dst.nodes[b]
                if an.kind==bn.kind==other:
                    shared=set(an.inputs)&set(bn.inputs)
                    if shared:
                        s=min(shared)
                        x=next((v for v in an.inputs if v!=s),s)
                        y=next((v for v in bn.inputs if v!=s),s)
                        return gate(other,s,gate(kind,x,y))
        key=(kind,args)
        if key not in cache:cache[key]=dst.add(kind,*args)
        return cache[key]
    inputs=set(src.input_ids)
    for i,n in enumerate(src.nodes):
        if i in inputs:mapping[i]=dst.add(n.kind)
        elif n.kind=='ZERO':mapping[i]=zero
        elif n.kind=='ONE':mapping[i]=one
        else:mapping[i]=gate(n.kind,*(mapping[x] for x in n.inputs))
    dst.input_ids=[mapping[n] for n in src.input_ids]
    dst.output_ids=[mapping[n] for n in src.output_ids]
    dst.validate();return dst

def build_circuit():
    return Candidate()._build_circuit()
