"""Build targeted directional trials based on external stimulus activation."""
from pathlib import Path
p=Path('/home/guoliang/multiplier/experiments/5/candidate_g0005_0003/deep_optimization')
s=(p/'general_baseline.py').read_text()
anchor='        columns[5].append(deleted_first_product_bit)\n        return columns'
variants={
'remove_zero4':'        columns[5].append(deleted_first_product_bit)\n        columns[4].pop()\n        return columns',
'remove_reuse5':'        columns[5].append(deleted_first_product_bit)\n        columns[5].pop()\n        return columns',
'remove_low3first':'        columns[5].append(deleted_first_product_bit)\n        del columns[3][0]\n        return columns',
'remove_low3second':'        columns[5].append(deleted_first_product_bit)\n        del columns[3][1]\n        return columns',
'remove_low4first':'        columns[5].append(deleted_first_product_bit)\n        del columns[4][0]\n        return columns',
'remove_low4second':'        columns[5].append(deleted_first_product_bit)\n        del columns[4][1]\n        return columns',
'comp_add4':'        columns[5].append(deleted_first_product_bit)\n        columns[4].append(one)\n        return columns',
'comp_add5':'        columns[5].append(deleted_first_product_bit)\n        columns[5].append(one)\n        return columns',
'comp_add6':'        columns[5].append(deleted_first_product_bit)\n        columns[6].append(one)\n        return columns',
'remove_col5last':'        columns[5].append(deleted_first_product_bit)\n        del columns[5][-2]\n        return columns',
'remove_col6last':'        columns[5].append(deleted_first_product_bit)\n        del columns[6][-1]\n        return columns',
'remove_col10rare':'        columns[5].append(deleted_first_product_bit)\n        del columns[10][9]\n        return columns',
}
assert s.count(anchor)==1
for name,new in variants.items():
    (p/(name+'.py')).write_text(s.replace(anchor,new))
