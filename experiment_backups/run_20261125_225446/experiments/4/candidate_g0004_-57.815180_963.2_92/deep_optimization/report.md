# Deep gate-level optimization report

All EVM evaluations use `/home/guoliang/multiplier/stimulus.npy` (1,050,624 cases), the unmodified workspace `eval.py`, and the installed tap2 cost library.

| Circuit | Weighted cost | EVM (dB) | Pre-compression slots |
|---|---:|---:|---:|
| Original parent | 973.2 | -57.852453944355204 | 92 |
| Immutable handoff | 972.2 | -57.8151798686191 | 92 |
| General-equivalence baseline (`general.py`) | 963.2 | -57.8151798686191 | 92 |
| Final delivered candidate | 963.2 | -57.8151798686191 | 92 |

General pass: inspected the two-product Booth generation, sign compensation, column-4 X/G compensation, custom lossy compressor and final approximate ripple adder. Replaced the fragile numeric compensation observations 478/721 by the actual AND-carry operands accompanying the intentionally omitted CD column-4 XOR sum, and used tap2's constant-folding `_or` instead of constructing a raw `OR(node,ZERO)`; this independently saved 1.0 weighted cost. Factored identical-input pairs within AND/OR cones at gate construction (both distributive orientations), saving another 8.0 weighted cost across reachable gates. The handoff and general baseline have identical raw outputs on **all 1,050,624 configured samples** (empirical bitwise comparison, not a formal proof), identical full-evaluator EVM; algebraic equivalence of `s&x | s&y = s&(x|y)` and the dual ensures the local factoring rewrite. No change to the true column-slot count. General-pass rejected trials: native XOR in place of shared Boolean XOR cost 987.2; reverting sign-digit factoring cost 999.2; replacing sign activity with XOR cost 977.2; removing the specialized bit-pattern `_and` factoring cost 977.2; a De Morgan rewrite produced no cost gain (963.2).

Directional pass: verified the library MUX_XOR truth table `e ^ ((a&b)|(c&d))`, ports `(a,b,c,d,e)`, cost 4.8. Tested using MUX_XOR on full-adder sum cones (1087.2), adding step-3 Booth cells (986.8), restricting mapped Booth cells to step 1 or step 2 (969.6 in either case), and an alternative shared zero-digit correction (963.2). Each offers no complete-circuit improvement over the general baseline; directional candidates were not promoted. These unsuccessful alternative circuit rewrites are not claimed to be proven equivalent by evaluation. The final retained implementation uses the existing 24 MUX_XOR cells. No exact-synth request was necessary for the simple fully specified two-input factoring identities; no don't-care assumptions were used.

The final candidate improves the original parent weighted cost by 10.0, while trading 0.0372740757361 dB of EVM margin; it meets the strict runtime limit -57.6 dB. Its delivered standalone `Candidate(MultiplierCircuit)` implements the three genuine stages, builds without arguments, and was validated by `gate_cost.py` and full `eval.py` after copying. It introduces no dependency on any trial source.
