from importlib import import_module

_mod = import_module("multiplier.9_bits_signed_exact_multiplier")

WIDTH = _mod.WIDTH
build_multiplier = _mod.build_multiplier
multiply = _mod.multiply

__all__ = ["WIDTH", "build_multiplier", "multiply"]
