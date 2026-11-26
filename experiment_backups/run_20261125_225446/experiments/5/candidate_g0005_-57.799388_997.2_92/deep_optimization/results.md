# Deep optimization results

All metrics below were measured with workspace `gate_cost.py` and full workspace `eval.py --stimulus-file /home/guoliang/multiplier/stimulus.npy` (1,050,624 samples). Costs are weighted, not gate counts.

| Circuit | Gate cost | EVM (dB) | Precompression slots |
|---|---:|---:|---:|
| Original parent (immutable `../parent.py`) | 1003.8 | -57.89064080628819 | 92 |
| Handoff (immutable `../partial_product_candidate.py`) | 1000.8 | -57.79938828565325 | 92 |
| General-equivalence baseline (`general_v1.py`) | 998.8 | -57.79938828565325 | 92 |
| Directional winner (delivered candidate, `direction_top.py`) | 997.2 | -57.79938828565325 | 92 |

The final circuit is a Pareto tradeoff against the parent: 6.6 weighted units less costly, unchanged slots, EVM worse by 0.09125252 dB, but still strictly below -57.6 dB. Versus the handoff it saves 3.6 units without changing raw outputs. No formal proof is claimed: packed simulation found **zero raw-output mismatches across all 1,050,624 configured stimulus rows** between handoff and general baseline, general baseline and directional winner, and handoff and delivered candidate. These checks go beyond rounded output/EVM equality but are empirical.

## Ordered general pass

Inspected the product digit generation, low-column cuts, signed guard/correction bits, G(X), four constant compensation slots, reference 3:2 compression order, and the custom carry/output path. Removed the two explicit `OR(signal,ZERO)` identity buffers from columns 4 and 5 without altering their weighted slot order or count. Consolidated the nested handoff mutations into one readable, index-stable `_product_columns` while retaining the same deletion and compensation positions. Tried a direct Boolean G XOR factorization; it yields the same whole-circuit cost as the original G MUX_XOR due to reachability/sharing. The saved baseline is 998.8, a 2.0 saving over the handoff, and passed full evaluator and raw comparison **before** directional trials began. Reference compression is delegated to tap2. The specialized output stage retains the original low-bit carry and sign-extension behavior.

## Directional pass

Inspected the installed tap2 MUX_XOR truth table, port order `(a,b,c,d,e)`, Boolean function `e ^ ((a&b)|(c&d))`, and cost 4.8. At the non-top Booth row's saturated highest cell the inherited `get_xor(9)==get_xor(8)` allows `(one|two)&(sign XOR bit[8])` to be expressed exactly as `MUX_XOR(one,bit[8],two,bit[8],cell_neg)` because `cell_neg = sign&(one|two)` in each such row. This eliminates eight reachable XORs, eight ANDs and eight ORs while adding eight MUX_XORs across both products: 1.6 weighted-unit savings. Checked full EVM and sample raw outputs. Alternative G mappings, product P factorizations and polarity choice showed no measured improvement; a cheaper sign-guard removal trial was rejected after 539,892 raw mismatches, as sign correction cannot be dropped. No truth-table synthesis or proof-plugin result was used; no don't-care assumptions were needed. Slot count remains honest at 92 throughout.

The delivered single-file candidate imports only the shared tap2 module, exposes parameterless `build_circuit`, and passes both evaluator checks. Parent and handoff snapshots remain untouched.
