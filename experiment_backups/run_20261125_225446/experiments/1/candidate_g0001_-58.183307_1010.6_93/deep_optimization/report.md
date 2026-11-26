# Deep gate-level optimization record

All metrics use the workspace gate_cost.py and full eval.py with `--stimulus-file /home/guoliang/multiplier/stimulus.npy` (1,050,624 cases). Gate cost is weighted, including MUX_XOR=4.8; counts include every pre-compression column slot.

| Circuit | Weighted cost | EVM (dB) | Pre-compression slots |
|---|---:|---:|---:|
| Immutable parent | 1020.4 | -58.12928019806061 | 93 |
| Immutable handoff | 1015.6 | -58.18330682718984 | 93 |
| Saved general baseline | 1010.6 | -58.18330682718984 | 93 |
| Final delivered candidate | 1010.6 | -58.18330682718984 | 93 |

## General equivalence pass

Inspected the complete generation, G compensation, reference LIFO compression, and specialized final adder against the installed tap2 primitives. Simplified the replacement at column 4 from a manually appended `OR(ONE,ZERO)` gate to the canonical ONE leaf. Though the apparent buffer costs one OR, its graph-level propagation removes three AND, three OR, and one NOT from the reachable arithmetic cones, saving **5.0** weighted cost. Eliminated unused integer node references (`23`, `24`) and dead pseudo-G local variables, preserving the real compensation bit and the three semantic stages. Tested alternative digit-sign guard factoring (equal cost) and multiplexer factoring / top-row XOR (more expensive); retained the lower-cost implementation. The saved baseline's complete EVM is identical to the handoff and a raw-output comparison across all 1,050,624 external-stimulus cases finds zero differences. This is empirical sample-based equivalence, not a formal proof.

## Directional MUX_XOR pass

Verified the installed five-port truth table and actual cost: `e ^ ((a & b) | (c & d))`, `(a,b,c,d,e)`, cost 4.8. Explored full-adder sum remapping to a MUX_XOR with ordinary majority carry (1133.4 total cost); replacing top Booth-row OR-of-AND selections with MUX_XOR cells (1032.2); permuted MUX_XOR port groupings of G and digit rows (1010.6 each, zero raw differences on all cases). More cells did not yield a saving: the top-row remapping loses shared cones, and the full-adder replacement increases weighted cost. Consequently retained the independently verified general baseline as the final directional result.

The final candidate strictly improves the original parent in both cost (9.8 cheaper) and EVM (0.05402662912923 dB lower), with identical slot count, and satisfies EVM < -57.6 dB. The final delivered file passes `gate_cost.py`, complete `eval.py`, and zero-argument construction with installed tap2; bitwise signed raw outputs equal the immutable handoff on the complete configured stimulus. The immutable handoff and parent were not changed. No SAT synthesis was invoked, so there are no SAT/timeout claims.
