# Deep optimization report

All full evaluations used `/home/guoliang/multiplier/stimulus.npy` (1,050,624 cases), workspace `gate_cost.py` and `eval.py`. Objectives are weighted cost, EVM dB, and **all** pre-compression column slots.

| Circuit | Cost | EVM dB | Slots |
|---|---:|---:|---:|
| Original parent | 959.2 | -57.77611271366918 | 94 |
| Immutable handoff | 959.2 | -57.77611271366918 | 94 |
| General-equivalence baseline | 959.2 | -57.77611271366918 | 93 |
| Selected final | 958.2 | -57.77611271366918 | 93 |

## General equivalence pass (completed before directional experiments)

Traced partial-product selectors, constant and sign compensation, compressor carry/sum logic, and output reachability. In particular, output bit 18 is assigned from bit 17 and output bits 0–5 are constants. Consequently the column-18 constant is unreachable and is removed from the honestly counted pre-compression layout: 94 -> 93 slots, unchanged cost and raw outputs. Full 1,050,624-case raw-output comparison against handoff passed; this is a **sample-based** check, not a formal proof. No other gate-saving exact rewrite survived measured cost. Trials of native XOR globally and individually in selector, high-cell, near-cell, compressor and output cones; native AND in place of the specialized selector; common-factor disabling; alternative global absorption; signed selector factoring; standard XOR full adder; input permutations of compressor/output adders; and majority carry factoring all cost at least as much or produced the same reachable circuit. One native-XOR high-cell trial failed the topology-dependent assertion (node identity differed), so it was not counted as a valid equivalent circuit. The exact synthesized-cone solver was not used: small locally identifiable exact cones already have library-native equivalent implementations, whose measured cost was non-improving.

## Directional pass

Tested partial-product ZERO-slot deletion (cost 958.2, slots 93, EVM -54.73144: changes compression schedule and quantization-boundary errors); low-column majority compression (column 5 cost 935.2 but sample EVM roughly -54.64; columns 6+ worse); output column-7 OR substitution (cost 958.2, EVM -56.08490); removal of signed compensation constants at columns 10, 11, 13, 15 (EVM -29.60, -23.58, -11.52, +0.68 dB); and insertion of a rounding bit at column 4 (cost 948.2, EVM -57.23566). These fail the strict -57.6-dB bound because dropped carries or compensation displace output quantization, sometimes by large fixed amounts. Cross-product reuse was inspected in the shared selector construction; native XOR substitutions increased weighted cost. All screening used a subset of the supplied external stimulus, never synthetic data; complete promising circuits were evaluated in full.

Adding **column 4** to the compressor's existing carry-only handling saves one OR gate. The removed sum is unobserved in the truncated low-bit output while its carry remains exact. Full raw-output equality against immutable handoff passes on all 1,050,624 supplied samples (sample-based, not formal). The final objectives [958.2, -57.77611271366918, 93] dominate the original parent [959.2, -57.77611271366918, 94], remain strictly feasible, and improve the same-EVM archived [959.2, -57.77611271366918, 94] record. No evaluator, seed, archive, or other candidate was modified.
