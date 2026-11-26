import importlib.util,json,numpy as np
from pathlib import Path
from tools.circuit_kit.circuit.multiplier.conditional_compensation.node_set_information import build_experiment
from tools.circuit_kit.circuit.multiplier.conditional_compensation.synthesize import error_budget
root=Path('/home/guoliang/multiplier/experiments/1/candidate_g0001_0003')
spec=importlib.util.spec_from_file_location('trial_parent',root/'parent.py'); module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
for name in ['col4_strong','col4_compact','col4_shared','col5_compact','col5_strong','pair_sparse','col4_single','col4_other','col4_weak','col4_triple']:
 d=root/name;cfg=json.loads((d/'screen.json').read_text());base,deleted,layout,_=build_experiment(module.Candidate,cfg['removed_slots']);print(name,'saved_cost',base.gatecost().total-deleted.gatecost().total,'removed',[(col,pos,layout[col][pos]) for col,pos in cfg['removed_slots']]);
 if (d/'table.npy').exists():
  meta=json.loads((d/'table.json').read_text());table=np.load(d/'table.npy');budget=error_budget(meta,-57.7);print(' table min/budget',int(table.min(axis=1).sum()),budget,'best',table.argmin(axis=1).tolist(),'zero',int(table[:,0].sum()))
