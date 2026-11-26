# Deep optimization record

All measurements use workspace `gate_cost.py` and full `eval.py --stimulus-file /home/guoliang/multiplier/stimulus.npy` (1,050,624 samples). Objectives are [weighted cost, EVM dB, pre-compression slots], minimized.

| circuit | cost | EVM dB | slots |
|---|---:|---:|---:|
| immutable original parent | 1037 | -58.18330682718984 | 93 |
| immutable handoff | 1022 | -57.719172653924716 | 92 |
| saved general-pass baseline `general.py` | 1017 | -57.719172653924716 | 92 |
| final `zero_position_1.py` | 1016 | -57.719172653924716 | 92 |

## General Boolean-equivalence pass

Inspected the three construction stages and tap2 primitives/compressor. Tried inherited `_and_absorb`/`_or_absorb` across product, compensation and output cones (no measurable saving); removed the handoff's two raw `OR(ZERO, x)` identity buffers and double NOT, preserving their **actual zero-valued column-four slot** and the actual column-five signal. Replaced brittle numeric node 91 with the actual row-zero Booth bit (step 0, k=4, first product), and removed unused numeric node references. Factored compensation G into `MUX_XOR` with its documented five-port order (the full-circuit reachable cost stayed unchanged). Kept library reference compressor because ordering matches and kept custom final carry since its low-column OR is distinct from reference. The baseline `general.py` was saved and measured **before** directional trials. Full-stimulus raw outputs of handoff and `general.py` matched at all 1,050,624 inputs; this is empirical, not a formal equivalence proof. Graphs changed due to removal of buffers, so graph identity is not claimed. Weighted cost decreased 5.

## Directional trials

Tested removal of zero/G, omission of each compensation column, bit-six/seven rounding, sign-XOR factoring, low carry exactness, replacement of zero by input bits or G, and low-column zero ordering. Complete-circuit cost and EVM recorded as `<name>.cost.json` and `<name>.eval.json` alongside each standalone trial source. Removing zero (-54.68 dB), G (-55.70 dB), compensation columns (-29.56, -23.56, -11.51, +0.68 dB), or column-five G replacement (-57.09 dB) violates EVM. Column-four `b[0]` (-57.46 dB), `d[0]` (-57.56 dB), and duplicated G (-57.28 dB) also violate the threshold. Extra rounding at column 6 or 7 violates it (-52.50 and -47.42 dB). Explicit signed shared-XOR and low-carry exactness produced no savings. Raising either pruning cutoff without updating dependent deletion indexes failed construction and was not scored or selected. The genuinely useful directional change moves the existing zero-weighted slot to position one in column four before reference compression; the resulting change in compressor placement decreases weighted cost by 1 without altering output. Full-stimulus raw outputs matched `general.py` at all 1,050,624 inputs; again sample-based only. No truth-table synth plugin was available through the specified workspace command tools; no SAT result is claimed.

The final candidate is a Pareto tradeoff against the original parent: saves 21 cost units and one slot, while EVM is less negative by 0.464134 dB; strict EVM <-57.6 dB passes. The existing archive includes other cost/accuracy/slot tradeoffs, so no claim of dominance over the whole archive is made. The final source imports solely the shared tap2 module, exposes parameterless `build_circuit()`, retains genuine three-stage product/compression/output boundaries, uses the library reference compressor, and does not override gate costs. The tool's allowed MUX_XOR gate was retained.
