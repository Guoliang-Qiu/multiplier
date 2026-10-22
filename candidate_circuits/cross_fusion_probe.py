"""Probe cross-product low-column fusion in the four-input compressor matrix.

This intentionally makes the approximation *before* the common compressor
tree: one entry from ``a*b`` and one from ``c*d`` in the same raw column are
replaced by their OR, with optional constant compensation.  It tests whether
the two product cones have useful joint redundancy that independent cut/round
search cannot see.
"""
from __future__ import annotations
import os

from multiplier.circuit import OUT_TOTAL
from initial_solutions.candidate_g0000_0002 import Candidate as Parent


class Candidate(Parent):
    COMP_COLS = tuple(int(x) for x in os.environ.get("COMP_COLS", "10,11,13,15").split(",") if x)
    ROUND_COLS = tuple(int(x) for x in os.environ.get("ROUND_COLS", "5").split(",") if x)
    FUSE_COL = int(os.environ.get("FUSE_COL", "4"))
    FUSE_INDEX = int(os.environ.get("FUSE_INDEX", "0"))
    FUSE_COUNT = int(os.environ.get("FUSE_COUNT", "1"))
    FUSE_OP = os.environ.get("FUSE_OP", "or")
    FUSE_CARRY = os.environ.get("FUSE_CARRY", "0") == "1"
    OVERLAP_MODE = os.environ.get("OVERLAP_MODE", "none")
    OVERLAP_TARGET = int(os.environ.get("OVERLAP_TARGET", "1"))
    GROUP4 = os.environ.get("GROUP4", "0") == "1"
    FUSE_CARRY_MODE = os.environ.get("FUSE_CARRY_MODE", "and")
    DISABLE_FUSION = os.environ.get("DISABLE_FUSION", "0") == "1"
    MAJ_SUM = os.environ.get("MAJ_SUM", "zero")
    COMP_EXTRA = tuple(int(x) for x in os.environ.get("COMP_EXTRA", "").split(",") if x)
    MAJ_COLS = tuple(int(x) for x in os.environ.get("MAJ_COLS", "").split(",") if x)

    def _build_circuit(self, layout_only=False, columns=None):
        a, b, x, d, zero, one = self.setup()
        # Parent's convention is (q_bits, m_bits): q is the multiplier bus.
        # Keep the same a,b,c,d role ordering as Parent._build_circuit.
        left = self._product_columns(b, a, zero, one, self.PROD_CUT_A)
        right = self._product_columns(d, x, zero, one, self.PROD_CUT_B)
        all_columns = [[] for _ in range(OUT_TOTAL)]
        for col in range(18):
            if col == self.FUSE_COL and not self.DISABLE_FUSION:
                # Preserve all but one cross-cone pair.  Pair selection is
                # deterministic and deliberately exposed for the probe sweep.
                n = min(len(left[col]), len(right[col]))
                if n:
                    idx = min(self.FUSE_INDEX, n - 1)
                    if self.GROUP4 and idx < n:
                        # Four same-weight bits -> one approximate sum bit.
                        # This is deliberately a coarse 4:1 compressor probe.
                        group = [left[col][idx], right[col][idx]]
                        if idx + 1 < n:
                            group += [left[col][idx + 1], right[col][idx + 1]]
                        g = group[0]
                        for bit in group[1:]:
                            g = self._or(g, bit)
                        all_columns[col].append(g)
                        selected = set(range(idx, min(idx + 2, n)))
                        for i in range(n):
                            if i not in selected:
                                all_columns[col].append(left[col][i]); all_columns[col].append(right[col][i])
                        all_columns[col].extend(left[col][n:]); all_columns[col].extend(right[col][n:])
                        continue
                    selected = set(range(idx, min(idx + self.FUSE_COUNT, n)))
                    for i in range(n):
                        if i in selected:
                            continue
                        all_columns[col].append(left[col][i])
                        all_columns[col].append(right[col][i])
                    for i in sorted(selected):
                        lnode, rnode = left[col][i], right[col][i]
                        if self.FUSE_OP == "exact":
                            all_columns[col].append(self._xor(lnode, rnode))
                            if col + 1 < OUT_TOTAL:
                                all_columns[col + 1].append(self._and(lnode, rnode))
                            continue
                        if self.FUSE_OP == "and":
                            fused = self._and(lnode, rnode)
                        elif self.FUSE_OP == "xor":
                            fused = self._xor(lnode, rnode)
                        elif self.FUSE_OP == "left":
                            fused = lnode
                        elif self.FUSE_OP == "right":
                            fused = rnode
                        elif self.FUSE_OP == "or_not_right":
                            fused = self._or(lnode, self._not(rnode))
                        else:
                            fused = self._or(lnode, rnode)
                        all_columns[col].append(fused)
                        overlap = self._and(lnode, rnode)
                        if self.FUSE_CARRY and col + 1 < OUT_TOTAL:
                            if self.FUSE_CARRY_MODE == "or":
                                all_columns[col + 1].append(self._or(lnode, rnode))
                            elif self.FUSE_CARRY_MODE == "xor":
                                all_columns[col + 1].append(self._xor(lnode, rnode))
                            else:
                                all_columns[col + 1].append(overlap)
                        elif self.OVERLAP_MODE == "next" and self.OVERLAP_TARGET == 1 and col + 1 < OUT_TOTAL:
                            all_columns[col + 1].append(overlap)
                        elif self.OVERLAP_MODE == "next" and self.OVERLAP_TARGET == 2 and col + 2 < OUT_TOTAL:
                            all_columns[col + 2].append(overlap)
                        elif self.OVERLAP_MODE == "next_not_left" and col + 1 < OUT_TOTAL:
                            all_columns[col + 1].append(self._and(overlap, self._not(lnode)))
                        elif self.OVERLAP_MODE == "next_not_right" and col + 1 < OUT_TOTAL:
                            all_columns[col + 1].append(self._and(overlap, self._not(rnode)))
                    all_columns[col].extend(left[col][n:])
                    all_columns[col].extend(right[col][n:])
                else:
                    all_columns[col].extend(left[col]); all_columns[col].extend(right[col])
            else:
                all_columns[col].extend(left[col]); all_columns[col].extend(right[col])
        for col in self.COMP_COLS + self.ROUND_COLS + self.COMP_EXTRA:
            all_columns[col].append(one)
        if layout_only:
            return self, [list(bucket) for bucket in all_columns]
        if columns is not None:
            all_columns = [list(bucket) for bucket in columns]
        for col in range(OUT_TOTAL):
            while len(all_columns[col]) >= 3:
                x0, x1, x2 = all_columns[col].pop(), all_columns[col].pop(), all_columns[col].pop()
                if col in self.MAJ_COLS and x0 not in (zero, one) and x1 not in (zero, one) and x2 not in (zero, one):
                    x0x2 = self._and(x0, x2)
                    carry = self._and(self._or(x1, x0x2), self._or(x0, x2))
                    if self.MAJ_SUM == "or":
                        all_columns[col].append(self._or(x0, self._or(x1, x2)))
                    elif self.MAJ_SUM == "xor":
                        all_columns[col].append(self._xor(self._xor(x0, x1), x2))
                    elif self.MAJ_SUM == "left":
                        all_columns[col].append(x0)
                    if col + 1 < OUT_TOTAL:
                        all_columns[col + 1].append(carry)
                    continue
                total, carry = self._add3(x0, x1, x2)
                all_columns[col].append(total)
                if col + 1 < OUT_TOTAL:
                    all_columns[col + 1].append(carry)
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
                outputs.append(self._xor(bucket[0], carry)); carry = self._and(bucket[0], carry)
            else:
                total, carry = self._add3(bucket[0], bucket[1], carry)
                outputs.append(total)
        self.output_ids = [zero] * 6 + outputs[6:18] + [outputs[17]]
        return self


def build_circuit():
    return Candidate()._build_circuit()
