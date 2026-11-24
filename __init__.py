"""Multiplier workspace with a single shared circuit implementation."""

import os
from pathlib import Path
import sys

# Existing candidates import multiplier.circuit. Resolve that name to the
# shared kit instead of maintaining a second circuit package in this workspace.
_solver_root = Path(os.environ.get(
    "OPEN_QUESTION_SOLVER_ROOT",
    Path(__file__).resolve().parent.parent / "open_question_solver",
)).resolve()
if not (_solver_root / "tools" / "circuit_kit" / "circuit").is_dir():
    raise ImportError(f"Shared circuit kit not found under {_solver_root}")
if str(_solver_root) not in sys.path:
    sys.path.insert(0, str(_solver_root))

from tools.circuit_kit import circuit as _circuit

sys.modules[__name__ + ".circuit"] = _circuit

from multiplier.circuit import (
    Circuit,
    GateCost,
    Node,
    simulate,
    simulate_many,
    validate_circuit,
)

__all__ = [
    "Circuit",
    "GateCost",
    "Node",
    "simulate",
    "simulate_many",
    "validate_circuit",
]
