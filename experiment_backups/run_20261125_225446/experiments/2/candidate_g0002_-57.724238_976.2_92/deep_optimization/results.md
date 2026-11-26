# Deep optimization record

Required stimulus: `/home/guoliang/multiplier/stimulus.npy`, shape (1,050,624, 4); evaluator `eval.py`, Q4.7 output rounding. Costs include reachable gates only; slots count pre-compression columns, including constants and repetitions.

| Complete circuit | Weighted cost | EVM dB | Slots | MAE | RMSE | Maximum error |
|---|---:|---:|---:|---:|---:|---:|
| immutable parent | 978.2 | -57.7781172796199 | 92 | 0.2637651455 | 0.3116979083 | 0.921875 |
| immutable handoff | 977.2 | -57.72423799932994 | 92 | 0.2649779812 | 0.3136374050 | 0.921875 |
| saved general-equivalence baseline, delivered | 976.2 | -57.72423799932994 | 92 | 0.2649779812 | 0.3136374050 | 0.921875 |
| directional G OR | 974.2 | -57.66509477604998 | 92 | 0.2663267481 | 0.3157802855 | 0.9140625 |
| directional G d[1] | 972.2 | -57.54787340839245 | 92 | 0.2690547995 | 0.3200708192 | 1.046875 |
| directional G AND | 974.2 | -57.36250974603955 | 92 | 0.2735218769 | 0.3269747863 | 1.046875 |
| directional G deletion | 964.2 | -55.495614023439856 | 91 | 0.3293964542 | 0.4053769499 | 1.25 |
| directional constant deletion | 972.2 | -55.59406104445025 | 91 | 0.3268737124 | 0.4008082938 | 1.21875 |

## First: general equivalence optimization

Inspected tap2’s `_gate`, `_fa`, `_ha`, `_add3`, reference compression/output routines and the complete handoff’s product, compressor, and output stages. The handoff uses a non-reference approximate compressor and output assembler, so replacing them with tap2 reference stages would change the circuit. Removed a raw `OR(correction, ZERO)` buffer (the kit’s constant-aware `_or` already folds this); this removes one reachable OR and saves 1 weighted cost. Replaced brittle prefix node identifiers 29/30/24 with the corresponding input-bus bits `d[0]`, `d[1]`, `c[4]` in the correction expression, without changing weighted cost or raw outputs. Preserved the actual pre-compression 92 slots. On the *entire configured workload*, handoff versus saved baseline had **zero differing 19-bit raw outputs**. This is a sample-based equivalence check, not a formal proof. Both circuits were evaluated completely with gate_cost.py and eval.py.

Additional exact rewriting attempts: replacing the custom AND/OR `_xor` with the kit’s native XOR raised weighted cost to 988.2 (8,192 sample outputs equal); exact full-adder carry-first factoring raised cost to 1044.2 (8,192 equal); sharing a top-row XOR selector raised cost to 982.2 (8,192 equal); expanding MUX_XOR selection into Booth step 3 raised cost to 1001.8 (8,192 equal). The installed kit contains the intended 4.8-cost, five-port MUX_XOR, so existing instances remain. No Cordis exact-synthesis plugin was available as a callable workspace API; no SAT or formal equivalence claim was made. The reference full-adder and constant-aware compressor remained inherited, and compression and output behavior remained unchanged.

## Second: directional optimization

Compared current archive objectives (including 954.2/-57.7235316/92, 970.2/-57.7770690/93) and the parent. Evaluated full-circuit compensation removal (a low-weight one) and removal of G; both reduce slots to 91 but substantially increase rounded-output errors and violate -57.6 dB. The first compensation trial initially failed during construction because changing `EXTRA_ONE` shifted indexed columns; repaired by deleting the original constant *after* the existing indexed mutations, then measured the complete circuit. No failed circuit was retained. Distribution-guided low-column alternative G=`d[1] | (d[0]&c[4])` is feasible at 974.2/-57.66509/92, trading a 2-cost saving for noticeably worse EVM and MAE versus the general baseline. G=`d[1]` and G=`d[1] & (d[0]&c[4])` violate the EVM bound; their rounded errors and higher maxima explain rejection. The trial to extend MUX_XOR across the third Booth row retained sample-based raw equality but cost 25.6 more, so no cross-layer mapping was adopted. No synthetic stimulus was used for screening or evaluation.

Select saved general baseline: 976.2/-57.7242379993/92, EVM strictly below -57.6. Against the parent, the delivered design is a valid Pareto tradeoff: cost 2.0 lower, same slot count, EVM 0.0538797 dB worse. Relative to the handoff, it strictly improves weighted cost at bitwise-identical raw outputs on all configured samples. The archive’s 954.2/-57.7235316/92 entry has slightly worse EVM, so it does not dominate the delivered candidate (although the delivered circuit is not a global best-cost solution). The candidate retains its standalone, three-stage architecture and zero-argument `build_circuit()`.
