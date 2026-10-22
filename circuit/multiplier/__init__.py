"""Multiplier-specific circuit extensions.

Extends the generic circuit package with 9-bit signed input support and
legacy IN_A/IN_B/IN_C/IN_D leaf components used by the multiplier candidates.

All functional code lives in :mod:`.base` — this module re-exports the public
API for backward compatibility.
"""
from ..components import ComponentLibrary, ComponentSpec, STANDARD_COMPONENTS
from ..model import Node
from ..cost import GateCost, gatecost
from ..validation import validate_circuit
from ..simulation import simulate, simulate_many, _simulate_packed_values
from ..analysis import (
    DependencyDecomposition,
    decompose_dependencies,
    reachable_node_ids,
)
from .tap2_9bit_multiplier import (
    Circuit,
    MultiplierCircuit,
    INPUT_WIDTH,
    WIDTH,
    OUT_WIDTH,
    OUT_TOTAL,
)

__all__ = [
    "Circuit", "MultiplierCircuit", "ComponentLibrary", "ComponentSpec",
    "DependencyDecomposition", "GateCost", "Node", "INPUT_WIDTH", "WIDTH",
    "OUT_WIDTH", "OUT_TOTAL", "decompose_dependencies", "gatecost",
    "simulate", "simulate_many", "reachable_node_ids", "validate_circuit",
    "STANDARD_COMPONENTS",
]
