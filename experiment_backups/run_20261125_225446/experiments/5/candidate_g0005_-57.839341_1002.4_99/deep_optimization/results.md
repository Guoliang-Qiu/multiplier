# Deep optimization results

Prescribed stimulus: `/home/guoliang/multiplier/stimulus.npy`, 1,050,624 cases. All EVM measurements used the workspace `eval.py`, and all gate costs used `gate_cost.py` (MUX_XOR 4.8).

| Circuit | Weighted cost | EVM dB | Pre-compression slots |
|---|---:|---:|---:|
| immutable parent | 1023.8 | -58.18330682718984 | 100 |
| immutable handoff | 1013.0 | -57.83934118866828 | 99 |
| general-equivalence baseline (`general.py`) | 1012.0 | -57.83934118866828 | 99 |
| final directional (`directional.py`) | 1002.4 | -57.83934118866828 | 99 |

## Ordered general pass

Inspected all product-row branches, the correction constants and deleted slots, compressor stages, custom low-column adder, and output sign/zero layout. Preserved the nonstandard column-three compressor and output OR in low columns: they are part of handoff behavior, not replaceable with the reference compressor/ripple adder. Replaced the bare `OR(g_1, ZERO)` insertion, where `g_1` was hard-coded gate 387, with the intended original column-four slot `columns[4][3]`. This avoids reliance on gate numbering, permits graph transformations, and uses inherited constant folding. Enabled the kit's existing AND/OR absorption throughout the circuit; one redundant OR disappears (cost -1). Tested permutations of inherited full-adder pin assignments: zero additional weighted savings, so rejected. Tested 1,050,624/1,050,624 prescribed input rows with *raw 19-bit output equality* against immutable handoff. This is an empirical comparison, not a formal equivalence proof. EVM and weighted cost independently checked on complete graphs.

## Directional pass

Inspected the kit's `MUX_XOR(a,b,c,d,e)` truth table and cost: `e XOR ((a AND b) OR (c AND d))`, gate cost 4.8. Extended the shared Booth recode MUX_XOR pattern to the terminal sign-inverted bit in each of the four non-top rows of both products. Existing MUX_XOR row recode term and negation-control factoring remain shared; the old terminal XOR/intermediate cones drop out, giving -9.6 weighted cost against general baseline (AND 410->378, OR 386->370, MUX_XOR 45->53). Verified raw-output equality across the entire stimulus with the saved general baseline, separately verified full EVM and full graph cost. The topmost row MUX_XOR alternate was empirically equivalent on 8192 external-stimulus cases but cost 1024.0, so rejected. No truth_table_exact_synth call was needed: the effective mapping was algebraically exact and confirmed empirically. This verification is not a formal proof.

Final vs original parent: cost -21.4, EVM +0.34396563852156 dB (worse, still below -57.6 dB), and pre-compression slots -1. Thus final is an eligible three-objective Pareto tradeoff, not a strict dominance claim. No deletion/layout search or new approximation scheme was conducted because this assignment requires Boolean equivalence to handoff.
