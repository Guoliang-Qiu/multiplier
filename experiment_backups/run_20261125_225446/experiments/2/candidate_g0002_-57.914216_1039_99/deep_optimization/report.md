# Gate-level optimization report

All evaluations used `/home/guoliang/multiplier/stimulus.npy` (1,050,624 four-input cases); EVM threshold is strictly below -57.6 dB. Metrics below are complete-circuit `gate_cost.py` and `eval.py` results. Precompression counts include constants and repeated slots.

| Circuit | Weighted cost | EVM dB | Slots |
|---|---:|---:|---:|
| Immutable original parent | 1067 | -58.2916177846 | 100 |
| Immutable handoff | 1050 | -57.8082953223 | 99 |
| General-equivalence baseline (`general.py`) | 1045 | -57.8082953223 | 99 |
| Delivered directional (`biased_494_one.py`) | 1039 | -57.9142162739 | 99 |

The delivery dominates the handoff in cost and EVM. Relative to the original parent, it is a valid Pareto tradeoff (28 cheaper, one fewer slot, 0.3774 dB higher EVM), satisfying the runtime constraint.

## General equivalence pass (before statistical analysis)

Inspected the weighted rows/partial-product layout, correction logic, compressor tree, output ripple, tap2 constant folding, hash-consing, inherited XOR and half/full adders. The source carried three successive history wrappers, unnecessary `OR(signal, ZERO)` correction buffers and double NOTs. Flattened only this *correction bookkeeping* into one readable `_product_columns` while preserving the actual row generator, weighted slot order, compressor and output stages; removed five reachable identity OR buffers and redundant inversions. Node references 420/421/91/425/494 are still the original precompression prefix, with unchanged product generation. Measured 1050 -> 1045 cost, unchanged 99 slots and -57.8082953223 dB. Raw 19-bit outputs equal the immutable handoff on every one of the 1,050,624 external samples; this is a sample check, not an exhaustive formal proof. Local double-NOT and OR-zero identities are exact Boolean identities.

Additional explored exact realizations: using inherited native XOR globally reduced cost to 1040 but **changed behavior**, since the handoff's decomposed `_xor(a,a)` is `a`, whereas native XOR is zero. First counterexample was external sample index 13, `[217,-256,-222,-255]`, with raw 1024 versus 1088: rejected. Switching native XOR *only during compression* preserved full-sample raw equality but cost 1051: rejected. Enabling inherited absorption for all AND/OR calls retained cost 1045: no improvement. The compressor's unusual column-three carry/sum and low-column output OR were preserved because changing these changes output behavior. The reference compressor/output are not interchangeable with the existing special realizations. No SAT synthesis was integrated; no exact-synthesis plugin call or claimed SAT proof.

## Directional pass (starting from saved general baseline)

Precompression probabilities estimated by packed simulation on precisely the configured external stimulus (`statistics.txt`). Column-four signal 421 was one with probability 0.12535; the final correction `NOT(494)` was one with probability 0.90567. Column-ten signal 680 had probability 0.01566 of one but carries 1024 times the raw weight of a column-zero bit, and deleting it failed badly. Column-three observations 88 and 420 had probabilities 0.37415 and 0.25057, with joint probability 0.0939. Column-four correction 421 and signal 425 have joint probability 0.0629. Even strongly biased slots cannot be selected solely by imbalance: weighted correction, output rounding, reachability and cost matter.

Replaced the *single column-four correction slot* `NOT(494)` with `ONE` (a +16 weighted correction when the original signal is zero, occurring ~9.43% of samples), which eliminates four reachable AND/OR gates and two inversions: 1045 -> 1039, 99 slots unchanged, EVM -57.8082953223 -> -57.9142162739 dB. This is deliberately approximate, not equivalent. The final circuit includes its correction and full downstream logic in the measured cost. Other fully evaluated hypotheses: replace 421 by one (1035, -57.3072, fails error limit); replace both by one (1031, -57.2440, fails); delete 680 (1040, -47.2263, fails); delete 421 (1036, -54.8011, fails); delete the NOT(494) correction (1038, -55.2369, fails); substitute observations 443 (1043, -57.4620, fails), 483 (1044, -57.8107, dominated by chosen delivery); delete 421 while replacing correction (1030, -54.7921, fails). More expensive observations would reactivate otherwise removable logic and are not selected. No alternatives changed the parent/handoff snapshots.

Delivered candidate was copied from the verified scoped trial to `generations/2/candidate_g0002_0004.py`; rerunning both workspace evaluators on that exact artifact reproduces 1039 cost, -57.9142162739 dB, and 99 slots. Standalone import, zero-argument `build_circuit()`, 19 outputs and `validate()` succeeded. All commands and subprocesses completed before marker creation.
