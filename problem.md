# 9-bit Approximate Multiplier Search

Generate and optimize signed 9-bit gate-level approximate multiplier candidates.

Constraints:

- Use only AND, OR, XOR, and NOT logic gates.
- Gate costs are AND=1, OR=1, XOR=3, and NOT=0.
- Preserve a clear gate-level Python netlist that can be simulated.
- Candidate implementations are read-only seeds under `initial_solutions/`; work on
  copies in the task root and never modify the seed files.
- The search minimizes both weighted gate cost and error against exact `a * b`.
- Each generation's non-dominated candidates must be preserved under
  `generations/<generation>/`.

Each candidate must expose `multiply(a, b)` and `build_multiplier(a, b)`.
