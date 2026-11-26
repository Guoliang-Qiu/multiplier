# Deep optimization record

All measurements use the workspace `gate_cost.py` and full `eval.py --stimulus-file /home/guoliang/multiplier/stimulus.npy` (1,050,624 cases). Triple is (weighted cost, EVM dB, precompression slots).

| Circuit | Triple | Result |
|---|---|---|
| Immutable parent | (970.2, -57.77706902080404, 93) | eligible; better EVM than handoff |
| Immutable handoff | (968.2, -57.65277192275167, 92) | eligible |
| General-equivalence baseline, final delivery | (967.2, -57.65277192275167, 91) | eligible, non-dominated versus parent; 0 raw mismatches with handoff on entire stimulus |

## Ordered general equivalence pass

Inspected tap2's gate cache, constant folding, exact `_ha`, `_fa`, `_add3`, reference compression and output algorithms, and the supplied Booth product generation, compensation, custom compressor, and clipped output. The customized compressor discards low-bit sums and the output replicates bit 17, so reference stages are *not* equivalent drop-ins. Preserved the supplied architecture and gate generation order to keep hardcoded compensation observations valid.

* Replaced the explicit XOR and AND of observations 689 and 230 with inherited `_ha` to share the exact half-adder sum and carry: cost 968.2 -> 967.2, same EVM and 92 slots.
* Removed the sole column-18 ONE: the output explicitly uses `outputs[17]` for sign bit 18; a column-18 slot is unreachable. Cost and output remain unchanged, slots 92 -> 91. Full-stimulus raw mismatch count 0 relative to baseline before deletion and relative to handoff. These are sampled checks, not a formal whole-domain proof.
* Tested post-generation compressor absorption, XOR cell substitution, five exact full-adder input permutations, alternative exact full-adder implementation, and explicit top-row polarity mux logic. Compressor absorption and permutations made no cost difference. Native downstream XOR increased cost to 974.2; alternative FA increased cost to 1036.2; polarity mux increased cost to 996.2. The tested alternatives were rejected. Full evaluations of XOR and top-row alternatives matched the handoff EVM, but raw equivalence was only explicitly checked for retained rewrites. Exact synth was unnecessary: the two-observation half-adder has a supplied exact and cheaper library realization.

## Subsequent distribution-guided pass

The actual external stimulus was sampled deterministically at every sixteenth row (65,664 rows) to inspect all 92 weighted slots before compression. Slot (column,index)=(5,7) has P(1)=0.09533; (10,9) P(1)=0.01610; (10,4) P(1)=0.10730. Conditional top-row slots near columns 12-16 have probabilities ~0.25 or ~0.75. These marginal biases do not establish low output error: column-10 weight is 32x column-5, and the downstream carry and quantization interact strongly. Statistical evidence was used only to prioritize actual implemented circuits.

* Replace (5,7) with ZERO: cost 962.2 but EVM -57.34356521559061, invalid. Removing it entirely: cost 961.2, EVM -55.471031350492, invalid. Removing it plus a column-4 ONE: 961.2, -54.89167423330116, invalid. Moving its contribution to column-4 ONE: 966.2, -57.124174225303165, invalid.
* Replace biased (10,9) with ZERO: 962.2, -47.23127192466226, invalid. Other zero/one slot substitutions were screened with complete weighted cost, including (10,4), (6,3), (8,4), but not promoted without full qualifying EVM.
* Remove column-18 ONE: 967.2, -57.65277192275167, 91, raw-output-equivalent; because this is an equivalence optimization, it was incorporated into the **general** baseline rather than claimed as a distribution improvement.

No approximate directional experiment beat the valid baseline. Retained the general-pass baseline. No candidate was modified except the assigned delivery file; immutable snapshots remain unchanged.
