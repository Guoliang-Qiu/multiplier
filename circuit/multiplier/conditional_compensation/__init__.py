"""Offline residual-information screening for multiplier candidates."""


def __getattr__(name):
    if name in {"build_experiment", "conditional_variance", "evaluate_node_set"}:
        from . import node_set_information
        return getattr(node_set_information, name)
    raise AttributeError(name)
