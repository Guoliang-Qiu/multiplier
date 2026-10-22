"""Old candidate primitives on the current three-stage multiplier interface.

Candidates implement real joint layout, compression and output stages. This
module only preserves their gate policy and layout-analysis entry points.
"""
from multiplier.circuit.multiplier.tap2_9bit_multiplier import MultiplierCircuit


class StagedCandidate(MultiplierCircuit):
    _USE_ABSORPTION = False

    def _gate(self, kind, *inputs, absorption=False):
        return super()._gate(kind, *inputs,
                             absorption=absorption or self._USE_ABSORPTION)

    @staticmethod
    def _bit(bits, index, zero):
        if index < 0:
            return zero
        return bits[min(index, len(bits) - 1)]

    @staticmethod
    def _qsub(q, step, zero):
        return (q[min(2 * step + 1, len(q) - 1)], q[2 * step],
                q[2 * step - 1] if step else zero)


def build_layout(candidate_type):
    circuit = candidate_type()
    buses = circuit.setup()
    columns = circuit._product_columns(*buses)
    circuit._columns = [list(bucket) for bucket in columns]
    return circuit, [list(bucket) for bucket in columns]


def finish_columns(circuit, columns):
    """Finish on the original instance, retaining IDs of supplied nodes."""
    if circuit.output_ids:
        raise ValueError('expected a pre-compression layout circuit')
    circuit._columns = [list(bucket) for bucket in columns]
    circuit._compress_columns()
    circuit._build_outputs()
    return circuit
