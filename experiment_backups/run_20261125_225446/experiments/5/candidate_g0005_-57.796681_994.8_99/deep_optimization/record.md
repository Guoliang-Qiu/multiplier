# Deep optimization record

External stimulus: `/home/guoliang/multiplier/stimulus.npy` (1,050,624 cases), evaluated with workspace `gate_cost.py` and `eval.py`.

| circuit | weighted gate cost | EVM dB | pre-compression slots |
|---|---:|---:|---:|
| immutable original parent | 1023.8 | -58.18330682718984 | 100 |
| immutable handoff | 1010.8 | -57.79668147672042 | 100 |
| general-equivalence baseline (`general.py`) | 1000.8 | -57.79668147672042 | 100 |
| delivered directional (`directional.py`) | 994.8 | -57.79668147672042 | 99 |

General pass: inspected all three stages and tap2's constant folding, cache, adders and reference algorithms. The col-3 compressor and col-6 output OR cannot be replaced by the reference because they intentionally approximate; the rest uses `_add3`. An alternative SOP-based global `_xor` cost 1021.8 and was rejected. Factoring the Booth recoding sign control for steps 0–3 decreased the cost to 1000.8. A hard-coded gate ID 101 in the handoff's compensation becomes incorrect after changing gate creation order: replaced it by the actual Boolean function `_xor(b[1],b[2])`. Handoff versus baseline raw outputs agreed on all 1,050,624 stimulus vectors (empirical, not formal equivalence); official EVM remained identical. No exact-synthesis plugin schema/tool was available, so no SAT or formal equivalence is claimed.

Directional pass: restoring one removed col-4 term produced cost 1013.8, count 101, EVM -57.85930459358372 and was rejected. Removing a col-5 real product produced cost 988.8, count 99, EVM -54.882518577463735 and failed the hard EVM limit. Removing col-18 compensation was behaviorally unobservable due to output layout, giving cost 1000.8 and count 99. Replacing direct `add('OR', signal, ZERO)` with the shared signal and `add('OR', ZERO, ZERO)` with ZERO reduced cost to 994.8, same 99 slots. Removing the zero slot changed low compressor ordering and failed EVM (-54.900772458915014, cost 990.8, count 98); consequently it is retained. Final versus handoff raw outputs matched on all 1,050,624 stimulus cases (empirical, not a proof). Final EVM is strictly under -57.6 dB and represents a Pareto tradeoff against parent (29.0 cheaper weighted cost, one fewer slot, worse EVM); it is not claimed to dominate the parent. The archive contains e.g. (963.2, -57.61668813404249, 90) which does not dominate the final because final EVM is better.

All trials remain in this experiment directory; no baseline snapshot or evaluator was modified.
