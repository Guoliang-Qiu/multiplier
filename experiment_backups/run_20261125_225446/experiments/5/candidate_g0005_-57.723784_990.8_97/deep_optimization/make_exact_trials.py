"""Generate exact compressor and output pairing variants of the general baseline."""
from pathlib import Path
p=Path('/home/guoliang/multiplier/experiments/5/candidate_g0005_0003/deep_optimization')
s=(p/'general_baseline.py').read_text()
for name, replacement in [('compress021','x0, x2, x1'),('compress120','x1, x2, x0'),('compress102','x1, x0, x2'),('compress201','x2, x0, x1')]:
    (p/(name+'.py')).write_text(s.replace('self._add3(x0, x1, x2)', 'self._add3('+replacement+')'))
for name, replacement in [('output021','bucket[0], carry, bucket[1]'),('output120','bucket[1], carry, bucket[0]'),('output102','bucket[1], bucket[0], carry')]:
    (p/(name+'.py')).write_text(s.replace('self._add3(bucket[0], bucket[1], carry)', 'self._add3('+replacement+')'))
