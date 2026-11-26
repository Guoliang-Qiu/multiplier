# Deep optimization results

Configured stimulus: `/home/guoliang/multiplier/stimulus.npy` (1,050,624 vectors). All figures are complete reachable-circuit `gate_cost.py` and full `eval.py` results; objective minimizes cost, EVM dB, slots.

| Implementation | Weighted gate cost | EVM dB | Pre-compression slots |
|---|---:|---:|---:|
| Original parent (unchanged) | 1020.4 | -58.12928019806061 | 93 |
| Immutable handoff (unchanged) | 1016.6 | -57.94456262108487 | 93 |
| General optimized baseline | 1015.6 | -57.94456262108487 | 93 |
| Directional trial | 1015.6 | -57.94456262108487 | 93 |

General pass: inspected the entire Booth partial-product generation, both deletions, correction G and insertion in column 4, reference LIFO compression, and the specialized low-column output adder and six zeroed output bits. Removed the standalone `OR(d[1], ZERO)` gate while preserving the same actual column-4 slot as `d[1]`. This saves 1 weighted cost versus the handoff and 4.8 versus the parent. Replaced a Booth selected-digit guard by the equivalent `~(m & low)` to explore sharing with row correction; no weighted cost benefit, hence restored it. Replaced a saturated sign-row AND/OR factor by XOR: cost increased to 1019.6, hence reverted. Inherited constant folding, hash-consing, full/half adders and constant-aware compressor were retained; the intentionally nonreference output stage preserves handoff's low-bit carry treatment. Correction G and numeric compensation leaf were reconstructed from named buses instead of fragile gate numbers. Full-stimulus raw-output comparison against handoff: **0 mismatches / 1,050,624 cases** (empirical, not a formal proof). General baseline full EVM evaluation completed.

Directional pass: verified installed MUX_XOR truth table and port order `(a,b,c,d,e)` with function `e ^ ((a & b) | (c & d))`, cost 4.8. Existing source uses this cell in partial products and G. Tried integrating mutually exclusive low Booth product terms in one cell, costing 1022.8; and saturated sign-row bit-2 selection, costing 1019.2. Both cost more than existing shared ordinary gates and were rejected. Reordered the two OR arms of G inside MUX_XOR (1015.6, equal cost), but this produces no whole-circuit improvement, so final delivery retains the general baseline. The tested directional trial's full eval matched the general baseline and full-stimulus raw outputs had **0 mismatches / 1,050,624** (empirical). No exact-synthesis Cordis API was available in this session, and no formal equivalence claim is made.

The final general baseline is a Pareto cost/accuracy tradeoff against parent: cost 1015.6 < 1020.4, EVM -57.94456262108487 < -57.6, while parent retains better EVM. Slot count 93 is unchanged, including all constants and repeated slots. No approximation layout search was undertaken.
