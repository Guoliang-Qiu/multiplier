"""Record measured full-circuit tradeoffs and architecture decision.

Parent A: cost 1019.4, EVM -57.9302733896, slots 100.
Parent B: cost 976.2, EVM -57.7242379993, slots 92.
B backbone with primitive-only MUX expansion: 1005, -57.7242379993, 92.
Fused wider Booth-cell realization from A: 1056, -57.7242379993, 92;
  rejected because no cost/accuracy gain. Hybrid cut (A cut=2, B cut=4):
  1024, -57.7066936582, 96; rejected as dominated by B.
Optimized exact Booth-cell factoring: 985, -57.7242379993, 92;
  raw outputs equal B's primitive-only version on all 1,050,624 stimuli.
Optimized G=OR(d1, AND(d0,c4)): 983, -57.6650947760, 92;
  selected: 2 cost improvement over equivalent generic-cell realization,
  strict EVM < -57.6. This is a Pareto alternative to the parent B:
  parent B is cheaper if its MUX_XOR cell is permitted (976.2), but the
  current task explicitly requires only AND/OR/XOR/NOT.

Other changes tested: extended approximate carry-only compressor in col 5:
  cost 981, EVM -54.6004596671 (ineligible). Dropping a col-4 slot:
  cost 969, EVM -55.3276473937 (ineligible). Changing output OR carry
  through col 7: cost 984, EVM -56.0089533982 (ineligible).
Parent A's extra compensation in col 18 is output-dead but still costs
one column slot, so it was not transferred. Parent A's low-column cut=2
was not transferred since hybrid cut costs more without improving EVM.
No whole-circuit synthesis was used; small-cone exact synth plugin unavailable
in the current environment, so all rewrites were evaluated by gate_cost.py
and eval.py on the configured stimulus.npy.
"""
