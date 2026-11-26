# Deep optimization record

All costs are output-reachable weighted gate costs; precompression counts include every slot. EVM used the complete configured `/home/guoliang/multiplier/stimulus.npy` (1,050,624 rows), with the workspace `eval.py` and `gate_cost.py`.

| circuit | cost | EVM dB | slots |
|---|---:|---:|---:|
| immutable parent | 978.2 | -57.7781172796199 | 92 |
| immutable handoff | 979.2 | -57.71198998619433 | 91 |
| saved general_baseline.py | 977.2 | -57.71198998619433 | 91 |
| final dir_step0.py | 970.2 | -57.71198998619433 | 91 |

## General pass (completed and baseline saved before directional trials)

Inspected Booth partial-product generation, sign-extension substitution and compensation, 3:2 compression, and the custom output ripple and bit masking. The handoff's two unshared OR-with-ZERO buffers have exactly the same Boolean values as their operands, and removing them preserves slot ordering and the full source architecture. Their two reachable OR gates disappear, saving 2.0. Measured alternative native XOR versus existing three-gate XOR (991.2); alternative column-3 majority/sum factoring (979.2, no saving); high-sign selection expansion (1007.2); Booth p complementary factoring (979.2); Booth two selection factoring (979.2); output carry De Morgan (984.2); proposed sign-digit factoring was **not equivalent** on 2,984/3,995 sampled external rows and was rejected. No SAT/exact synthesis claim is made: the configured exact tool was not called, since direct algebraic alternatives and whole-circuit measurement sufficed for these small local trials.

## Directional pass

Inspected installed `tap2_9bit_multiplier.py`: MUX_XOR ports `(a,b,c,d,e)`, function `e ^ ((a&b)|(c&d))`, cost 4.8. Existing 24 cells mapped Booth middle digits. Extending the mapping to step-0, digits k=4..8, lets the step-0 `negative=q[1]` term act as cell e directly, eliminating surrounding complement/XOR logic; step-0 3..8 had the same reachable graph. Final cost saves 7.0 versus general baseline and 9.0 versus handoff, with 34 MUX_XOR cells. Extending to step 3 (1002.8), zero-e generic cells (1038.2), or sign-digit cells (1022.8) raised full-circuit cost. Low-digit ranges 3..5, 3..6, 3..7, 5..8, 6..8 measured 975.4, 973.0, 970.6, 975.6, 978.0 respectively, none better than 970.2.

Raw output equality was tested on every one of the 1,050,624 external workload inputs for final versus saved general baseline: **zero differences**. Sample-based verification, not a formal proof. General baseline has full-evaluator identical metrics to handoff, and elimination of `OR(signal,ZERO)` is a Boolean identity independent of stimulus. Step-0 mapping identity follows by splitting on `(q1,q0)` = `(0,0),(0,1),(1,0),(1,1)` and substituting Booth `one=q0`, `two=q1&~q0`: e=q1 XOR selected uncomplemented multiplier partial products exactly matches original selected `(q1 XOR multiplier_bit)` terms. Complete circuit validates and final EVM is below -57.6 dB. Parent versus final is a Pareto tradeoff: final improves cost and slots but EVM increases from -57.7781 to -57.7120 dB.
