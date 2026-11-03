"""Compatibility for historical candidates with their own complete builder.

No compressor/CPA is substituted: every candidate's original _build_circuit
remains authoritative. Stage hooks fail loudly if used independently.
"""
from multiplier.circuit.multiplier.tap2_9bit_multiplier import MultiplierCircuit as _Base

class LegacyMultiplierCircuit(_Base):
    _USE_ABSORPTION = False

    def _gate(self, kind, *inputs, absorption=False):
        return super()._gate(kind, *inputs, absorption=absorption or self._USE_ABSORPTION)

    @staticmethod
    def _bit(bits, index, zero):
        return zero if index < 0 else bits[min(index, len(bits)-1)]

    @staticmethod
    def _qsub(q, step, zero):
        return (q[min(2*step+1,len(q)-1)], q[2*step], q[2*step-1] if step else zero)

    def _compress_columns(self):
        raise NotImplementedError('Historical compression is inside _build_circuit')

    def _build_outputs(self):
        raise NotImplementedError('Historical CPA is inside _build_circuit')
