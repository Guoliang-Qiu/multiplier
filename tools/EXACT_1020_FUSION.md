# 1020 exact-cell and AB/CD normalization experiment

Baseline: `initial_solutions/candidate_dist_recoded1020.py`.
Reproduce: `python tools/explore_1020_fusion.py`.
The original candidate was not modified.

| Exact adder alternative selection | Joint column normalization | Cost | Raw mismatches |
|---|---|---:|---:|
| no | no | 1020 | 0 / 22945 |
| yes | no | 1020 | 0 / 22945 |
| no | yes | 1020 | 0 / 22945 |
| yes | yes | 1020 | 0 / 22945 |

Inputs: 16384 independent uniform signed-9-bit quadruples (seed 102010),
plus all 6561 combinations of {-256,-255,-128,-1,0,1,127,254,255}.

At each of 73 ordinary full adders, test all six operand permutations of
three explicit parity/majority structures: the existing shared 7-gate cell,
its complemented-input/output dual, and an explicit shared propagate/generate
implementation. Speculative nodes/caches are rolled back between alternatives.
No alternative reduced incremental reachable weighted cost; all selected the
original cell. This is a local cost search, not a global optimality proof.

Normalize the shared AB/CD raw columns using ZERO removal, x+~x=1, and
x+x=2*x, propagating carries to the next column modulo the output width.
This did not reduce total cost. Because the baseline has approximate downstream
logic, arithmetic equivalence of the column sum alone is insufficient to
prove raw-output equivalence; the table reports simulation evidence, not SAT.

No full EVM rerun was needed: no lower-cost candidate was found and the
baseline is unchanged. Its previously measured full EVM is
-58.06279335814503 dB. No ABC/Yosys or external synthesis was used.
