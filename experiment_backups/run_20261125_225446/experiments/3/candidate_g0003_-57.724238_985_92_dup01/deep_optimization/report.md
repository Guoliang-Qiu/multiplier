# Deep optimization record

All gate costs are complete output-reachable weighted costs, and slot counts include pre-compression constants. All EVMs come from the full workspace `eval.py --stimulus-file /home/guoliang/multiplier/stimulus.npy` (1,050,624 samples). Strict eligibility: EVM < -57.6 dB.

| Circuit | Cost | EVM dB | Slots | Status |
|---|---:|---:|---:|---|
| Immutable original parent | 983 | -57.66509477604998 | 92 | eligible |
| Immutable handoff | 983 | -57.66509477604998 | 92 | eligible; identical parent |
| General-equivalence baseline | 983 | -57.66509477604998 | 92 | same graph and raw outputs as handoff |
| Final directional correction XOR | 985 | -57.72423799932994 | 92 | eligible Pareto tradeoff versus parent |
| G input OR | 982 | -57.61401726269534 | 92 | fails strict limit |
| G omitted | 973 | -55.495614023439856 | 91 | fails |
| Column-5 term omitted | 975 | -55.24761455029859 | 91 | fails |
| Column-6 term omitted | 970 | -54.9691643084305 | 91 | fails |
| G XOR through MUX_XOR | 985.8 | -57.72423799932994 | 92 | dominated by ordinary-gate XOR |

## General equivalence optimization (performed first)

Reviewed true product columns and compensation, custom majority compression and `_add3`, and final ripple-carry/output truncation against installed tap2. Full-stimulus raw-equivalence comparisons: replacing sign-row XNOR active-gating with direct positive/negative selector terms retains raw outputs but increases cost to 1011; shared sign-selector XOR increases cost to 989; global SOP XOR increases cost to 993; native XOR increases cost to 993. Alternative equivalent De Morgan and XNOR constructions cost 983. No cheaper equivalent circuit found; therefore saved unmodified handoff as `general_baseline.py` with separately measured cost and EVM and full-stimulus raw-output equality (zero mismatches, identical graph). These checks are sample-based, not formal proofs. No truth_table_exact_synth was called, since local simplifications and the existing highly shared cones produced no suitable promising isolated small cone requiring SAT synthesis.

## Directional optimization (performed after baseline)

Evaluated independent low-weight product-slot omissions, explicit compensation, compressor majority at column 5, final-adder low-bit OR threshold, cross-layer correction sharing from columns 4/5, and sign-/neighbor-bit corrections using complete gate-cost and full-stimulus EVM. Most failed the strict threshold; experiment trial source and associated metric JSON files remain here. Stimulus error analysis found mean signed raw delta -29.3657321744, with especially negative residual (-35.3438453674) when d's low bits equal 01. Replacing the handoff G correction OR with XOR of `d[1]` and `(d[0] & c[4])` recovers accuracy at +2 weighted cost, same 92 honest slots. Native XOR cell, SOP, mixed, and MUX_XOR implementations were compared; the current inherited gate realization cost 985 versus MUX_XOR 985.8. This result is nondominated relative to parent (higher cost and more-negative EVM), but the archive's cost-954.2/EVM--57.72353/slots-92 candidate dominates the final candidate; directional stage nonetheless requires improvement or Pareto tradeoff relative to *original parent*.

No evaluator scripts, immutable snapshots or other delivery candidates were changed. Final target import and zero-argument construction and cost/EVM are checked after delivery.
