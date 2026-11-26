# Deep optimization report

All measurements use workspace `gate_cost.py` and full `eval.py --stimulus-file /home/guoliang/multiplier/stimulus.npy` (1,050,624 external cases); cost is output-reachable weighted gate cost. Inputs/bus order and three construction stages remain unchanged.

| Circuit | Cost | EVM dB | Precompression slots |
|---|---:|---:|---:|
| immutable original parent | 1067 | -58.2916177846 | 100 |
| immutable handoff | 1048 | -57.9142162739 | 99 |
| first equivalence baseline (`general_baseline.py`) | 1043 | -57.9142162739 | 99 |
| **final equivalence baseline (`general_buffers.py`)** | **1039** | **-57.9142162739** | **99** |
| optional directional +ONE column 3 | 1027 | -57.6022162099 | 100 |

## General-equivalence pass (performed first)

Inspected all three stages: row partial-product expressions, hardcoded G corrections, constant-aware 3:2 compression (including customized low-column compressor), and output carry/signed-output wiring. Removed a redundant branch choosing identical column-2 layouts and dead G inputs 152/568 in the final correction; replaced an `OR(ONE,ZERO)` with `ONE`. Subsequently eliminated four `OR(observation,ZERO)` insertion buffers in earlier G corrections (keeping the real partial-product columns and observation node numbering stable). The final baseline saves 9 weighted cost versus handoff, with unchanged 99 slots, unchanged full EVM, and **zero mismatched raw output bits** against the handoff on all 1,050,624 configured samples. This is sample-based equivalence, not a formal proof. The local `OR(x,ZERO)=x`, double-NOT, and dead-variable rewrites are Boolean identities.

Other equivalence experiments: replacing `_xor` with native XOR everywhere cost 1040 but changed behavior because hardcoded node-index observations shifted, giving EVM -56.8972 (not equivalent, rejected); native XOR confined to compression/output maintained EVM but cost 1049 (rejected). Sorting compressor inputs to prioritize constants kept cost 1043, EVM unchanged (no gain). Rewriting low-column compressor XOR as half-adder logic also kept cost 1043 (no gain). No exact synthesis plugin is available from this session's exposed tools; the local Boolean identities needed no SAT result.

## Directional pass (after equivalence baseline was saved)

External-stimulus precompression signal rates: column 10 slot 9 (node 680) 1.566%, column 10 slot 4 (node 346) 10.941%, column 4 slot 2 (node 707) 12.535%, column 3 slot 1 (node 706) 25.057%. Although rare, dropping 680 or 346 yields EVM -47.2856 or -39.1899 respectively because their high column weights and carry impact dominate. Dropping node 707 yields EVM -54.7921; paired removal of 680 and 707 yields -47.0224, and removal of both high-column bits yields -38.3521. All violate the -57.6 dB constraint. Statistical frequency alone therefore fails as a gate-level optimization proxy.

Tested constant compensation: add ONE in column 3 costs 1027 and yields EVM -57.6022162, just passes the strict EVM limit, but its 0.0022 dB margin is fragile and it trades an additional partial-product slot and degraded EVM for 12 units of cost versus the general baseline. The general baseline offers better EVM and fewer slots at cost 1039, so it is retained as the robust eligible improvement over the parent. ONE in columns 5 and 6 yields EVM -55.4947 and -52.0940; replacing the column-4 ONE with ZERO gives -57.4009; all fail the constraint. These trials used complete circuit construction and workspace evaluators, not proxy scores.

Final installed delivery candidate: `generations/1/candidate_g0001_0005.py`, from `general_buffers.py`; final rerun yielded weighted cost 1039, EVM -57.9142162739 dB, slots 99. Compared with original parent: -28 cost, -1 slot, +0.3774015 dB worse EVM; this is an eligible Pareto tradeoff and improves handoff cost with identical measured EVM and slots. Circuit imports directly from the installed tap2 library and zero-argument `build_circuit()` succeeds as tested by both workspace evaluators. Immutable snapshots remained untouched.
