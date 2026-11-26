# Deep gate optimization record

All reported EVM evaluations used `eval.py --stimulus-file /home/guoliang/multiplier/stimulus.npy` (1,050,624 samples); costs and partial-product counts used workspace `gate_cost.py`. The library has `MUX_XOR(a,b,c,d,e) = e ^ ((a & b) | (c & d))`, cost 4.8; AND/OR cost 1, XOR 3, NOT 0. The configured specialized exact-synthesis tool was not available in the active tool interface, so no SAT result or formal equivalence is claimed.

| Circuit | Weighted cost | EVM dB | Precompression slots |
|---|---:|---:|---:|
| Original parent snapshot | 1037 | -58.18330682718984 | 93 |
| Supplied handoff snapshot | 1025 | -57.768547437293265 | 92 |
| General-equivalence baseline (saved `general_baseline.py`) | 1018 | -57.768547437293265 | 92 |
| Final directional result (retain general baseline) | 1018 | -57.768547437293265 | 92 |

General pass: inspected both Booth partial-product matrices, G compensation and constant slots, reference LIFO compression, approximate low-column final-adder carry, and masked output bits. Removed an explicit OR with constant ZERO on the column-five correction (1 unit), factored G from `(D1&D0)|(D1&~C2)` into `D1&(D0|~C2)` (1 unit), and replaced `~one & (h XOR m)` by `m&low&~h | ~(m|low)&h` for Booth two-digit selection, sharing the AND/OR terms of one-digit selection (6 units). The exact low-bit carry behavior and precompression slot order are preserved. Baseline was evaluated in full and raw-output compared to the handoff across all 1,050,624 configured samples: zero differences. This is empirical, not formal proof.

Further general trials: substituting primitive XOR for signed multiplicand XOR reduced AND/OR but increased XOR cost, yielding equal overall cost (1024 before the two-digit change); implementing one-digit with primitive XOR raised total cost to 1030; a signed-row multiplexer syntax-only rewrite did not change the graph/cost. Reference `_fa`, `_ha`, `_add3`, and the reference compression implementation were reused; no copied gate primitives or cost overrides.

Directional pass (after baseline): G mapped to MUX_XOR with `e = D0&C3` and either `(D1&D0)|(D1&~C2)` or `D1&(D0|~C2)` as its masked OR. The latter introduces no reachable MUX_XOR cell after existing deletion and output pruning; both trial mappings measured unchanged cost 1018, and the first completed full evaluation and raw equivalence comparison (zero differences). Replacing signed-row two-AND/one-OR cells with MUX_XOR using zero `e` gave cost 1099, while replacing `_fa` sum logic with a MUX_XOR expression while retaining carry logic gave cost 1210. Neither is beneficial. The final candidate therefore retains the verified general baseline, with no reachable MUX_XOR cells. Truncation/deletion and compensation layouts were deliberately not searched because this task requires equivalence and preservation of the supplied algorithmic architecture.

The selected candidate has EVM strictly below -57.6 dB and is a Pareto tradeoff against the parent: weighted cost -19, EVM worse by 0.414759389896575 dB, and partial-product slots -1. Against the supplied handoff, it saves 7 weighted units at identical measured EVM and slot count. No rounding of fractional gate cost was used for comparisons.
