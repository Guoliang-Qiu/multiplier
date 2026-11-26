# Gate-level optimization record

All complete-circuit measurements use workspace `gate_cost.py` and `eval.py --stimulus-file /home/guoliang/multiplier/stimulus.npy`, 1,050,624 cases. Weighted costs retain the MUX_XOR fractional price. Column slots are counted before compression, including repeated terms and constants.

| Implementation | Cost | EVM dB | Pre-compression slots | MAE | RMSE | Maximum error |
|---|---:|---:|---:|---:|---:|---:|
| Immutable parent | 970.2 | -57.777069 | 93 | 0.263789 | 0.311736 | 0.875000 |
| Immutable handoff | 968.2 | -57.652772 | 92 | 0.266610 | 0.316229 | 0.960938 |
| General equivalence baseline | 965.2 | -57.652772 | 92 | 0.266610 | 0.316229 | 0.960938 |
| Final directional variant | 965.2 | -57.652772 | 91 | 0.266610 | 0.316229 | 0.960938 |

## General equivalence pass

Reviewed partial-product selectors and corrections, shared AND/XOR transformations, compressor majority and sum paths, and final output assembly. Three `self.add('OR', signal, zero)` compensation-buffer gates were replaced with their actual `signal` inputs, preserving their weighted column slots. The full-stimulus **raw 19-bit outputs agree bitwise** with the immutable handoff (0 mismatches); this is sample-based equivalence, not formal proof. The buffer identity itself is elementary Boolean equality. General-baseline `gate_cost.py` and `eval.py` outputs are saved in adjacent JSON files.

Other investigated rewrites: replacing the custom XOR mapping with the native XOR produced cost 977.2 and 352,672 raw mismatches because the established XOR-aware `_and` selector rewrite changes the construction; removing that `_and` rewrite produced cost 967.2 but 261,212 raw mismatches. Changing top-row XOR polarity preserved sampled outputs but raised cost to 1010.2. An alternate (supposedly exact) full-adder parity identity produced cost 897.2 but 963,908 mismatches; it is **not** a valid full adder. Factored majority had no cost effect. Symmetric `_add3` input permutations had no cost effect. These trials were not adopted.

## Directional pass

The pre-compression one-slot constant at column 18 is removed: the implemented output repeats bit 17 as bit 18, and the column-18 constant has no route to any bit 0..17. Full-stimulus raw comparison with the handoff yielded **zero mismatches**; cost remains 965.2, while honest slot count decreases to 91. This yields [965.2, -57.652772, 91] versus original parent's [970.2, -57.777069, 93]: lower cost and slots, with a small EVM tradeoff, below the strict -57.6 dB limit. It also strictly dominates the handoff in cost and slots at unchanged EVM. The archived 970.2/-57.777069/93 point remains a distinct accuracy/cost tradeoff.

For input-distribution screening, prescribed stimulus gives negative fractions b=0.74951 and d=0.25049, while a,c negative fractions are ~0.5; exact reference low-seven-bit residues 63 and 64 have observed rates 0.005839 and 0.011446, respectively. Deletion of the active weight-five G correction had cost 954.2, slots 91, but EVM -55.576319; replacing it by ONE had cost 955.2, EVM -56.841568. Deleting either tested weight-four/weight-five correction had EVM -55.102220/-55.351769. Adding rounding ONE to weight-six gave EVM -52.467392. Replacing the final adder's XOR by OR at bit 7, 9 or 10 cost 964.2 but yielded EVM -56.176620, -44.873097 or -41.883813, respectively. Replacing two additional Booth rows with MUX_XOR increased cost to 986.8. None of these complete-circuit approximations meets the strict EVM bound. Low-weight corrections control the Q4.7 rounding boundary; stronger truncation causes many boundary crossings, and higher-weight OR substitutions cause larger errors. Thus the feasible 91-slot variant is retained.

The installed kit was inspected: tap2 provides gate caching, primitives, `_fa`, `_ha`, `_add3`, and reference compressor/output assembly, and MUX_XOR port order is (a,b,c,d,e). Existing customized compression discards selected low sums and existing output assembly intentionally performs low-column OR and sign-bit replication; they cannot be replaced by reference stages without changing the circuit. No solver plugin was invoked: the supplied compensation G is already present, and the local gate optimization trials required no expensive small-cone exact synthesis.
