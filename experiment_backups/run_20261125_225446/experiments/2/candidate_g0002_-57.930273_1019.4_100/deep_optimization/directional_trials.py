"""Directional approximation trials based on verified general-pass baseline."""
from pathlib import Path
root = Path(__file__).resolve().parent
base = (root/'general_baseline.py').read_text()
variants = {}
# Remove a single additional low-weight weighted slot without concealing column count.
for column, slot in ((3,0),(3,1),(4,0),(4,1),(4,2),(4,3),(4,4),(5,0),(5,1),(6,0)):
    variants[f'remove_{column}_{slot}'] = base.replace('        # X refers to nodes in the original pre-compression prefix.', f'        del columns[{column}][{slot}]\n        # X refers to nodes in the original pre-compression prefix.')
for col in (3, 5, 6, 7):
    variants[f'round_{col}'] = base.replace('        # X refers to nodes in the original pre-compression prefix.',f'        columns[{col}].append(one)\n        # X refers to nodes in the original pre-compression prefix.')
# Cross-layer: the sign-extended Booth high bit is shared by two digit choices.
# The general pass already factors it, so preserve its mapping while testing the
# compressor's special low-column realization against the reference realization.
variants['reference_lowcompress'] = base.replace('if col == 3 and compressor_index <= 1:', 'if False:')
variants['restore_first'] = base.replace('        del columns[4][4]\n        del columns[4][1]', '        del columns[4][1]')
variants['restore_second'] = base.replace('        del columns[4][4]\n        del columns[4][1]', '        del columns[4][4]')
variants['restore_both'] = base.replace('        del columns[4][4]\n        del columns[4][1]', '')
variants['remove_comp_10'] = base.replace('COMP_COLS = (10, 11, 13, 15, 18)', 'COMP_COLS = (11, 13, 15, 18)')
variants['add_comp_4'] = base.replace('COMP_COLS = (10, 11, 13, 15, 18)', 'COMP_COLS = (4, 10, 11, 13, 15, 18)')
for name, text in variants.items():
    (root/(name+'.py')).write_text(text)
