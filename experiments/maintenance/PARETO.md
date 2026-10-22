# Current initial_solutions frontier

All entries below were remeasured with the unchanged evaluator:
`TAP2_COPIES=8 OPENBLAS_NUM_THREADS=1 python eval.py <candidate>`.
Each evaluation uses 1,050,624 cases. Both cost and EVM dB are minimized.

| Candidate | Cost | EVM dB |
|---|---:|---:|
| candidate_dist_smt978_refined.py | 978 | -57.852453944 |
| candidate_dist_smt980.py | 980 | -57.909628250 |
| candidate_dist_top_reuse984.py | 984 | -57.928584136 |
| candidate_dist_recoded1020.py | 1020 | -58.062793358 |
| candidate_dist_recoded1025.py | 1025 | -58.168466039 |
| candidate_g0001_0000.py | 1037 | -58.183306827 |
| candidate_g0001_0005_joint1060.py | 1060 | -58.239899776 |
| candidate_g0001_0001.py | 1064 | -58.264840287 |
| candidate_g0001_0005_joint1072.py | 1072 | -58.349556201 |
| candidate_g0001_0005_col2_joint_asym.py | 1084 | -58.382742434 |
| candidate_g0001_0004.py | 1111 | -58.416063321 |
| candidate_g0001_0005.py | 1114 | -58.423129084 |
| candidate_exact_rounding_optimized.py | 1289 | -58.442285723 |

Removed `candidate_dist_smt978.py` (978, -57.850639203), strictly dominated
by `candidate_dist_smt978_refined.py` at the same cost.

Removed no-op `_gate` overrides and false `_USE_ABSORPTION` flags where
the parent already provides identical behavior; removed unused `step1_one`
and `step1_two` declarations. All simplifications preserved the entire DAG,
input/output IDs and cost. Full before/after evidence and metrics are in
`audit_cleanup.json`.

Retained overrides with real semantic/construction differences: enabled
absorption, shared AND/OR XOR construction, and joint Booth recoding.
`_bit` and `_qsub` are not supplied by the current tap2 base. Approximate
compressor/output stages also differ from the library reference stages.
