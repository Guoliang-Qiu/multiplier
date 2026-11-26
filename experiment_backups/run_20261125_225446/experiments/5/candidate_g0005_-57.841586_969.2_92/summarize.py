import json
from pathlib import Path
r=Path('/home/guoliang/multiplier/experiments/5/candidate_g0005_0004')
records=[]
for p in sorted(r.glob('s*/')):
 screen=p/'screen_result.json'
 if not screen.exists():continue
 cfg=json.loads((p/'table_config.json').read_text())
 synth=p/('synthesis_small.json' if p.name=='s41_42_compact' else 'synthesis.json')
 s=json.loads(synth.read_text()) if synth.exists() else {}
 cost=json.loads((p/'cost.json').read_text()) if (p/'cost.json').exists() else {}
 perf=json.loads((p/'eval.json').read_text()) if (p/'eval.json').exists() else {}
 records.append({'trial':p.name,'removed_slots':cfg['removed_slots'],'node_ids':cfg['node_ids'],
 'compensation_columns':cfg['compensation_columns'],
 'remaining_variance':json.loads(screen.read_text())['remaining_variance'],
 'synthesis_status':s.get('status','not attempted'),'G_cost':s.get('weighted_cost'),
 'complete_cost':cost.get('gate_cost'),'complete_evm_db':perf.get('evm_db'),
 'complete_partial_product_count':cost.get('partial_product_count')})
archive=json.loads(Path('/home/guoliang/multiplier/generations/pareto_archive/archive.json').read_text())['records']
selected=[969.2,-57.84158629896105,92]
report={'baseline':{'gate_cost':973.2,'evm_db':-57.852453944355204,'partial_product_count':92},
 'selected':'s41_compact','selected_pareto_dominators':[v['objectives'] for v in archive if all(a<=b for a,b in zip(v['objectives'],selected))],
 'archive_size':len(archive),'trials':records,
 'notes':'Seven-gate paired trial interrupted in foreground after 120 s; two-gate retry sat. Two-slot single-output trial unsat from exact table lower bound for its chosen observations. Unmeasured costs remain unknown.'}
(r/'search_summary.json').write_text(json.dumps(report,indent=2)+'\n')
