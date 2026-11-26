"""Screen column-by-column cheap approximate majority compressors."""
from pathlib import Path
import subprocess,sys,json
here=Path(__file__).resolve().parent
base=(here/'maj_col4.py').read_text();root=Path('/home/guoliang/multiplier')
for col in range(6,18):
    text=base.replace('MAJ_COLS = (0, 1, 2, 3, 4)',f'MAJ_COLS = (0, 1, 2, 3, 4, {col})')
    p=here/(f'maj_col{col}.py');p.write_text(text)
    cost=subprocess.run([sys.executable,str(root/'gate_cost.py'),str(p)],capture_output=True,text=True)
    if cost.returncode:print(col,'cost failed',cost.stderr[-250:],flush=True);continue
    data=json.loads(cost.stdout)
    print(col,'cost',data['gate_cost'],data['partial_product_count'],flush=True)
    if data['gate_cost'] >= 970.2:continue
    result=subprocess.run([sys.executable,str(root/'eval.py'),str(p),'--stimulus-file',str(root/'stimulus.npy')],capture_output=True,text=True)
    print(col,'EVM',json.loads(result.stdout)['evm_db'] if result.returncode==0 else result.stderr[-250:],flush=True)
