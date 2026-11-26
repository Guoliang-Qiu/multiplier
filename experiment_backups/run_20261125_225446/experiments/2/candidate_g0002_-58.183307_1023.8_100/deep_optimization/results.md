# Deep gate-level optimization record

All weighted costs and EVM values below come from workspace `gate_cost.py` and `eval.py --stimulus-file /home/guoliang/multiplier/stimulus.npy` (1,050,624 rows). Partial-product counts include every precompression slot.

| circuit | weighted cost | EVM (dB) | precompression slots |
|---|---:|---:|---:|
| immutable original parent | 1067.2 | -58.34955620145295 | 101 |
| immutable handoff | 1053.2 | -58.18330682718984 | 100 |
| saved general baseline (`general_baseline.py`) | 1032.2 | -58.18330682718984 | 100 |
| delivered directional candidate (`generations/2/candidate_g0002_0001.py`) | 1023.8 | -58.18330682718984 | 100 |

The final candidate improves the parent's cost by 43.4 (with one fewer slot), trading 0.16625 dB EVM; the final EVM meets the strict -57.6 dB limit. Relative to handoff, cost decreases 29.4 with identical output and slot count.

## General equivalence pass (before directional changes)

Inspected Booth recode / partial-product generation, the two deleted column-3 bits and replacement compensation constant, the custom low-column compressor, and the low-column OR/output-sign construction. Removed the dead input-dependent branch replacing both products' column-2 slots with `[zero,one]`, and replaced a raw `add('OR', one, zero)` compensation node by its actual constant `one`. The raw node bypassed tap2's constant-folding and hash-consing and pinned a redundant cone of gates; full-circuit reachable cost fell by 21.0. Saved and evaluated this baseline BEFORE expanding MUX_XOR use. The compensation is still a real precompression slot and the original algorithmic column layout remains intact.

Other local general-pass trials: using the library XOR directly raised cost (1053.2 before cleanup, 1044.2 after); alternative custom compressor expression did not reduce cost, while one proposed compressor decomposition changed raw behavior. Shortening the terminal output loop did not affect reachable cost. Three attempted Booth simplifications of `p`, `b` and `d_tmp` were rejected because raw outputs changed on the configured stimulus (4,455, 1,539, and 1,105 mismatches on a 9,298-row subsample, respectively). No inferred reachability-based don't-cares were used; exact synthesis was not needed for these small explicitly checked rewrites.

## Directional pass (after general baseline)

The preexisting 24 MUX_XOR cells already implement the shared-library truth table `e ^ ((a & b) | (c & d))`, ports `(a,b,c,d,e)`, cost 4.8. Expanded the zero-digit-aware partial-product mapping from Booth steps 1 and 2 to steps 0 and 3 as well, giving 46 reachable MUX_XOR cells and an additional 8.4 weighted cost saving. `cell_neg = negative & (generated_one | two)` retains the necessary all-zero row and preserves the full handoff output; the final sign-inverted terminal bits remain in the existing realization. Considered mapping step 4 and the top bits (both had no effect on reachable cost); mapping the low custom compressor into MUX_XOR increased cost to 1041.6, mapping all XORs to MUX_XOR raised cost to 1108.4, and a proposed column-2 MUX_XOR failed sample equivalence. Gate count alone was not used to select the mapping.

Both optimized circuits were compared bitwise on the **raw 19-bit signed output**, for *all 1,050,624 configured stimulus rows* versus immutable handoff: zero mismatches each. This is empirical sample-based equivalence, **not formal proof**. Both passed `Circuit.validate()`. The final delivery path was independently remeasured with both evaluators and a parameterless import/build/validate check; no processes were left running.
