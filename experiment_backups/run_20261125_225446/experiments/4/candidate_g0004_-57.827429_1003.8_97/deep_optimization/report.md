# Deep optimization report

All reported EVM measurements used `eval.py --stimulus-file /home/guoliang/multiplier/stimulus.npy` (1,050,624 cases); costs and true pre-compression column slots used `gate_cost.py`. The assigned candidate is a parameterless, validated `build_circuit()` with fixed four-input leaves.

| circuit | weighted cost | EVM dB | precompression slots |
|---|---:|---:|---:|
| Original parent, immutable `../parent.py` | 1023.8 | -58.18330682718984 | 100 |
| Handoff, immutable `../partial_product_candidate.py` | 1009.8 | -57.82742896557088 | 99 |
| First-stage general-equivalence baseline, `general_equivalent.py` | 1003.8 | -57.82742896557088 | 99 |
| Final directional variant, `directional_best.py` / assigned delivery | 1003.8 | -57.82742896557088 | 97 |

## General equivalence stage

Inspected Booth-row partial products and hardcoded compensation signals, the special column-3 compressor, full adders, and final ripple/output bits. Handoff's G corrections were hardcoded to nodes 143 and 216: instead retain their genuine original column-4 partial-product nodes before deletion, and reuse those source IDs for the low-column corrections. Removing two OR-with-ZERO buffer gates saves 2 cost; specializing the Booth row-zero negative polarity for step zero saves 4 more cost. Full-stimulus raw-output comparison between handoff and general baseline found **zero** mismatches (sample-based, not a formal proof). Full EVM stayed unchanged. `fa_mixed`, `special_xor`, output absorption and other local tests failed to save further cost; `xor_native`, `xor_alt` and the suggested terminal-row factoring with hardcoded IDs changed the output. Structural binding made alternative global XOR implementations equivalent on a subsample, but they added 12 weighted cost. A MUX_XOR replacement of the low Booth a-expression added 9 weighted cost.

## Directional stage

Explicitly removed the disconnected column-18 ONE compensation slot, and one redundant column-2 ZERO slot. Both changes preserve the output on **all** external stimuli (zero raw mismatches against the general baseline); they lower the truthful reported slot count by two without changing reachable cost or EVM. The final candidate offers a parent-relative tradeoff: cost improves by 20.0 and slots by 3, while EVM worsens by 0.35587786161896 dB but remains under the strict -57.6 dB threshold. It is **not** globally nondominated in the archive: archive entry (980.2, -58.026732013627964, 94) dominates it. Archive entry (986.2, -57.90019115841574, 93) also dominates it.

Measured additional low-bit deletions in columns 4/5/6 reduced cost by 9.8–14.8 but yielded EVM -54.8 to -55.44 dB; rejected. Adding compensation at columns 6–9 or removing meaningful high-column compensation was far outside the EVM limit. Replacing column-3's special compressor with an ordinary _add3 raised cost from 1003.8 to 1021.8 and slightly altered EVM. Replacing output low-column OR with XOR made no measured difference. A duplicate column-3 ONE changed EVM slightly and increased cost. No cheaper feasible directional approximation was retained. No truth_table_exact_synth invocation was configured through the available local APIs; no synthesis result was assumed.

The source retains actual joint weighted partial-product columns, custom low-column reduction, and output assembly. All gate cost comes from the shared library and MUX_XOR remains present. Full-stimulus raw equivalence checks do not constitute formal equivalence proofs.
