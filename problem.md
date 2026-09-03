# 9-bit Approximate Fixed-Point Multiplier Search

Generate and optimize signed 9-bit gate-level approximate multiplier circuits.

Constraints:

- Each input is a 9-bit two's-complement Q2.7 code in `[-256, 255]`.
- The circuit has two 9-bit input buses and an 18-bit two's-complement Q4.14 output bus. Bus lists are least-significant bit first.
- Evaluation externally rounds Q4.14 to Q4.7 to nearest, with ties away from zero. MAE, RMSE, and maximum error are reported in real-value units.
- Candidates expose only a zero-argument `build_circuit()` that returns `multiplier.circuit.Circuit`.
- A candidate generates a static, input-independent DAG. It must not simulate inputs, compute scores, or override gate costs.
- Gate nodes may use only AND, OR, XOR, and NOT. ZERO, ONE, IN_A, and IN_B are allowed leaves.
- Fixed external gate costs are AND=1, OR=1, XOR=3, and NOT=0. Only output-reachable gates are counted.
- Configured baseline implementations are read-only seeds. Mutations operate on copies under `generations/` only.
- The search minimizes weighted gate cost and Q4.7 real-value MAE.
- Each generation's non-dominated candidates are preserved under `generations/<generation>/`.
