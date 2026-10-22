"""Circuit package public API.

Generic implementation is split into ``components``, ``model``, ``simulation``,
``analysis``, ``cost`` and ``validation``.  Multiplier-specific extensions
(9-bit signed inputs, legacy IN_A/IN_B/IN_C/IN_D, gate primitives, build
pipeline) live in the ``multiplier`` sub-package and are re-exported here.
"""
from .components import ComponentLibrary, ComponentSpec, STANDARD_COMPONENTS
from .model import Node
from .cost import GateCost, gatecost
from .validation import validate_circuit
from .simulation import simulate, simulate_many
from .analysis import (
    DependencyDecomposition,
    decompose_dependencies,
    reachable_node_ids,
)
from .multiplier import (
    Circuit, MultiplierCircuit, INPUT_WIDTH, WIDTH, OUT_WIDTH, OUT_TOTAL,
)

__all__ = [
    "Circuit", "MultiplierCircuit", "ComponentLibrary", "ComponentSpec",
    "DependencyDecomposition", "GateCost", "Node", "INPUT_WIDTH", "WIDTH",
    "OUT_WIDTH", "OUT_TOTAL", "decompose_dependencies", "gatecost",
    "simulate", "simulate_many", "reachable_node_ids", "validate_circuit",
    "STANDARD_COMPONENTS",
]
