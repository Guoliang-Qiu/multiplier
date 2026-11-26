"""Explore exact compressor and output-assembly operand scheduling."""
from pathlib import Path
root=Path(__file__).parent
s=(root.parent/'partial_product_candidate.py').read_text()
for perm in ('x1, x2, x0','x2, x0, x1','x0, x2, x1'):
 name=perm.replace(', ','_')
 (root/('schedule_'+name+'.py')).write_text(s.replace('self._add3(x0, x1, x2)',f'self._add3({perm})'))
for perm in ('carry, bucket[0], bucket[1]','bucket[1], carry, bucket[0]','bucket[1], bucket[0], carry'):
 name=perm.replace(', ','_').replace('[','').replace(']','')
 (root/('output_'+name+'.py')).write_text(s.replace('self._add3(bucket[0], bucket[1], carry)',f'self._add3({perm})'))
