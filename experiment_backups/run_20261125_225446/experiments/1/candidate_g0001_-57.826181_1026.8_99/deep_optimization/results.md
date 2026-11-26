# Deep optimization results

All evaluations used `gate_cost.py` and `eval.py --stimulus-file /home/guoliang/multiplier/stimulus.npy` (1,050,624 samples). Triples are [weighted cost, EVM dB, pre-compression slots].

| Circuit | Cost | EVM | Slots |
|---|---:|---:|---:|
| Immutable original parent | 1067.2 | -58.3495562015 | 101 |
| Immutable handoff | 1052.2 | -57.8261811914 | 100 |
| General-equivalence baseline (`equivalent_baseline.py`) | 1026.8 | -57.8261811914 | 100 |
| Final (`remove_comp18.py`) | 1026.8 | -57.8261811914 | 99 |

## General equivalence pass

Inspected partial-product Booth generation, compensation insertion, specialized column-3 compression, and final adder/output sign replication against the tap2 implementations. Preserved custom compression and output logic because the library reference is not equivalent. Replaced additional Booth-cell AND/OR/XOR networks at steps 0 and 3 with shared MUX_XOR cells (the 5-port library cell is 4.8), factored the shared `cell_neg` Booth-row enable into its correction bit, removed the dead conditional around the identical column-2 constant assignment, and replaced `OR(b[0], ZERO)` with `b[0]`. The latter removes one reachable OR. The initial additional step-3 muxes alone reduced cost from 1052.2 to 1049.8; sharing the correction enable reduced this to 1042.8; step-0 muxes reached 1026.8. Equivalence was checked on **all 1,050,624 raw outputs**, with zero mismatches against the handoff. This is empirical sample equivalence, not a formal proof. Full evaluator metrics are identical. The output's deliberate bit-17-to-bit-18 sign replication means bit-18 compensation cannot affect output, whereas other compensation columns cannot be dropped without enormous error. No exact SAT synthesis was invoked: the available direct Booth identities and sharing yielded useful cheaper cells, without a small isolated cone whose new truth-table synthesis would outperform the already shared multi-output structure.

## Directional pass

Measured the real pre-compression slots on 105,063 uniformly subsampled rows **from the configured external stimulus**: column 3 slots had P(1)=0.37380, 0.25104, 0.37587, 0.24946; column 4 surviving generated slots were 0.40806, 0.34318, 0.40551, 0.34342, with the existing `b[0]` compensation at 0.49902. Thus slot imbalance alone is inadequate: columns have distinct weights and their removal changes the carry network and signed error. Actual complete-circuit trials: inserting ONE at column 4 yielded [1032.8,-57.43070,101], column 5 [1029.8,-56.01464,101], column 6 [1026.8,-52.58793,101]; inserting `b[0]` at column 5 [1033.8,-56.47666,101], `d[0]` [1033.8,-56.79743,101]; removing column-3 slot 1 [1019.8,-54.59913,99]; replacing columns-4 slot 0/1/2 by ZERO cost 1016.8/1019.8/1016.8 but EVM -57.44475/-57.48687/-57.43544, all above the strict -57.6 threshold. Column 5/6 deletions also failed it. Dropping constants at columns 10,11,13,15 catastrophically raised error; dropping column-18 constant preserved all observed raw outputs, saved one slot, and did not change weighted cost. This is an **exact output-cone dead-code elimination** justified by replicated output bit 17, not a workload-dependent approximation. Final candidate is strictly better than the equivalently optimized baseline in third objective, though no workload-dependent approximation met the threshold. The original parent retains a more accurate nondominated trade-off; the final candidate offers lower cost and slots with eligible EVM.

The distinct construction stages and original pre-compression column semantics are retained. All trials and scripts are contained in this directory; immutable snapshots were not modified.
