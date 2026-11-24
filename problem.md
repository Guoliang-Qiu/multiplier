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
- Candidates provide a zero-argument `build_circuit()` returning the shared tap2
  `Circuit`, with a readable `Candidate(MultiplierCircuit)` implementation.
- A candidate generates a static, input-independent DAG. It must not simulate inputs, compute scores, or override gate costs.
- Candidates based on `MultiplierCircuit` must implement the complete construction
  stages `_product_columns(a, b, c, d, zero, one)`, `_compress_columns()`, and
  `_build_outputs()`. The base `_build_circuit()` calls them in that order:
  setup the four LSB-first input buses, generate one joint pre-compression
  column layout for `a*b + c*d`, compress the columns, and create
  `output_ids`. `_product_columns()` receives all four buses together so a
  candidate may share logic across both products and must return the complete
  list of weighted columns. `_compress_columns()` and `_build_outputs()` are
  abstract extension points rather than fixed algorithms; candidates may use
  the reference implementations `_compress_columns_reference()` and
  `_build_outputs_reference()` or implement custom approximate, fused, wider,
  truncated, or low-bit carry logic. The construction must still return a
  complete valid circuit and set the required output bus. Preserve the actual
  semantic boundaries of partial-product generation, compression, and output
  construction, not just the method names. Do not move compression into
  `_product_columns()` to reduce the reported partial-product count or flatten
  the implementation into opaque gate replay.
- Reuse the implementations provided by
  `tools.circuit_kit.circuit.multiplier.tap2_9bit_multiplier.MultiplierCircuit`.
  Before adding or changing a helper, check whether tap2 already provides it.
  Do not copy or reimplement equivalent gate primitives, constant folding,
  hash-consing, input setup, full/half adders (`_fa`, `_ha`), or constant-aware
  compressors (`_add3`). When a construction stage matches the library's
  reference algorithm, delegate to that reference implementation instead of
  duplicating its body. Do not add no-op overrides or forwarding wrappers.
- Override a tap2 implementation only when the candidate genuinely needs a
  different realization, such as a different gate-sharing structure, an
  approximate compressor, or specialized carry handling. Document the specific
  difference and why it is needed; keep the override limited to that behavior.
  Inheritance enables reuse; it does not require calling every parent method.
  A genuinely tuned subclass implementation may replace a stage or helper
  without calling `super()`. Follow any additional stage-specific restrictions
  in the active mutation or crossover task.
  For refactoring intended to preserve the circuit, verify graph/output
  equivalence and weighted cost. For algorithmic changes, validate the complete
  circuit with `gate_cost.py` and `eval.py` rather than assuming a shorter
  expression is cheaper or equally accurate.
- Approximation must be implemented as a runnable circuit, not as a post-processing
  rule or a predicted score. Every approximation scheme must be evaluated by the
  existing `eval.py` procedure, using
  `--stimulus-file /home/guoliang/multiplier/stimulus.npy`, Q4.7 quantization,
  and the existing `evm_db` calculation. Screening and error-table generation
  must also use this external stimulus file, not replacement stimuli.
- The search should explicitly consider targeted approximation schemes that are
  effective for this objective, including partial-product truncation or removal,
  simplified compressors/adders, selective rounding, and compensation constants.
  These choices must be judged by the `eval.py` results and weighted gate cost,
  rather than by gate count or an isolated local error estimate.
- Gate nodes may use AND, OR, XOR, NOT, and MUX_XOR. ZERO, ONE, IN_A, IN_B,
  IN_C, and IN_D are allowed leaves.
- MUX_XOR is a supported optimization component, not a legacy or prohibited
  gate. It computes `e ^ ((a & b) | (c & d))`. The current shared tap2 API uses
  port order `(a, b, c, d, e)`; inspect the actual library before wiring it.
  Do not expand existing MUX_XOR cells merely to satisfy a primitive-only
  whitelist or work around a tool's integer-cost assumption. Expansion is an
  optimization option only when justified by measured complete-circuit results.
- Four-input candidates must use the input buses in fixed `a`, `b`, `c`, `d`
  order, with leaves `IN_A`, `IN_B`, `IN_C`, and `IN_D`.
- The current shared-library gate costs are AND=1, OR=1, XOR=3, NOT=0, and
  MUX_XOR=4.8. Only output-reachable gates are counted. The workspace evaluator
  and installed component library are authoritative; candidates must not
  override costs. Weighted costs and cost savings may be fractional and must
  not be rounded to integers for acceptance or comparison. Report tool
  incompatibilities rather than changing the allowed component set to hide them.
- Configured baseline implementations are read-only seeds. Mutations operate on copies under `generations/` only.
- The search minimizes three objectives: `[gate_cost, evm_db,
  partial_product_count]`, for the four-input `a*b + c*d` circuit. Count every
  column slot immediately before compression, including constants, compensation
  bits, and repeated uses. Respect the active runtime EVM limit and compare
  complete-circuit trade-offs against the current Pareto population.
- For equivalence-preserving rewrites, check raw-output bitwise equality on the
  configured stimulus as well as complete gate cost and EVM. Equal EVM alone
  is not equivalence; distinguish sample-based checks from formal proofs.
- Selected candidates are stored under `generations/<generation>/`; the
  cross-generation Pareto archive is stored under `generations/pareto_archive/`.
