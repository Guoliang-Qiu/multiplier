# Deep optimization record

All measurements used `gate_cost.py` and full `eval.py --stimulus-file /home/guoliang/multiplier/stimulus.npy` (1,050,624 cases). Objectives are weighted gate cost, EVM dB, and genuine pre-compression slots.

| Circuit | Cost | EVM (dB) | Slots |
|---|---:|---:|---:|
| Immutable original parent | 1015.6 | -57.94456262108487 | 93 |
| Immutable handoff | 1004.8 | -57.89064080628819 | 92 |
| General-equivalence baseline / selected final | 1003.8 | -57.89064080628819 | 92 |
| Directional extra constant at column 6 | 1003.8 | -51.75924438107124 | 93 |
| Directional deletion at column 4 slot 0 | 994.0 | -54.747785843887655 | 91 |
| Directional extra constant at column 4 | 1013.8 | -57.18392369608225 | 93 |
| Directional exact low carry trial | 1003.8 | -57.89064080628819 | 92 |

General equivalence pass: inspected joint Booth product generation, G compensation and low-column pruning, reference compression and final low-bit output adder. Replaced the handoff's raw node IDs 29 and 30 with explicit `d[0]`, `d[1]`, and removed an uncached `OR(signal, ZERO)` buffer in favor of inherited cached `_or`. Factored the sign selection guard from `(negative & (one|two))` to `(negative & ~(m&low))`, and reused the common sign-correction guard in the previous-row product carry. The guard factoring was checked against the handoff. Cost saving from the previous uncached buffer is exactly 1.0 weighted unit; factoring did not cost more. The full external stimulus showed **zero raw-output bitwise mismatches** against the handoff; this is sample-based evidence, not a formal proof. Full evaluator EVM and all other reported metrics matched exactly. Tried a custom constant-first compressor order, with zero cost improvement and zero sample mismatches; retained the shared library reference compressor instead. Evaluated an exact low-bit output adder realization; its result and cost matched the baseline, so retained the original specialized low-bit logic. No duplicate tap2 primitives were introduced. The small G function is already expressed with one MUX_XOR and the shared inherited gate primitives; exact-synthesis plugin was not available through the exposed tools, so no SAT proof or synthesized alternative is claimed.

Directional pass: tried targeted partial-product removal, compensation at two low weights, and exact low-column output handling. Low-weight deletion and constant compensation failed the strict -57.6 dB requirement. On the configured stimulus the handoff's raw bias was +0.20654528136374192, but the column-4 positive constant still increased quantized RMSE; local raw bias was therefore not a reliable selection criterion. Keep the verified general-equivalence baseline. It saves 11.8 weighted units and one slot relative to the original parent, at a 0.05392181479668 dB worse EVM; thus it is a feasible parent trade-off rather than an across-objectives dominance claim. The archive's 971.2/-57.83461265306508/92 entry is cheaper but less accurate, and its 980.2/-58.026732013627964/94 entry is more accurate but has more slots. Other archive entries also offer different accuracy/cost compromises, so no unverified archive dominance assertion is made.

The final candidate is standalone and uses the imported shared tap2 implementation, a static three-stage DAG, fixed four buses, a 19-bit output, and the inherited reference compressor. No snapshots, evaluator code, or other delivery candidates were changed.
