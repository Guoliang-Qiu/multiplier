"""Shared pre-compression insertion contract for tables and exported circuits."""
from .node_set_information import build_experiment

MODEL = 'precompression_append_v1'

def prepare(implementation, removed_slots):
    # Reuse slot validation; preserve every original prefix node, including
    # observation cones no longer reachable from the remaining slots.
    build_experiment(implementation, removed_slots)
    circuit = implementation()
    buses = circuit.setup()
    circuit._columns = circuit._product_columns(*buses)
    for col, pos in sorted(map(tuple, removed_slots), reverse=True):
        del circuit._columns[col][pos]
    return circuit

def finish(circuit, columns, nodes):
    for col, node in zip(columns, nodes):
        # Fixed opaque buffers keep compressor scheduling/constant dispatch
        # identical for enumerated constant actions and symbolic G outputs.
        # Both table and export retain these actual gates and charge their cost.
        circuit._columns[col].append(circuit.add('OR', node, circuit._zero))
    circuit._compress_columns()
    circuit._build_outputs()
    circuit.validate()
    return circuit
