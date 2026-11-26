# Deep optimization report

All metrics use `gate_cost.py` and full `eval.py --stimulus-file /home/guoliang/multiplier/stimulus.npy` (1,050,624 rows). Raw-output equality is sample-based, not a formal proof.

| Circuit | Weighted cost | EVM dB | Precompression slots |
|---|---:|---:|---:|
| Original parent | 954.2 | -57.72353155447783 | 92 |
| Immutable handoff | 954.2 | -57.72353155447783 | 92 |
| Saved general-equivalence baseline `general_baseline.py` | 954.2 | -57.72353155447783 | 92 |
| Final delivered circuit | 954.2 | -57.72353155447783 | 91 |

General pass: inspected all three stages and the installed library. Explored replacing custom factored adders by inherited `_add3` (cost 955.2), replacing custom XOR by inherited XOR (1091.2), both (965.2), alternative carry factoring (1017.2), compressor input permutations (954.2), two other exact XOR realizations (954.2 and 1091.2), MUX_XOR full-adder sums (1070.4–1133.4), original signed top-row expression (982.2), direct constant-folded G5/G6 boundary slots (954.2), top-row factor variants, and post-build XOR absorption (954.2). None yielded a cheaper equivalent circuit. Preserved the handoff as general-pass baseline and checked equal raw outputs across all configured stimulus rows. No exact synthesis Cordis API was exposed; no external plugin invocation was made.

Directional pass: deleting the column-18 ONE compensation has no effect because output assembly sets output bit 18 equal to bit 17; it reduces honest slot count from 92 to 91 without changing reachable gate cost. Raw sample outputs equal parent; EVM and all error metrics equal parent. Removing the zero G6 slot cost 953.2 but failed EVM (-55.48538), owing to changed approximate compressor dispatch and rounding-boundary errors. Removing the G5 compensation cost 937.4 but failed EVM (-56.54663). Removing column-10 compensation cost 951.2 and failed EVM (-29.57342), reflecting large systematic offset. Extra low-column compensation ONE at column 5 cost 954.2 but failed EVM (-55.71983); the raw bias improved while quantized RMSE worsened. Column 7 ONE failed (-47.32565). Extending Booth MUX_XOR step 3 cost 977.8. Column-cut trials at weight 5 were not valid with the current weight-4 replacement and were discarded, not evaluated as candidates. The 91-slot final is a Pareto improvement over the 92-slot parent at identical cost and EVM and satisfies EVM < -57.6. No snapshots or evaluator scripts changed.
