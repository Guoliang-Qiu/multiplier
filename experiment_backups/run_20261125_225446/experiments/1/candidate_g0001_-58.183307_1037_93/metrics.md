# Candidate g0001_0006 search record

Full `gate_cost.py` and `eval.py --stimulus-file /home/guoliang/multiplier/stimulus.npy` measurements, objectives [cost, EVM dB, pre-compression slots]:

| circuit | cost | EVM dB | slots | assessment |
|---|---:|---:|---:|---|
| parent A | 1026.8 | -57.8261811914 | 99 | eligible; column-3 approximate compressor, extra bit-4 deletion, b[0] compensation |
| parent B | 1010.6 | -58.1833068272 | 93 | eligible; asymmetric pruning, G compensation, MUX_XOR rows |
| fused direct low-column deletion (`fused_drop.py`) | 1047 | -55.6498806832 | 91 | rejected: low-column loss exceeds EVM cap |
| gate-shared fusion (`shared_drop.py`) | 1017 | -55.6498806832 | 91 | rejected: optimized gate cost but unacceptable EVM |
| parent-A b[0] compensation (`shared_bit.py`) | 1041 | -58.0509000618 | 93 | eligible but dominated by parent B |
| shared signed-row gate rewrite (`shared_row.py`) | 1037 | -58.1833068272 | 93 | eligible, sample raw outputs match parent B |
| selective Booth sign logic (`sign_qsub.py`) | 1037 | -58.1833068272 | 93 | eligible; six native XOR cells, remaining gates AND/OR/NOT |
| final `candidate_g0001_0006.py` | 1037 | -58.1833068272 | 93 | graph/output/cost identical to sign_qsub after helper consolidation |

Parent B is the Pareto-best measured source but uses forbidden MUX_XOR, so final keeps its coherent asymmetric truncation and compensation backbone while incorporating parent A's shared AND/OR parity style only where it fits. The substituted signed Booth-row cones cost 1037 rather than 1067 for individually decomposed MUX_XOR cells (`fused0.py`), a 30-gate deep-optimization saving. Full sample-based bitwise raw-output equality (1,050,624 external stimulus rows) was checked against parent B for the gate-shared trial; this is **not** a formal proof. Parent A's stronger truncation/approximation cannot simply be grafted onto B, because the compressor LIFO ordering changes and eligible EVM fails. Selective compensation removal, low-column truncation and output carry simplification were screened; those measured with eval violated the hard EVM cap. No synthesis tool was available in the configured specialized tool list of this session.
