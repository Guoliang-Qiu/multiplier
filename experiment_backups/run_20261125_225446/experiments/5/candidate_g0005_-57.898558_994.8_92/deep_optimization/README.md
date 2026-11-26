# Deep optimization, candidate g0005_0008

All measurements use the workspace `gate_cost.py` and full `eval.py --stimulus-file /home/guoliang/multiplier/stimulus.npy`; 1,050,624 external samples. Slots count every pre-compression entry.

| Circuit | Weighted cost | EVM dB | Slots |
|---|---:|---:|---:|
| Immutable parent | 1010.6 | -58.18330682718984 | 93 |
| Immutable handoff / initial delivery | 995.8 | -57.898557989441954 | 92 |
| General equivalence baseline (`general_baseline.py`) | 994.8 | -57.898557989441954 | 92 |
| Directional delete column-5 slot 2 | 985.8 | -55.28800562571141 | 91 |
| Directional delete compensation ONE column 4 | 993.8 | -55.206528749664244 | 91 |
| Directional add rounding ONE column 6 | 994.8 | -52.003376981872414 | 93 |

General pass: inspected all construction stages, tap2's cached gates, exact `_add3`, compressors, and final carry logic. Identified a direct un-cached OR with ZERO inserted as column-5 slot; its node-number `65` is the first product's existing step-zero Booth bit-4 MUX_XOR. Replaced it with the explicit corresponding input expression (b[0]&a[4] | (b[1]&~b[0])&a[3]) XOR b[1] through tap2's cached `_mux_xor`, removing one output-reachable OR, preserving 92 slots. An initial bus-misidentification trial using d instead of b failed raw comparison at stimulus case 9 and was corrected before baseline acceptance. Reference compression remains delegated. FIFO compressor placement and a Boolean-equivalent sign guard were tested (`compress_fifo.py`, `guard_shared.py`): both retained cost 994.8 and raw-output agreement on the full stimulus, so they were not selected. Other potential G and output rewrites were not substituted without a measured improvement. All reported raw-equivalence checks are empirical on the configured workload, **not formal proofs**; the single-cell identity of the selected rewrite follows directly from its MUX_XOR operands and unchanged preceding allocation. The corrected baseline passed raw 19-bit output equality for all 1,050,624 samples. Its full eval reproduced the handoff EVM.

Directional pass: profile from external stimulus: ~13.63% of exact raw residues lie in [56,72] mod 128, ~50.40% have opposite-sign products, ~9.78% have an input with absolute value at least 250. Explicit partial-product deletion, compensation deletion, and selective rounding were independently built and fully evaluated. All failed the strict EVM < -57.6 dB requirement; retain general baseline. Existing joint product columns and cached MUX_XOR sharing remain intact. Archive objectives were inspected; baseline is a valid tradeoff against its immutable parent (cost -15.8, slots -1, but EVM +0.2847488 dB), not a claim of global archive dominance. No specialized exact synthesizer was available through the present tools; no SAT results or formal equivalence are asserted.
