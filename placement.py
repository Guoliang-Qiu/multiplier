"""Generic CSA/CPA rebuild used by placement-aware initial solutions."""

from __future__ import annotations

from multiplier.circuit import Circuit


def rebuild_columns(circuit: Circuit, columns: list[list[int]]) -> Circuit:
    """Rebuild an exact carry-save/final adder from pre-CSA columns.

    This compatibility path deliberately uses the standard full adder. A
    candidate may provide a more specialized implementation by replacing its
    ``build_circuit_from_columns`` wrapper.
    """
    zero = next(node_id for node_id, node in enumerate(circuit.nodes) if circuit.nodes[node_id].kind == "ZERO")

    def xor(a, b): return circuit.add("XOR", a, b)
    def and_(a, b): return circuit.add("AND", a, b)
    def or_(a, b): return circuit.add("OR", a, b)

    def add3(a, b, cin):
        ab = xor(a, b)
        total = xor(ab, cin)
        carry = or_(and_(a, b), and_(ab, cin))
        return total, carry

    columns = [list(column) for column in columns]
    for col in range(len(columns)):
        while len(columns[col]) >= 3:
            total, carry = add3(columns[col].pop(), columns[col].pop(), columns[col].pop())
            columns[col].append(total)
            if col + 1 < len(columns):
                columns[col + 1].append(carry)

    outputs = []
    carry = None
    for bucket in columns:
        bucket = bucket or [zero]
        if carry is None:
            if len(bucket) == 1:
                outputs.append(bucket[0])
            else:
                outputs.append(xor(bucket[0], bucket[1]))
                carry = and_(bucket[0], bucket[1])
        elif len(bucket) == 1:
            outputs.append(xor(bucket[0], carry))
            carry = and_(bucket[0], carry)
        else:
            total, carry = add3(bucket[0], bucket[1], carry)
            outputs.append(total)

    width = circuit.output_width
    if len(outputs) < width:
        outputs.extend([zero] * (width - len(outputs)))
    circuit.output_ids = outputs[:width]
    return circuit
