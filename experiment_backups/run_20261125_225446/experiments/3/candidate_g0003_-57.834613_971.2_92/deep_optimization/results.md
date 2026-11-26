# Deep optimization results

All figures use `gate_cost.py` and full `eval.py --stimulus-file /home/guoliang/multiplier/stimulus.npy` (1,050,624 samples). Objective order: weighted cost, EVM dB, honest pre-compression slots.

| Circuit | Cost | EVM dB | Slots | Raw-output relationship |
|---|---:|---:|---:|---|
| Immutable original parent | 969.2 | -57.83461265306508 | 94 | baseline |
| Immutable supplied handoff | 974.2 | -57.83461265306508 | 93 | not assumed equivalent |
| Saved general-equivalence baseline | 971.2 | -57.83461265306508 | 93 | 0/1,050,624 mismatches vs handoff |
| Delivered directional candidate | 971.2 | -57.83461265306508 | 92 | 0/1,050,624 mismatches vs handoff |

The final candidate improves on the original parent by **two** partial-product slots while retaining its measured EVM (but costs 2 more). It also improves handoff cost by 3 and slot count by one, and is not dominated by the inspected cross-generation archive: the archive has a 969.2/-57.83461265306508/93 candidate, but none with both at most 971.2 cost and at most -57.83461265306508 EVM and 92 or fewer slots. The required EVM is strictly below -57.6 dB.

## Ordered general equivalence pass

Inspected handoff partial-product generation, both signed top Booth-selector products, special low-column carry-only compressor, low-column final-adder OR approximation, and tap2's folding, full adder, half adder and MUX_XOR mapping. Identified the original G inputs as the first and fourth *original* column-five slots, before deletion, instead of opaque numeric node IDs 94 and 417. Replaced buffered `OR(signal,ZERO)` slots by their exact original signals, and replaced the one-off primitive XOR with the existing absorption-aware `_xor`: this reuses an output-reachable sum network and costs 971.2 instead of 974.2. Raw sample comparison: zero mismatches, maximum raw difference zero. Full eval confirms unchanged EVM. The source of this stage is `general_equivalence_baseline.py`.

Additional measured general-pass experiments: isolated `_xor` reuse 973.2, removal of two redundant buffers 972.2, combined rewrite 971.2; alternate XNOR factoring 978.2; SOP XOR 987.2; disabled absorption 974.2; alternate full-adder 974.2; original SOP signed selector 1002.2; De Morgan compensation AND 972.2; disabled specialized `_and` factoring 977.2. The initial attempt to bind G inputs after deleting column slots changed 377,181 raw outputs and yielded -55.6433 dB, so it was discarded and corrected to bind before deletion. The exact-cone synthesis service was not exposed as a callable tool; no SAT claim is made. These checks are stimulus-sample equivalence, not formal proofs.

## Subsequent directional pass

The output stage explicitly sets bit 18 equal to bit 17. Therefore the additional column-18 constant does not influence the 19-bit output; deleting it changes the honest precompression slot count 93 -> 92, without changing weighted output-reachable cost, raw output on the complete configured stimulus, or measured EVM. Both signed products and their other high-weight compensation are preserved. The two originally removed column-five partial products are recombined into a sum at weight five and carry at weight six, and both appear in the precompression column count.

Other complete-circuit trials: replacing G sum by OR cost 970.2, EVM -57.63581 (feasible but dominated by archive); replacing it by AND -56.21482; dropping G sum -56.35722, dropping G carry -56.19444; deleting the column-four ZERO yielded cost 960.2 and 92 slots but EVM -57.57330 (infeasible), indicating its compressor scheduling and rounding-boundary effect. Adding an extra weight-four ONE to that layout gave -57.61328 at cost 963.2 and 93 slots, dominated by archive; combined G OR plus that compensation yielded -57.15940. Removing weight-ten compensation yielded -29.5463 dB due to an 8-unit output offset; removing the column-four one yielded -56.84644 dB. Changes to final low-column OR and 6/7 rounding deteriorated EVM. No approximation with better overall Pareto tradeoff was found, so the equivalently optimized circuit plus dead-slot removal was selected. MUX_XOR remains available and 24 such cells are retained; a new MUX_XOR G mapping cost 974.0 and was rejected.

`gate_cost.py` validates the final parameterless `build_circuit()` and output bus, with 455 AND, 401 OR, 240 zero-cost NOT, and 24 MUX_XOR cells (24*4.8), for a fractional weighted total 971.2. Official `eval.py` results: MAE 0.26250947799831337, RMSE 0.309677119860418, maximum absolute error 0.875, bias 0.2853194193998043, EVM -57.83461265306508 dB. Final official evaluation on the assigned delivery path completed normally.
