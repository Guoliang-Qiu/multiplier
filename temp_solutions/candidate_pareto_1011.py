"""Fixed higher-accuracy candidate from the 1037/-58.18 seed."""
from __future__ import annotations

from multiplier.initial_solutions.candidate_g0001_0000 import Candidate as Seed


class Candidate(Seed):
    _EDIT_BY_CALL = {0: "pair_or", 1: "or", 2: "pair", 3: "approx", 6: "zero"}

    def __init__(self):
        super().__init__()
        self._add3_calls = 0

    def _add3(self, a, b, c):
        index = self._add3_calls
        self._add3_calls += 1
        mode = self._EDIT_BY_CALL.get(index)
        if mode is None:
            return super()._add3(a, b, c)
        zero = self._zero
        pair = self._or(a, c)
        both = self._and(a, c)
        carry = self._and(pair, self._or(b, both))
        if mode == "pair_or":
            return pair, both
        if mode == "or":
            return self._or(pair, b), carry
        if mode == "pair":
            return self._xor(a, c), both
        if mode == "approx":
            q = self._or(b, both)
            return self._xor(pair, q), carry
        if mode == "zero":
            return zero, carry
        raise ValueError(mode)


def build_circuit():
    return Candidate()._build_circuit()
