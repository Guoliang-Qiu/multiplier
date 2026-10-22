# Equal-flow synthesis comparison

All rows were passed through the same native ABC/AIG flow:

```text
two rounds; each round: resyn2, resub, dc2, rewrite
accept only strict weighted-cost decreases
AND cost = 1, NOT cost = 0
```

The complete default evaluator was then run on every normalized netlist.

| source | raw cost | normalized cost | EVM (dB) |
|---|---:|---:|---:|
| `initial_solutions/candidate_g0000_0001.py` | 999 | **961** | -57.615905464558 |
| `initial_solutions/candidate_g0000_0002.py` | 1005 | **969** | -57.642343733513 |
| `temp_solutions/candidate_pareto_1009.py` | 1009 | **973** | -57.708456420645 |
| `temp_solutions/candidate_pareto_1011.py` | 1011 | **975** | -57.745244789076 |
| `initial_solutions/candidate_g0001_0000.py` | 1037 | 999 | -58.183306827190 |

This corrects the earlier unfair comparison. The 999-cost baseline also
improves to 961 under exactly the same equivalence-preserving synthesis flow,
so the 973/975 results do not dominate that baseline. They remain new Pareto
tradeoff points among the ten uniformly synthesized initial solutions and the
two new candidates: their EVM is better, but their cost is higher than 961.

The strict target under this synthesis protocol is therefore:
`cost < 961` and `evm_db < -57.61590546455796`. It has **not** been reached.

Raw logs and equivalence proofs are in `generations/9/`. The machine-readable
report is `generations/9/fair_comparison.json`; the full twelve-row table is
`generations/9/fair_comparison.md`. All references are relative to the project
root. These are equal-effort heuristic results, not minimum-cost proofs.
