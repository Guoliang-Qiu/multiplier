# Deep optimization report

External stimulus: `/home/guoliang/multiplier/stimulus.npy` (1,050,624 rows). Cost and EVM measured with the workspace `gate_cost.py` and full `eval.py` on each baseline. All slot counts are measured immediately before compression by tap2.

| Variant | Weighted cost | EVM dB | Slots | Note |
|---|---:|---:|---:|---|
| Immutable parent | 969.2 | -57.83461265306508 | 93 | Feasible |
| Immutable handoff | 968.2 | -57.614047989826645 | 93 | Feasible |
| General-equivalence baseline | 960.2 | -57.614047989826645 | 93 | Selected: Pareto tradeoff against parent (lower cost, worse EVM) |

## Ordered first pass: equivalent gate-level optimization

Examined partial-product Booth selectors and sign correction, compressor FA/majority and output carry logic. Replaced the raw `add('OR', ONE, ZERO)` in the real column-four compensation insertion by the inherited constant-folded ONE. This removes eight weighted output-reachable gates because even a semantically constant, non-canonical OR node blocks tap2's constant-aware compressor and carries. The column slot remains present, preserving the exact compressor schedule, bitwise outputs and count of 93. Raw-output equality against handoff was checked on **all 1,050,624 configured samples** (zero differing raw outputs); this is a sample-based equivalence check, not a formal proof. Gate cost 960.2 vs 968.2; EVM identical at -57.614047989826645 dB.

Also measured alternatives: sign-digit `pos|neg` changed to XOR: 974.2; remove special shared-selector `_and` override: 974.2; combine these: 980.2; native XOR primitive in place of shared OR/AND realization: 987.2; direct sign-cell construction: 996.2. Native `_gate` absorption had equal cost; compressor local XOR native implementation had equal cost. Each of these was tested for raw bitwise equality against the handoff on all configured samples (zero differences). No finite truth-table synthesis plugin was configured in this session; did not assert SAT proof. Saved frozen general baseline in `general_equivalence_baseline.py` before directional trials.

## Ordered second pass: approximation and weighted-column search

Each independent directional variant was evaluated with full workspace eval and the external stimulus. Eliminating the explicit zero column-four slot decreased cost to 959.2 and slots to 92, but EVM deteriorated to -54.37482468555948 dB. Eliminating the column-four ONE reduced slots to 92 but increased cost to 963.2 and deteriorated EVM to -55.14053732302994 dB. Removing each individual compensation ONE in columns 10, 11, 13 and 15 gave 92 slots and EVM -29.648137237678984, -23.60059564305864, -11.525133585476823 and +0.6816843416744428 dB, respectively. Adding a column-six rounding ONE gave 94 slots and EVM -51.533942555161325 dB. All were rejected under the strict EVM < -57.6 dB requirement. The original handoff's G-selector substitution, low-weight omission, sign-factorization and mixed MUX_XOR realization were preserved rather than repeating its prior deletion/layout search. No directional variant improved the verified equivalence baseline. The baseline and parent are nondominated with respect to each other: cost saving 9.0 for an EVM tradeoff of 0.220564663238435 dB. The archived population contains other points and no archive files were modified.

Final source is the standalone general-equivalence baseline; it implements all three stages, uses the shared kit directly and retains all 93 genuine column slots. No configured library costs or evaluator code changed.
