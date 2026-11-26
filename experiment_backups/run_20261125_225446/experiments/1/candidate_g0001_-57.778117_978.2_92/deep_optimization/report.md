# Deep gate optimization record

External stimulus: `/home/guoliang/multiplier/stimulus.npy` (1,050,624 four-input cases). All rows use workspace `gate_cost.py` and complete `eval.py`; raw-output equality tests use the same full stimulus and are empirical, not formal proofs.

| Circuit | Cost | EVM dB | Precompression slots |
|---|---:|---:|---:|
| Original immutable parent | 986.2 | -57.9001911584 | 93 |
| Immutable handoff | 983.2 | -57.7781172796 | 93 |
| First equivalent cleaned baseline | 979.2 | -57.7781172796 | 92 |
| Final equivalent baseline (`general_baseline.py`) | **978.2** | **-57.7781172796** | **92** |

## General equivalence pass (completed before directional experiments)

* Inspected partial-product Booth generation, fixed correction layout, row sign-term sharing, low-column compression and ripple output. Collapsed the two historical compensation wrappers, eliminated a raw `OR(ZERO,ZERO)` buffer and a dead hard-coded node-538 reference, and retained the literal zero slot (removing it altered output because the compressor deliberately discards a low-column sum). Counted the literal slot, not just live gates. Removed column-18 constant compensation: final output bit 18 is copied from bit 17. Inserting the remaining zero at the start of column 4 saves one gate through a different compression ordering, without changing outputs on the full stimulus.
* Raw output of final baseline matches immutable handoff on all **1,050,624** samples, with weighted cost -5 and slot count -1. Valid final EVM < -57.6 dB. In particular, output semantics and carry treatment of the approximate low-bit compressor were retained.
* Tried native XOR (991.2), a two-minterm XOR (991.2), complementary-XNOR XOR (979.2 before zero scheduling), disabling absorption (979.2), no sign-row rewrite (1007.2), and several exact full-adder realizations (979.2, 1046.2, 1046.2). Existing 24 MUX_XOR cells retained, because their complete weighted cost is preferable to the tested alternatives. Reference compressor/output stages cannot replace the intentionally approximate majority suppression and truncated output assembly. A raw equality run confirmed the XNOR XOR trial but offered no cost improvement.
* Removing the apparently redundant zero slot cost 977.2 but **failed** raw equality at sample 4100 and yielded EVM -54.6506 dB. This is why it was not accepted as an equivalent rewrite. No exact-synth tool API is installed in this session; no SAT result was claimed.

## Distribution-guided pass (after saving equivalent baseline)

Measured the *actual* precompression slot signals in `slot_bias.tsv`, with `slot_bias.py` on the configured workload. Column-4 slots 0 and 1 are one with probability 0.406981 and 0.407036; slot 3 is one with probability 0.375846. Column-5 slots are near 0.375, column-9 sign slot 4 is near 0.249537, and column-16 two slots are near 0.75. Constant slots are listed explicitly. Simple low-column deletion might seem attractive, but the two 0.407 slots feed distinct logic and a constant-aware compressor, so weight, carry effects and whole-cone reachability dominated probability alone.

Implemented zero/one replacements of biased slots, pairs of opposite constants, selective rounding and cheap input-bit conditional observations. Tested complete gate cost and full evaluation for promising variants. For example, replacing column-4 slot 0 by ZERO on the final equivalent baseline cost 962.2, slots 92, EVM -57.413373; replacing it by ONE cost 968.2, slots 92, EVM -57.384087; replacing it by `c[4] & d[0]` cost 970.2, slots 92, EVM -57.451950. Paired ZERO/ONE column-4 replacements cost 956.2 but EVM -57.309937. All violate the strict -57.6 dB runtime bound. The correction column 10 removal gave -29.57096 dB; adding a column-4 ONE gave -57.23947 dB. A lower-cost approximate circuit is thus **not** a valid improvement. Preserve equivalent baseline as the final eligible Pareto trade-off versus parent: 8.0 less weighted gate cost and one fewer partial-product slot, with EVM 0.121926 dB worse, still below -57.6 dB.
