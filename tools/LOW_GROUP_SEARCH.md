# Low-column group search

Baseline: `initial_solutions/candidate_g0000_0001.py`.
Search: `python tools/search_low_groups.py`.

Screening uses 32768 uniform independent ABCD samples, seed 812. It verifies
that the original circuit raw output equals the signed 19-bit column sum with
its bottom six bits cleared. Each proposed column change is evaluated after
this truncation and the evaluator's floor(raw/128 + 0.5) quantization.
This is a sampled screen, not exhaustive enumeration or authoritative EVM.

Search families:
- Symmetric subsets in columns 4 and 5 replaced by an existing node plus a
  nonnegative integer constant. Candidate support must be contained in the
  replaced subset's structural support.
- Joint symmetric single-entry substitutions in columns 4 and 5.
- One-sided or symmetric substitutions with constant offsets -32,-16,0,16,32.

The latter two families used a sample MSE ratio cutoff of 1.004. No candidate
under gate cost 1000 survived. The subset search used a looser cutoff of 1.025;
one lower-cost candidate survived: replace column-4 nodes 247 and 457 by
their first AND operands, 245 and 455.

## Authoritative validation

Candidate: `initial_solutions/candidate_g0000_0001_col4_probe.py`.
TAP2_COPIES=8, OPENBLAS_NUM_THREADS=1; 1050624 cases.

| Metric | Baseline (previous full run) | Column-4 candidate |
|---|---:|---:|
| Gate cost | 1000 | 996 |
| EVM dB | -57.61590546455796 | -57.5150381058694 |
| Raw MSE | 0.09691321518686083 | 0.08904117467807747 |
| Raw bias (reference minus circuit) | 0.24210652877480432 | 0.2216620119923969 |
| Quantized RMSE | 0.3175736631844264 | 0.3212830740902626 |
| Max absolute quantized error | 1.0 | 1.0 |

Conclusion: saves four weighted gates, but does not meet -57.60 dB. Lower raw
MSE and bias do not guarantee better quantized EVM. The baseline is retained.

Correction to the previous balanced-probe interpretation: replacing two
column-6 negative terms adds mean raw error +16, while removing two column-8
terms subtracts 128, for net -112. This is not bias cancellation. The terms
removed there are B[8]&~B[7] and D[8]&~D[7], not the opposite polarity.
Carry propagation does not invalidate weighted column-sum arithmetic.
