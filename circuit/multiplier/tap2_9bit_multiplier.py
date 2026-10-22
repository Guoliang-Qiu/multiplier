"""Shared infrastructure for multiplier circuit candidates.

Provides the multiplier-specific ``Circuit`` subclass (legacy leaf components,
packed simulation) and the ``MultiplierCircuit`` base class (gate primitives,
arithmetic helpers, setup).  Each candidate subclass implements its own
``_build_circuit`` using these primitives.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from ..components import ComponentLibrary, ComponentSpec, STANDARD_COMPONENTS
from ..model import Circuit as _GenericCircuit
from ..simulation import _simulate_packed_values

INPUT_WIDTH = 9
WIDTH = 9
OUT_WIDTH = 18
OUT_TOTAL = 19


_LEGACY_COMPONENTS = ComponentLibrary([
    *STANDARD_COMPONENTS,
    ComponentSpec("XOR", 2, gate_cost=3, truth_table=(0, 1, 1, 0)),
    *(ComponentSpec(name, 0, 0, "leaf", (0,))
      for name in ("IN_A", "IN_B", "IN_C", "IN_D")),
])


class Circuit(_GenericCircuit):
    """Multiplier circuit with legacy IN_A..IN_D leaves and packed simulation."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("components", _LEGACY_COMPONENTS)
        super().__init__(*args, **kwargs)

    def simulate_many(self, input_values, chunk_size=64):
        results = []
        for start in range(0, len(input_values), chunk_size):
            chunk = input_values[start:start + chunk_size]
            values = _simulate_packed_values(self, chunk, input_width=INPUT_WIDTH)
            results.extend(sum(((values[i] >> index) & 1) << bit
                               for bit, i in enumerate(self.output_ids))
                           for index in range(len(chunk)))
        width = len(self.output_ids)
        sign_bit, modulus = 1 << (width - 1), 1 << width
        return [raw - modulus if raw & sign_bit else raw for raw in results]


class MultiplierCircuit(Circuit, ABC):
    """Base class for multiplier circuit candidates.

    Provides gate primitives (constant-fold + hash-cons), arithmetic helpers
    (full adder, half adder, 3:2 compressor), input setup, and the shared
    partial-product column interface.  The base ``_build_circuit`` defines the
    common construction flow; subclasses implement ``_product_columns``.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._zero: int | None = None
        self._one: int | None = None
        self._gate_cache: dict = {}
        self._columns: list[list[int]] = [[] for _ in range(OUT_TOTAL)]

    def column(self, index: int, *nodes: int) -> list[int]:
        """Append partial-product nodes to a weighted column."""
        if index < 0 or index >= OUT_TOTAL:
            raise IndexError(f"column index out of range: {index}")
        self._columns[index].extend(nodes)
        return self._columns[index]

    def _build_circuit(self):
        """Build the complete circuit from the candidate's product columns."""
        self._columns = [[] for _ in range(OUT_TOTAL)]
        a, b, c, d, zero, one = self.setup()
        self._columns = self._product_columns(a, b, c, d, zero, one)

        if len(self._columns) != OUT_TOTAL:
            raise ValueError(f"expected {OUT_TOTAL} product columns")

        self._compress_columns()
        self._build_outputs()
        return self

    @abstractmethod
    def _product_columns(
        self,
        a: list[int],
        b: list[int],
        c: list[int],
        d: list[int],
        zero: int,
        one: int,
    ) -> list[list[int]]:
        """Build all pre-compression columns for ``a * b + c * d``.

        The four input buses are passed together so a candidate can share
        logic across both products.  The returned columns contain the
        complete partial-product layout, including constant compensation
        terms required by the candidate.
        """
        raise NotImplementedError

    @abstractmethod
    def _compress_columns(self):
        """Compress the partial-product columns.

        Implementations may call ``_compress_columns_reference()`` and then
        customize the result, or provide a fully custom compressor tree.
        """
        self._compress_columns_reference()

    def _compress_columns_reference(self):
        """Reference 3:2 compression implementation for candidate classes."""
        # Reduce every column to at most two bits before the final carry pass.
        for col in range(OUT_TOTAL):
            while len(self._columns[col]) >= 3:
                x = self._columns[col].pop()
                y = self._columns[col].pop()
                z = self._columns[col].pop()
                total, carry = self._add3(x, y, z)
                self._columns[col].append(total)
                if col + 1 < OUT_TOTAL:
                    self._columns[col + 1].append(carry)

    @abstractmethod
    def _build_outputs(self):
        """Build output nodes from the compressed columns.

        Implementations may call ``_build_outputs_reference()`` and then
        customize the output layout, or provide a fully custom final adder.
        """
        self._build_outputs_reference()

    def _build_outputs_reference(self):
        """Reference ripple-carry output implementation for candidates."""
        # Resolve the remaining two-row representation with a ripple carry.
        outputs = []
        carry = self._zero
        for col in range(OUT_TOTAL):
            bucket = self._columns[col]
            if len(bucket) == 0:
                total, carry = carry, self._zero
            elif len(bucket) == 1:
                total, carry = self._ha(bucket[0], carry)
            else:
                total, carry = self._add3(bucket[0], bucket[1], carry)
            outputs.append(total)
        self.output_ids = outputs

    # ------------------------------------------------------------------ setup

    def setup(self):
        """Add ZERO/ONE constants and 4 x WIDTH input leaves.

        Returns ``(a, b, c, d, zero, one)`` where each of ``a..d`` is a list
        of WIDTH node IDs.
        """
        self._zero = self.add("ZERO")
        self._one = self.add("ONE")
        a = [self.add("IN_A") for _ in range(WIDTH)]
        b = [self.add("IN_B") for _ in range(WIDTH)]
        c = [self.add("IN_C") for _ in range(WIDTH)]
        d = [self.add("IN_D") for _ in range(WIDTH)]
        self.input_ids = a + b + c + d
        return a, b, c, d, self._zero, self._one

    # ------------------------------------------------------- gate primitives

    def _gate(self, kind, *inputs, absorption=False):
        """Constant-fold, complement-fold, and hash-cons local gates."""
        zero, one = self._zero, self._one
        if kind == "NOT":
            source = inputs[0]
            if source == zero:
                return one
            if source == one:
                return zero
            node = self.nodes[source]
            if node.kind == "NOT":
                return node.inputs[0]
        else:
            a, b = inputs
            if a == b:
                return zero if kind == "XOR" else a
            if kind == "AND":
                if zero in inputs:
                    return zero
                if one in inputs:
                    return b if a == one else a
            elif kind == "OR":
                if one in inputs:
                    return one
                if zero in inputs:
                    return b if a == zero else a
            elif kind == "XOR":
                if zero in inputs:
                    return b if a == zero else a
                if one in inputs:
                    return self._not(b if a == one else a)
            if absorption:
                if kind == "OR":
                    for operand, other in ((a, b), (b, a)):
                        on = self.nodes[other]
                        if on.kind == "AND" and operand in on.inputs:
                            return operand
                elif kind == "AND":
                    for operand, other in ((a, b), (b, a)):
                        on = self.nodes[other]
                        if on.kind == "OR" and operand in on.inputs:
                            return operand
            na, nb = self.nodes[a], self.nodes[b]
            if ((na.kind == "NOT" and na.inputs[0] == b) or
                    (nb.kind == "NOT" and nb.inputs[0] == a)):
                return zero if kind == "AND" else one
            if inputs[1] < inputs[0]:
                inputs = (inputs[1], inputs[0])
        key = (kind, inputs)
        node = self._gate_cache.get(key)
        if node is None:
            node = self.add(kind, *inputs)
            self._gate_cache[key] = node
        return node

    def _and(self, a, b):
        return self._gate("AND", a, b)

    def _and_absorb(self, a, b):
        return self._gate("AND", a, b, absorption=True)

    def _or(self, a, b):
        return self._gate("OR", a, b)

    def _or_absorb(self, a, b):
        return self._gate("OR", a, b, absorption=True)

    def _xor(self, a, b):
        return self._gate("XOR", a, b)

    def _not(self, a):
        return self._gate("NOT", a)

    # ----------------------------------------------------------- arithmetic

    def _fa(self, a, b, cin):
        """Exact 7-gate full adder with shared OR/XNOR terms."""
        ac = self._and(a, cin)
        aoc = self._or(a, cin)
        xn = self._or(ac, self._not(aoc))
        b_or_xn = self._or(b, xn)
        total = self._or(self._not(b_or_xn), self._and(b, xn))
        carry = self._and(aoc, b_or_xn)
        return total, carry

    def _ha(self, a, b):
        """Exact half adder: carry = a&b, sum = (a|b)&~carry."""
        carry = self._and(a, b)
        total = self._and(self._or(a, b), self._not(carry))
        return total, carry

    def _add3(self, x, y, z):
        """Constant-aware 3:2 compressor dispatching to _fa/_xor/_ha."""
        zero, one = self._zero, self._one
        consts = [n for n in (x, y, z) if n in (zero, one)]
        reals = [n for n in (x, y, z) if n not in (zero, one)]
        if not consts:
            return self._fa(x, y, z)
        if len(consts) == 1:
            a, b = reals
            if one in consts:
                carry = self._or(a, b)
                total = self._or(self._and(a, b), self._not(carry))
                return total, carry
            return self._xor(a, b), self._and(a, b)
        if len(consts) == 2:
            a = reals[0]
            if zero in consts and one in consts:
                return self._not(a), a
            if one in consts:
                return a, one
            return a, zero
        n = consts.count(one)
        return (one if n == 1 else zero), (one if n > 1 else zero)
