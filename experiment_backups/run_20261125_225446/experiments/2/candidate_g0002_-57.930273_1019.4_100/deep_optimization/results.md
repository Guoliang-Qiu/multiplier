# Deep optimization record

All metrics use workspace `gate_cost.py` and full `eval.py --stimulus-file /home/guoliang/multiplier/stimulus.npy` (1,050,624 samples); gate prices include fractional MUX_XOR=4.8. Pre-compression counts include every column slot.

| Circuit | Weighted cost | EVM dB | Pre-compression slots | MAE | RMSE | Maximum absolute error |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Immutable parent | 1067.2 | -58.34955620145295 | 101 | .2517868622 | .2918515081 | .640625 |
| Immutable handoff | 1046.2 | -57.93027338959716 | 100 | .2604202137 | .3062852498 | .75 |
| General-equivalence baseline | 1019.4 | -57.93027338959716 | 100 | .2604202137 | .3062852498 | .75 |
| Delivered candidate | 1019.4 | -57.93027338959716 | 100 | .2604202137 | .3062852498 | .75 |

## General equivalence pass (completed and frozen before directional trials)

Inspected product generation, the special column-three compressor and output ripple construction, plus tap2's `_gate`, `_fa`, `_ha`, `_add3`, reference compressor and reference output assembly. The existing special compressor is 3 cheaper than replacing it with the reference in the improved circuit; the output's intentional low-column OR cannot be replaced by an exact ripple adder without changing behavior. The original XOR uses cheaper 2 AND + OR compared with the weighted XOR=3 on most complete circuits. Testing primitive XOR gave 1058.2; primitive XOR plus an alternative parity-based full adder 1202.2; Booth-only primitive XOR 1052.2; XOR sum-of-products 1058.2; NAND-like factoring 1098.2. Their full-circuit cost does not justify integration.

Expanded the original MUX_XOR Booth mapping to valid steps zero and three as well as one and two: 1035.4, compared with 1046.2. The digit-one and digit-two selectors are mutually exclusive and the sign-flip term is gated with their union; the shared kit's MUX_XOR pin order is `(a,b,c,d,e)`. Factored high sign-extension row bit 9, whose two selected XOR arguments both resolve to the same sign-bit-XOR, into `(one | two) & sign_xor`: 1019.4. Replaced a redundant identical-branch conditional for a constant column with the identical unconditional assignment. This preserves all pre-compression slots. Sample-based raw-output bitwise equality against handoff checked all 1,050,624 external stimulus inputs: zero mismatches (not a formal proof). Complete eval independently confirms matching EVM and errors. Saved `general_baseline.py` before directional trials.

No exact cone synthesis plugin was invoked: local algebraic identities and complete stimulus equivalence sufficed for the useful rewrites; no SAT or formal infeasibility claims are made. Unchanged tap2 primitives and compressor `_add3` are inherited.

## Directional trials

Measured the required stimulus input means approximately (-.351, -85.667, -.401, +84.667), with 13.63% of cases within 8 raw counts of a Q4.7 half-way rounding boundary. Screening used this file only. Additional deletion at column 6 slot 0 cost 1004.6/99 slots, but EVM -55.1135, MAE .3447, RMSE .4236 and maximum 1.25; deletion at column 3 slot 1 cost 1010.4/99, EVM -54.4743, RMSE .4560; column 4 slot 0 cost 1009.6/99, EVM -54.9416, RMSE .4321. These fail because weighted low-column deletions propagate through the nonlinear approximate carry/output logic, concentrating error near rounding boundaries. An attempted column 4 slot 4 deletion was invalid after the existing two deletions, so it was excluded. Additional one-bit rounding compensation at column 6 has EVM -51.9362; at column 7 -47.0347, both causing large positive quantized shifts. Removing compensation at column 10 yields EVM -29.6168 (approximately 8 real-value units raw bias); do not repeat without a genuinely revised correction. Restoring one removed low-column slot cost 1035.4/101 and EVM -57.8572 (dominated by general baseline). Restoring both cost 1045.4/102 and EVM -57.5530 (ineligible). Other candidate costs were screened but were not credited with unmeasured accuracy. Shared Boolean intermediates and Booth MUX_XOR mapping were already exploited in the general pass. No directional attempt produced a better feasible trade-off, hence retained the general baseline.

The archive contains e.g. (986.2, -57.900191, 93) and (980.2, -58.026732, 94), which dominate this candidate globally; nonetheless the delivered circuit is an eligible improvement over its assigned original parent in gate cost and slot count, with a measurable EVM trade-off and EVM < -57.6. All construction remains static and readable and the selected output is a valid 19-bit bus. No snapshots, evaluator files, or unrelated delivery candidates were modified.
