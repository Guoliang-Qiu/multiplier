import unittest

from multiplier.circuit import (
    Circuit,
    SubcircuitObservation,
    build_subcircuit_truth_table,
    collect_subcircuit_observations,
    extract_subcircuit,
)


def make_test_circuit(mask_output: bool = False):
    circuit = Circuit()
    zero = circuit.add("ZERO")
    a_ids = [circuit.add("IN_A") for _ in range(9)]
    b_ids = [circuit.add("IN_B") for _ in range(9)]
    xor = circuit.add("XOR", a_ids[0], b_ids[0])
    both = circuit.add("AND", a_ids[0], b_ids[0])
    either = circuit.add("OR", xor, both)
    output = circuit.add("AND", either, zero) if mask_output else either
    circuit.input_ids = a_ids + b_ids
    circuit.output_ids = [output] + [zero] * 17
    return circuit, (xor, both, either), (a_ids[0], b_ids[0])


class SubcircuitTest(unittest.TestCase):
    def test_extracts_boundary_from_edges(self):
        circuit, nodes, inputs = make_test_circuit()

        subcircuit = extract_subcircuit(circuit, nodes)

        self.assertEqual(subcircuit.node_ids, nodes)
        self.assertEqual(subcircuit.input_ids, inputs)
        self.assertEqual(subcircuit.output_ids, (nodes[-1],))

    def test_real_inputs_leave_unobserved_patterns_as_dont_cares(self):
        circuit, nodes, _ = make_test_circuit()
        subcircuit = extract_subcircuit(circuit, nodes)
        observations = collect_subcircuit_observations(
            circuit, subcircuit, [(0, 0), (0, 1), (1, 0)]
        )

        table = build_subcircuit_truth_table(observations)

        self.assertEqual([row.input_values for row in table], [(0, 0), (0, 1), (1, 0)])
        self.assertNotIn((1, 1), [row.input_values for row in table])
        self.assertEqual([row.allowed_outputs for row in table], [
            ((0,),), ((1,),), ((1,),)
        ])

    def test_masked_output_is_observability_dont_care(self):
        circuit, nodes, _ = make_test_circuit(mask_output=True)
        subcircuit = extract_subcircuit(circuit, nodes)

        table = build_subcircuit_truth_table(collect_subcircuit_observations(
            circuit, subcircuit, [(0, 0), (0, 1)]
        ))

        self.assertEqual(table[0].allowed_outputs, ((0,), (1,)))
        self.assertEqual(table[1].allowed_outputs, ((0,), (1,)))

    def test_repeated_local_input_intersects_global_constraints(self):
        observations = [
            SubcircuitObservation((0, 0), (1,), (0,), ((0,), (1,))),
            SubcircuitObservation((1, 1), (1,), (0,), ((0,),)),
        ]

        table = build_subcircuit_truth_table(observations)

        self.assertEqual(table[0].allowed_outputs, ((0,),))
        self.assertEqual(table[0].occurrences, 2)


if __name__ == "__main__":
    unittest.main()
