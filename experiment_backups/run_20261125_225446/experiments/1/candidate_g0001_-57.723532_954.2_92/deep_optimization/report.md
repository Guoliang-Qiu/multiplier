# Deep gate-level optimization report

## Inputs and validation

Immutable parent and handoff are byte-for-byte identical (inspected sources); assigned delivery candidate initially has the same source. Installed tap2 `MUX_XOR(a,b,c,d,e)` has truth function `e ^ ((a & b) | (c & d))` and gate cost 4.8; AND/OR cost 1, XOR cost 3, NOT cost 0. Evaluators were run with `OPEN_QUESTION_SOLVER_ROOT=/home/guoliang/open_question_solver` and `--stimulus-file /home/guoliang/multiplier/stimulus.npy`. No evaluator or input file was changed.

| Circuit | Weighted gate cost | EVM dB | Precompression slots | Raw equality with handoff |
|---|---:|---:|---:|---|
| Original parent | 954.2 | -57.72353155447783 | 92 | identical source |
| Immutable handoff | 954.2 | -57.72353155447783 | 92 | reference |
| Saved general baseline (`general_baseline.py`) | 954.2 | -57.72353155447783 | 92 | 0 mismatches / 1,050,624 configured samples |
| Final delivery (original parent restored) | 954.2 | -57.72353155447783 | 92 | identical source |

The baseline retains valid behavior and satisfies EVM < -57.6 dB. The raw comparison is **empirical**, not a formal proof; its input stimulus is the configured external file. Algebraic replacements in general baseline: the step-four Booth bit-one expression factors to a plain XOR of the two multiplicand low bits; in the output-adder stage nonconstant full adders use the existing candidate's factored adder instead of tap2's full adder (the overall cost is unchanged). Two complete consecutive Boolean cleanup passes were tried, and the second pass does not change measured reachable cost. The precompression layout, compensation terms, approximate carry/drop in columns 0–3, zero-boundary opacity, and final output rounding/bit mapping remain unchanged.

## General-pass negative experiments

All costs are measured on the entire resulting candidate by `gate_cost.py`. Replacing the candidate's `_fa_factored` by inherited tap2 `_fa`: 955.2; using native XOR instead of three-gate shared XOR: 1091.2; sharing sum OR and AND terms with a factored carry: 1017.2; sum-of-products polarity implementation of XOR: 1091.2. The alternative step-four digit expression and output full-adder replacement each alone gave no complete-circuit cost improvement; they are preserved in the saved general baseline only as equivalent independently useful simplifications. The unmodified handoff Boolean graph cleanup already folds constant OR buffers after compression, performs absorption and factoring, and removes unreachable gates; folding before compression would change special approximate compressor dispatch and was intentionally avoided. No deletion/compensation-layout mutation was made.

## Directional-pass negative experiments

After saving and evaluating the general baseline, the MUX_XOR experiments in `directional_trial.py` measured: broadening step-zero placement to k=3 or k=9 had unchanged cost 954.2 (those bits are unreachable or excluded by top-digit guard); simplifying step-zero MUX_XOR correction masking had unchanged cost 954.2; mapping full-adder sum to MUX_XOR and majority carry to shared AND/OR gave cost 1080.0; mapping signed top Booth digit through a MUX_XOR gave cost 999.8 with full-stimulus EVM -57.72353155447783; adding MUX_XOR in step-three Booth row gave cost 977.8. These alternatives provide no eligible Pareto improvement over the parent. The signed-top mapping's MUX_XOR equality follows because the two Booth one-digit and negative-digit controls are mutually exclusive; EVM was explicitly checked even though its cost is worse. As no directional experiment improved the saved baseline, and the baseline is not itself an improvement over the original parent, the delivery file is restored to the verified original parent. No SAT tool was invoked: the tested small rewrites have direct Boolean identities, whereas SAT timeout would not prove infeasibility.

All figures above are tool-reported fractional weighted cost, not raw gate counts. General and directional experiments were kept separate and none of the immutable snapshots was modified.
