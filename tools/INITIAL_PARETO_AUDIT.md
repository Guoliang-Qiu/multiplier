# Current initial-solutions Pareto frontier

All values remeasured after migration to the current three-stage MultiplierCircuit.
`TAP2_COPIES=8`, `OPENBLAS_NUM_THREADS=1`, seed 42; 1,050,624 cases per candidate.
Lower weighted cost and more negative EVM are better. Equal points are deduplicated.

| Candidate | Gate cost | EVM dB |
|---|---:|---:|
| `candidate_g0000_0001.py` | 1000 | -57.615905465 |
| `candidate_g0000_0002.py` | 1005 | -57.642343734 |
| `candidate_dist_1020_to1010.py` | 1010 | -57.768091087 |
| `candidate_dist_1015_probe1014.py` | 1014 | -57.845339958 |
| `candidate_dist_1020_to1015.py` | 1015 | -57.928584136 |
| `candidate_dist_recoded1020.py` | 1020 | -58.062793358 |
| `candidate_dist_recoded1025.py` | 1025 | -58.168466039 |
| `candidate_g0001_0000.py` | 1037 | -58.183306827 |
| `candidate_g0001_0005_joint1060.py` | 1060 | -58.239899776 |
| `candidate_g0001_0001.py` | 1064 | -58.264840287 |
| `candidate_g0001_0005_joint1072.py` | 1072 | -58.349556201 |
| `candidate_g0001_0005_col2_joint_asym.py` | 1084 | -58.382742434 |
| `candidate_g0001_0004.py` | 1111 | -58.416063321 |
| `candidate_g0001_0005.py` | 1114 | -58.423129084 |
| `candidate_exact_rounding_optimized.py` | 1289 | -58.442285723 |

The JSON audit retains full measurements and dominators of removed candidates.
Candidate layouts use the joint `_product_columns(a,b,c,d,zero,one)` interface;
compression and output construction are separate `_compress_columns()` / `_build_outputs()` stages.
`candidate_support/staged.py` preserves the former absorption policy and layout helpers.
`finish_columns(circuit, columns)` reuses the supplied layout instance, never a second setup.
