# Agent Guide: Partial-Product Removal and Compensation Optimization

This directory provides a staged optimization workflow. The agent reads the
candidate implementation and selects removal slots, observation nodes X, and
compensation positions. The tools measure the proposal, generate an error table,
synthesize a cost-bounded G(X), and export a complete candidate. Parameter
selection is an arithmetic and structural design decision, not blind enumeration.

## Node-set linear information model (default)

`evaluate_node_set` now defaults to `deletion_model="linear"`. If P is the
baseline signed raw output and D is the weighted sum of the selected original
column slots, the analytical deleted value is **P-D**, with no floor and no
19-bit wrap. The residual is `(T-P+D)/128`. This does not construct a cheaper
circuit. Its `deleted.gate_cost` is null; `physical_deletion_gate_cost` is a
separate measurement of actual slot deletion, not the cost of P-D.

Compare `information_mse` with `baseline_conditional_variance` using the SAME X,
not with baseline MSE or unconditional variance. If X determines D exactly,
`removed_conditional_variance` and `conditional_variance_gap` must both be zero.
X may be any nonconstant pre-compression nodes in this analytical mode;
`x_unreachable_after_physical_deletion` identifies nodes that cannot be reused
for free after deletion.

Set `deletion_model="physical"` to recover the legacy quantized-residual
screening described below. **Error-table, SMT, and export tools still model
physical deletion followed by exact output addition.** Linear-model variance
and physical-model error budgets must not be interchanged.

## Recommended Agent Workflow

1. Inspect `_product_columns`, `_compress_columns` and `_build_outputs`. Record
   the baseline performance/cost and the original low-column slot layout. Keep
   seed files unchanged; generate experiments as new files.
2. Select a coherent group of removable slots in columns 0--5. Inspect node
   functions and sharing, not just their IDs. Removing a slot may save no gates
   if its logic remains needed elsewhere, and can change compressor scheduling.
3. Choose retained pre-compression nodes X that may explain the lost contribution
   or the quantization boundary. Use `node_set_information.py` to measure the
   proposal. Its conditional variance is an output-domain information heuristic,
   not a rigorous rejection bound for pre-quantization compensation.
4. Choose at most three G output positions using the range/granularity analysis
   below. Generate a fresh error table for this exact X, deletion and position
   choice with `compensation_error_table.py`.
5. Run `synthesize.py` under the target EVM constraint and measured deletion
   saving. Let SMT choose G's outputs jointly with its gate implementation;
   do not fix each state's minimum-error output in advance.
6. Export the SAT solution with `export_candidate.py`. Measure the final full
   candidate with the authoritative evaluator and reachable gate-cost calculation.
   Retain improvements based on these final measurements, not just G's cost or
   a table-derived EVM. Record the chosen positions and their justification.

## Choosing Compensation Positions: Range and Granularity

The compensation positions are **not arbitrary tuning parameters**. Match their
numeric expressive range to the contribution removed and the correction actually
needed. Do not give G a much larger range merely because the API permits high
columns: this can waste gates, introduce large errors, or exploit output wrapping
rather than produce a useful local compensation.

For removed slots with columns `c_i` and bit functions `p_i(s)`, their weighted
contribution is `D(s) = sum(2**c_i * p_i(s))`. A conservative unsigned range is
`0 <= D <= sum(2**c_i)`. Tighten this using constants, repeated/shared signals,
correlations and reachable input patterns; these slots need not be independent.
Keep signed Booth corrections and sign-extension conventions in the analysis.

For chosen compensation columns `k_j`, enumerate the actual representable set:

```
C = {sum(2**k_j * b_j) : each b_j is 0 or 1}
```

Compare both its maximum and the gaps between its values to D's range. At most
three bits allow at most eight encodings, but repeated columns can give fewer
distinct numeric values. A broad range with coarse steps may miss useful small
corrections; an unnecessarily fine or wide encoding may cost more than it saves.

### Example: Removing Three Bits in Column k

The removed weighted sum is `(p0+p1+p2)*2**k`, potentially taking values
`{0,1,2,3}*2**k`.

| New compensation columns | Representable values | Design interpretation |
|---|---|---|
| `[k, k+1]` | `{0,1,2,3}*2**k` | Natural two-bit encoding of the full removed sum range. |
| `[k, k, k]` | `{0,1,2,3}*2**k` | Same numeric range but three outputs; examine whether G sharing justifies it. |
| `[k+1]` | `{0,2}*2**k` | A cheaper, coarser approximation worth evaluating if performance allows. |
| `[k, k+1, k+2]` | `{0,...,7}*2**k` | Exceeds the removed sum range; do not select without evidence of a broader correction need. |

For example, three removed bits in column 4 can contribute 0, 16, 32 or 48.
Positions `[4,5]` encode exactly these values; a high-weight bit in column 10
adds 1024 and is not a sensible default replacement for this local loss.

Matching the range does **not** prove X can determine the removed value or that
G will be cheap. Also, the existing candidate can use approximate compressors,
low-bit pruning and asymmetric compensation. Consequently the actual raw-output
change after deletion need not equal D(s), and the best correction may account
for existing bias or the rounding threshold. Treat range matching as the default
design principle, not a universal hard constraint. Any deliberately wider range
should be justified by measured raw-output/residual behavior and final savings.

The current model adds nonnegative weighted bits to the deleted raw output.
It does not provide a signed correction control. Do not use high-bit wraparound
as an unexplained substitute for a negative correction. The exporter implements
this exact addition after the deleted circuit, not injection into its approximate
compressors, so include the cost of that exact addition in the final decision.

## Configuration

The first-stage tool only evaluates one agent-selected removal and X choice;
it does not search for them or synthesize G.

```json
{
  "implementation": "/home/guoli/open_question_solver/tools/circuit_kit/circuit/multiplier/conditional_compensation/candidate_g0001_0005_col2_joint_asym.py",
  "removed_slots": [[4, 0]],
  "node_ids": [2, 3]
}
```

Run from `/home/guoli/open_question_solver`:

```bash
python -m tools.circuit_kit.circuit.multiplier.conditional_compensation.node_set_information config.json --output report.json
```

- `implementation`: Python module exposing the concrete `Candidate` class.
- `removed_slots`: original pre-compression `(column, position)` pairs. Only
  columns 0 through 5 can be removed. Positions are all measured before deletion.
  Duplicate uses of a node are distinct slots; nodes are not globally deleted.
- `node_ids`: exactly one ordered X vector. `[2,3]` evaluates `(node2,node3)`
  only, not its subsets. IDs must be distinct, nonconstant pre-compression nodes
  still reachable in the deleted circuit. At most 16 nodes are supported for
  the dense state table. `[]` measures the no-information baseline `Var(R)`.

The implementation must put its logic in `_product_columns`,
`_compress_columns` and `_build_outputs` and support deepcopy of instance state.
The tool forks a common pre-compression snapshot, deletes the specified slots
from one copy, and completes both circuits using their own stage methods.
It does not call a custom `_build_circuit` override.

## Python API and layout inspection

```python
from tools.circuit_kit.circuit.multiplier.conditional_compensation import (
    build_experiment, evaluate_node_set,
)
from tools.circuit_kit.circuit.multiplier.conditional_compensation.candidate_g0001_0005_col2_joint_asym import Candidate

baseline, deleted, columns, prefix_size = build_experiment(Candidate, [])
print(columns[:6])
report = evaluate_node_set(Candidate, removed_slots=[(4, 0)], node_ids=[2, 3])
```

The included example has the same complete 1,439-node DAG and input/output IDs
as the original candidate, with weighted reachable cost 1,084. Its original
column heights 0--5 are `[0,0,4,4,6,6]`. ZERO slots are intentionally preserved
to retain compressor scheduling. The original candidate files are not imported
or modified. Removing `(4,0)` gives cost 1,071, not a claim of improved EVM.

## Statistics and report

Samples are generated locally by `generate_evaluation_samples()`: enumerate
unordered `(b,d)` pairs (`b <= d`), independently draw `a,c` from permutations
with seed 42 and `TAP2_COPIES` (default 8). This produces 1,050,624 samples by
default, in the tap2 evaluator's order, without importing `eval.py`. It is not
independent uniform sampling of all four operands. Python callers may pass
`samples` explicitly for tests.

For each sample:

```
reference = (a*b+c*d)/128
R = reference - floor(deleted_raw/128 + 0.5)
information_mse = sum_x count(x)/N * Var(R | X=x)
```

The JSON report contains the sampling metadata, reference energy, baseline and
deleted MSE/EVM/cost, removed slots, node IDs, and information MSE. The first
supplied node is bit 0 of the X state code. No `.npy` sidecar is produced.
Later column-compensation tools must evaluate their candidate actions through
the complete compressor, carry and quantization path rather than treating a
conditional mean as an additive column correction.

The baseline candidate need not be exact. The mathematical reference is always
used for R. Conditional variance is a sample-based lower bound for unrestricted
real additive correction of the quantized output, not a certified population
bound or a bound for arbitrary column injection before nonlinear rounding and
approximate compression. For column-injected G, use it as an information metric
and evaluate complete-circuit action losses before implementation. No G is
fitted by this tool.

## Integer Compensation Error Table for SMT

`compensation_error_table.py` is the second-stage numerical experiment. It accepts
the agent-selected `node_ids` and at most three `compensation_columns`. For
each X state, it enumerates all `2**len(compensation_columns)` bit assignments,
adds their exact weighted raw value to `deleted_raw`, applies the final
quantization, and reports the conditional error table.

```bash
PYTHONPATH=/home/guoli/open_question_solver/tools/circuit_kit \
python -m circuit.multiplier.conditional_compensation.compensation_error_table \
  /home/guoli/open_question_solver/tools/circuit_kit/circuit/multiplier/conditional_compensation/example_error_table_config.json \
  --output /home/guoli/open_question_solver/tools/circuit_kit/circuit/multiplier/conditional_compensation/example_error_table_result.npy
```

For columns `[4,5,6]`, the eight raw compensation values are:

```text
0, 16, 32, 48, 64, 80, 96, 112
```

`error_table[x][y]` contains the integer sum
`sum((T_i - 128*Y_i(y))**2 for i where X_i == x)`, with
`T_i=a_i*b_i+c_i*d_i` and `Y_i(y)=floor((wrap19(D_i+C(y))+64)/128)`.
The integer division is exact, including for negative values. This models exact
weighted addition to the deleted result, not insertion into approximate
compressors. Overflow follows signed 19-bit wrapping.

Rows encode X with `node_ids[0]` as bit 0. Columns encode G with
`compensation_columns[0]` as bit 0. Repeated compensation columns are allowed:
they represent separate partial products at the same weight. Unobserved X
states have all-zero rows and zero `state_counts`; they are not proven
unreachable. No G truth table is selected by this program.

`reference_squared_sum` is the integer `sum(T_i**2)`. `error_scale=16384`
means a table entry divided by 16384 is an unscaled squared-error sum, not a
conditional mean. Counts are already represented in these sums; do not multiply
by frequencies again. For a chosen output code `g[x]` per state:

```text
S = sum(error_table[x][g[x]] for x in states)
MSE = S / error_scale / sample_count
EVM_dB = 10*log10(S / reference_squared_sum)
```

Use `evaluate_truth_table(report, matrix, output_codes)` to compute these metrics
without resimulation. Zero error (negative infinite dB) or zero reference
energy (undefined ratio) returns dB=null; inspect the numerator/denominator.

The downstream SMT constraint for target `tau` is
`S <= reference_squared_sum * 10**(tau/10)`. Convert that budget to an integer
with sufficiently precise arithmetic before solving. The table generator
does not accept `target_evm_db` or optimize gate cost; SMT should jointly choose
the truth table and its Boolean implementation under the total error budget.

With `--output result.npy`, the integer matrix is saved as a plain int64 NumPy
array (no pickle). `result.json` stores the accompanying metadata without
duplicating the matrix: reference energy, input/output encoding, sampling,
counts, scale, matrix filename, shape and dtype. Both files describe one run.
`--output` is required. The matrix is only saved in NPY, never embedded in JSON.
The Python API `generate_error_table(...)` returns `(metadata, matrix)`.

```python
import json
from pathlib import Path
import numpy as np

path = Path("result.npy")
report = json.loads(path.with_suffix(".json").read_text())
matrix = np.load(path, allow_pickle=False)
# evaluate_truth_table(report, matrix, output_codes)
```

## Error-constrained SMT synthesis

`synthesize.py` constructs a shared multi-output Boolean DAG using Z3
(`z3-solver` is required). It uses topological source selection as in the exact
truth-table synthesis tool, but the output truth table is a decision variable:

```
sum(error_table[x, G(x)] for x in states) <= integer_error_budget
```

The dB target is converted to a conservative integer budget using 80-digit
Decimal arithmetic and flooring. All table coefficients and solver constraints
are integers. The generated DAG is independently simulated on all X states,
and its error is checked against the table before returning SAT.

```bash
PYTHONPATH=/home/guoli/open_question_solver/tools/circuit_kit \
python -m circuit.multiplier.conditional_compensation.synthesize \
  /home/guoli/open_question_solver/tools/circuit_kit/circuit/multiplier/conditional_compensation/example_synthesis_config.json \
  --output /home/guoli/open_question_solver/tools/circuit_kit/circuit/multiplier/conditional_compensation/example_synthesis_result.json
```

Configuration paths are relative to the configuration file. The NPY's matching
JSON supplies X, compensation columns, removal slots and reference energy.
The implementation must be the same candidate used to generate that table.
Its baseline and deleted circuits are rebuilt to measure the saved gate cost.
There is no user-supplied savings value in the CLI.

The synthesis configuration must explicitly repeat the matrix interpretation:

```json
{
  "error_table": "example_error_table_result.npy",
  "node_ids": [2, 3],
  "compensation_columns": [4, 5, 6],
  "target_evm_db": -54.0
}
```

The tool cross-checks these two lists against the error-table metadata and
rejects mismatches. This makes the row/column encoding visible in the SMT
instance instead of relying on an implicit sidecar lookup.

### Choosing `target_evm_db`

`target_evm_db` is an **absolute final EVM target**, not merely a target for
the compensation network. Compare it with the original candidate's measured
`baseline.evm_db` from `node_set_information.py`. The final exported candidate
should normally lose no more than **0.2 dB per optimization step**:

```text
target_evm_db <= baseline.evm_db + 0.2
```

Remember that more-negative dB is better. For example, if the original
candidate is `-57.6 dB`, use a target no weaker than approximately `-57.4 dB`
for a single step. A target such as `-54 dB` would permit a much larger
regression and is unsuitable when preserving the parent's quality is required.
Use the authoritative full-circuit evaluator after export; the table synthesis
target is only a pre-integration constraint under its exact-addition model.
If several optimizations are chained, apply the 0.2 dB budget to each accepted
step and compare every new candidate with its immediate parent.

- Physical gate count cannot exceed the measured saving. Optional `max_gates`
  can lower this cap but cannot raise it.
- Weighted cost also cannot exceed the saving: AND=1, OR=1, XOR=3, NOT=0.
- All costs from 0 through the saving are checked in ascending order. A SAT
  result is minimum weighted cost **within the physical gate cap**. Inputs and
  constants can directly feed outputs; zero-gate solutions are allowed.
- NOT is free in weighted cost but counts toward the physical gate cap.
- Internal WIRE slots permit smaller DAGs and are removed from the emitted
  netlist. Only AND/OR/XOR/NOT are emitted as actual gates.
- `timeout_ms` is per solver check (default 60000), not a total search timeout.
  On UNKNOWN/timeout the search stops rather than falsely claiming optimality.

The SAT result contains `circuit`, `output_codes`, `weighted_cost`, `gates`,
and the recomputed table-based EVM. `instantiate_compensation(candidate,
node_ids, result['circuit'])` emits this G network into an initialized candidate
and returns its output node IDs in compensation-column order.

This synthesizes G, not the final compensated multiplier. The error table
assumes exact weighted addition to the deleted raw output (with 19-bit wrap).
Integrating G must preserve that arithmetic. Extra addition/compression costs
are not included in G's budget; final total reachable cost and EVM must be
validated after integration. A G costing the full saving has no remaining
budget for additional logic and may give no net improvement.

Timeouts, unknown results and interruptions during synthesis are archived in
`hard_instances/<timestamp>/`: the exact NPY, metadata, input configuration,
result/search bound and, when available, `problem.smt2`. The SMT-LIB file can
be replayed independently of candidate files. A build-phase interruption may
have no SMT file; use the saved table and `saved_cost` in the Python API to
reconstruct it. Ordinary UNSAT results are not archived as hard instances.

## Exporting a complete candidate

After a SAT result, `export_candidate.py` reads the source implementation, error
table and synthesis result, verifies the G truth table against the error budget,
and creates a new standalone candidate module. See `example_export_config.json`.

```bash
PYTHONPATH=/home/guoli/open_question_solver/tools/circuit_kit \
python -m circuit.multiplier.conditional_compensation.export_candidate \
  /home/guoli/open_question_solver/tools/circuit_kit/circuit/multiplier/conditional_compensation/example_export_config.json \
  --output /home/guoli/open_question_solver/tools/circuit_kit/circuit/multiplier/conditional_compensation/candidate_compensated.py
```

Output must be a new `.py` in this package directory, so relative imports keep
working after moving the circuit package. Existing files are never overwritten.
The generator leaves the source candidate untouched. The emitted module contains
the full reachable frozen DAG, a concrete `Candidate(MultiplierCircuit)` and
`build_circuit()`; it does not load the synthesis JSON or source candidate at
runtime. It needs only the circuit package, not Z3 or the experiment files.

The complete network adds G **after the deleted raw output**, before external
quantization, using exact arithmetic with 19-bit wrap. It does not inject G
into the candidate's approximate compressors, which would change the model.
The companion JSON reports baseline, deleted and final reachable costs, net
savings, and table-derived performance. A non-improving candidate is exported
but marked `strict_cost_improvement=false`; it is not presented as a successful
cost optimization. Final EVM should still be checked with the evaluator.

This frozen export preserves the three-stage interface but its column hook
returns final result bits, not original pre-CSA partial products. Use the source
candidate, not the frozen export, for further partial-product deletion searches.
