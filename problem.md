# Four-Input 9-bit Approximate Fixed-Point Multiplier Search

Generate and optimize signed 9-bit gate-level approximate circuits for the
two-product sum `a*b + c*d`.

Constraints:

- There are four independent 9-bit two's-complement Q2.7 input buses,
  `a`, `b`, `c`, and `d`, each with codes in `[-256, 255]`.
- The circuit computes the fixed-point sum `a*b + c*d` and exposes a 19-bit
  two's-complement Q4.14 output bus. Input and output bus lists are
  least-significant bit first.
- The exact real-valued reference is `(a*b + c*d) / 128`.
- Evaluation quantizes only the circuit result from Q4.14 to Q4.7 using
  `floor(raw / 128 + 0.5)`. MAE, RMSE, maximum absolute error, error rate,
  and related metrics are reported in real-value units.
- Four-input evaluation enumerates every unordered `(b, d)` pair in the
  signed 9-bit domain and samples a fixed number of `(a, c)` values per pair
  using RNG seed 42. The per-pair sample count is controlled by
  `TAP2_COPIES` and defaults to 8.
- Candidates expose only a zero-argument `build_circuit()` that returns `multiplier.circuit.Circuit`.
- A candidate generates a static, input-independent DAG. It must not simulate inputs, compute scores, or override gate costs.
- Gate nodes may use only AND, OR, XOR, and NOT. ZERO, ONE, IN_A, IN_B,
  IN_C, and IN_D are allowed leaves.
- Four-input candidates must use the input buses in fixed `a`, `b`, `c`, `d`
  order, with leaves `IN_A`, `IN_B`, `IN_C`, and `IN_D`.
- Fixed external gate costs are AND=1, OR=1, XOR=3, and NOT=0. Only output-reachable gates are counted.
- Configured baseline implementations are read-only seeds. Mutations operate on copies under `generations/` only.
- The search minimizes weighted gate cost and Q4.7 real-value MAE for the
  four-input `a*b + c*d` objective.
- Each generation's non-dominated candidates are preserved under `generations/<generation>/`.
