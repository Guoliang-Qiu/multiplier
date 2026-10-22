"""Local gate/error probes based on the higher-EVM g0001_0002 seed."""
from __future__ import annotations

import os
if os.environ.get("HIGH_EVM_PARENT", "0002") == "0000":
    from initial_solutions.candidate_g0001_0000 import Candidate as Parent
elif os.environ.get("HIGH_EVM_PARENT", "0002") == "999":
    from initial_solutions.candidate_g0000_0001 import Candidate as Parent
else:
    from initial_solutions.candidate_g0001_0002 import Candidate as Parent
from multiplier.circuit import OUT_TOTAL


class Candidate(Parent):
    MAJ_COLS = tuple(int(x) for x in os.environ.get("MAJ_COLS", "").split(",") if x)
    CPA_OR_UNTIL = int(os.environ.get("CPA_OR_UNTIL", "-1"))
    COMPRESSOR_MODE = os.environ.get("COMPRESSOR_MODE", "exact")
    CPA_LOW_CARRY = os.environ.get("CPA_LOW_CARRY", "exact")
    MAJ_LIMIT = int(os.environ.get("MAJ_LIMIT", "999"))
    POP_MODE = os.environ.get("POP_MODE", "native")

    def _build_circuit(self, layout_only=False, columns=None):
        a, b, c, d, zero, one = self.setup()
        all_columns = [[] for _ in range(OUT_TOTAL)]
        for left, right, cut in ((a, b, self.PROD_CUT_A), (c, d, self.PROD_CUT_B)):
            product = self._product_columns(right, left, zero, one, cut)
            for col in range(18):
                all_columns[col].extend(product[col])
        for col in self.COMP_COLS + self.ROUND_COLS:
            all_columns[col].append(one)
        if layout_only:
            return self, [list(bucket) for bucket in all_columns]
        if columns is not None:
            all_columns = [list(bucket) for bucket in columns]
        for col in range(OUT_TOTAL):
            if self.POP_MODE == "sorted":
                all_columns[col].sort()
            elif self.POP_MODE == "reverse_sorted":
                all_columns[col].sort(reverse=True)
            elif self.POP_MODE == "alternate":
                all_columns[col] = all_columns[col][::2] + all_columns[col][1::2]
            compressor_index = 0
            while len(all_columns[col]) >= 3:
                x0, x1, x2 = all_columns[col].pop(), all_columns[col].pop(), all_columns[col].pop()
                if self.COMPRESSOR_MODE == "majority" and col in self.MAJ_COLS and compressor_index < self.MAJ_LIMIT and all(x not in (zero, one) for x in (x0, x1, x2)):
                    carry = self._and(self._or(x1, self._and(x0, x2)), self._or(x0, x2))
                    if col + 1 < OUT_TOTAL:
                        all_columns[col + 1].append(carry)
                    compressor_index += 1
                    continue
                total, carry = self._add3(x0, x1, x2)
                all_columns[col].append(total)
                if col + 1 < OUT_TOTAL:
                    all_columns[col + 1].append(carry)
                compressor_index += 1
        carry = None
        outputs = []
        for col, bucket in enumerate(all_columns):
            bucket = bucket or [zero]
            if col < 6:
                outputs.append(zero)
                if len(bucket) > 1:
                    lo, hi = bucket[0], bucket[1]
                    pair = self._and(lo, hi)
                    if self.CPA_LOW_CARRY == "or":
                        pair = self._or(lo, hi)
                    elif self.CPA_LOW_CARRY == "lo":
                        pair = lo
                    carry = pair if carry is None else self._or(pair, self._and(carry, self._or(lo, hi)))
                elif carry is not None:
                    carry = self._and(bucket[0], carry)
                continue
            if carry is None:
                outputs.append(bucket[0] if len(bucket) == 1 else self._xor(bucket[0], bucket[1]))
                if len(bucket) > 1: carry = self._and(bucket[0], bucket[1])
            elif len(bucket) == 1 and bucket[0] == zero:
                outputs.append(carry); carry = zero
            elif len(bucket) == 1 and bucket[0] == one:
                outputs.append(self._not(carry))
            elif len(bucket) == 1:
                total = self._or(bucket[0], carry) if col <= self.CPA_OR_UNTIL else self._xor(bucket[0], carry)
                outputs.append(total); carry = self._and(bucket[0], carry)
            else:
                total, carry = self._add3(bucket[0], bucket[1], carry); outputs.append(total)
        self.output_ids = outputs[:18] + [outputs[17]]
        return self


def build_circuit():
    return Candidate()._build_circuit()
