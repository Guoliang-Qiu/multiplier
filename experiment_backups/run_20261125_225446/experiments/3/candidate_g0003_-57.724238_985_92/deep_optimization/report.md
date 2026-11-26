# Deep gate-level optimization report

Stimulus: `/home/guoliang/multiplier/stimulus.npy` (1,050,624 cases). All costs are weighted output-reachable gate costs from workspace `gate_cost.py`, and EVM comes from workspace `eval.py --stimulus-file ...`.

| Implementation | Gate cost | EVM (dB) | Pre-compression slots |
|---|---:|---:|---:|
| Original parent (immutable) | 983 | -57.66509477604998 | 92 |
| Handoff (immutable) | 986 | -57.72423799932994 | 92 |
| General-equivalence baseline (`general_baseline.py`) | 985 | -57.72423799932994 | 92 |
| Final, same as general baseline | 985 | -57.72423799932994 | 92 |

## Ordered general pass

Inspected the input/partial-product generation, radix-four sign correction, shifted/deleted column-four entries, G compensation, carry-save compression, and final seven-bit low-column treatment. Removed the handoff's two historical intermediate column-mutation wrappers and obsolete correction logic. Named G's inputs `d[1]`, `c[4]`, and `d[0]` instead of depending on node IDs 30, 24, and 29. In this exact graph the handoff's `add('OR', G, ZERO)` was an output-reachable redundant buffer, removed in the baseline; it saves one weighted cost. The compressor's special branches refer solely to empty columns 0–3, so delegated to tap2's identical reference compressor. The final output stage remains specialized to preserve the original low-column OR treatment and output-bit arrangement. Baseline raw output differed from the handoff at **zero** of 1,050,624 configured samples; this is empirical evidence, not formal proof.

Additional measured complete-circuit general trials: native XOR cost 995, SOP XOR cost 995, removing sign factoring cost 1013, alternate correction cost 985, compressor reverse cost 985, sorted compressor variants 986–988, inherited absorption variants 985, inherited half-adder output variant 985. No one of these lowered the baseline's cost. The comparison used the complete circuit, rather than treating cheaper-looking isolated expressions as savings. General baseline was evaluated by the full workspace evaluator before directional trials.

## Directional MUX_XOR pass

Inspected tap2 truth table, cost 4.8, and port order `(a,b,c,d,e)` corresponding to `e ^ ((a&b)|(c&d))`. Tried mapping G directly as `MUX_XOR(c[4],d[0],ZERO,ZERO,d[1])`: cost 985.8, zero raw-output differences from handoff; full evaluator EVM -57.72423799932994. A generic XOR-of-two-product-OR mapping cost 987.8, zero differences. Also fused XOR-of-AND expressions: cost 1002.6, zero differences. The mapped G saves no complete-circuit cost because the existing shared AND and XOR representation is cheaper in the full graph. Retained the 985-cost general baseline. The raw comparison is sample-based, not a formal equivalence proof. No exact synthesizer was invoked because the actual shared XOR/AND structure already provided the cheap local correction and mapped variants were costlier.

Final is a Pareto tradeoff against the parent: EVM improves by 0.05914322327996 dB for two more weighted gates, at identical 92 slots; EVM is strictly below -57.6 dB. It also strictly improves the handoff cost by 1 without changing the measured raw results.
