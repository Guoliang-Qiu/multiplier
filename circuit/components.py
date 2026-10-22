"""Component declarations and closed component libraries."""
from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Iterable

@dataclass(frozen=True)
class ComponentSpec:
    name: str
    arity: int
    gate_cost: int = 0
    category: str = "gate"
    truth_table: tuple[int, ...] = ()

    def __post_init__(self):
        if self.arity < 0:
            raise ValueError("component arity cannot be negative")
        expected = 1 << self.arity
        table = self.truth_table
        if not table:
            raise ValueError(f"{self.name} must declare a truth table")
        if len(table) != expected:
            raise ValueError(
                f"{self.name} truth table must contain {expected} entries"
            )
        if any(value not in (0, 1) for value in table):
            raise ValueError(f"{self.name} truth table values must be 0 or 1")


STANDARD_COMPONENTS = (
    ComponentSpec("AND", 2, gate_cost=1, truth_table=(0, 0, 0, 1)),
    ComponentSpec("OR", 2, gate_cost=1, truth_table=(0, 1, 1, 1)),
    ComponentSpec("NOT", 1, truth_table=(1, 0)),
    ComponentSpec("INPUT", 0, category="leaf", truth_table=(0,)),
    ComponentSpec("ZERO", 0, category="leaf", truth_table=(0,)),
    ComponentSpec("ONE", 0, category="leaf", truth_table=(1,)),
)

class ComponentLibrary:
    def __init__(self, components: Iterable[ComponentSpec]):
        self._components = {component.name: component for component in components}
        if not self._components:
            raise ValueError("component library cannot be empty")

    @classmethod
    def standard(cls) -> "ComponentLibrary":
        return cls(STANDARD_COMPONENTS)

    def require(self, name: str) -> ComponentSpec:
        try:
            return self._components[name]
        except KeyError as error:
            raise ValueError(f"component {name!r} is not declared") from error

    def names(self) -> tuple[str, ...]:
        return tuple(self._components)

    def __contains__(self, name: str) -> bool:
        return name in self._components

    def __len__(self) -> int:
        return len(self._components)
