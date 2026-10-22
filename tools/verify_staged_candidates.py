"""Verify candidate stage APIs and graph-preserving layout completion."""
import importlib
import inspect
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from multiplier.candidate_support.staged import build_layout, finish_columns
from multiplier.circuit.multiplier.tap2_9bit_multiplier import MultiplierCircuit
from multiplier.circuit.multiplier.conditional_compensation import candidate_g0001_0005_col2_joint_asym as reference


def main():
    folder = Path(__file__).resolve().parents[1] / 'initial_solutions'
    count = 0
    for path in sorted(folder.glob('*.py')):
        mod = importlib.import_module('multiplier.initial_solutions.' + path.stem)
        cls = getattr(mod, 'Candidate', None)
        if cls is None:
            continue
        assert not inspect.isabstract(cls), path
        assert cls._build_circuit is MultiplierCircuit._build_circuit, path
        direct = mod.build_circuit()
        layout, cols = build_layout(cls)
        assert not layout.output_ids and len(cols) == 19
        prefix = tuple(layout.nodes)
        assert tuple(direct.nodes[:len(prefix)]) == prefix, path
        rebuilt = finish_columns(layout, cols)
        assert direct.nodes == rebuilt.nodes, path
        assert direct.input_ids == rebuilt.input_ids, path
        assert direct.output_ids == rebuilt.output_ids, path
        direct.validate()
        count += 1
    migrated = importlib.import_module(
        'multiplier.initial_solutions.candidate_g0001_0005_col2_joint_asym').build_circuit()
    supplied = reference.build_circuit()
    assert migrated.nodes == supplied.nodes
    assert migrated.output_ids == supplied.output_ids
    assert migrated.input_ids == supplied.input_ids
    print(f'{count} staged candidates: complete graph equality for staged/direct construction.')
    print('1084 candidate: node-for-node equal to supplied conditional_compensation reference.')


if __name__ == '__main__':
    main()
