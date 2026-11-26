"""Generate focused exact Boolean factoring gate trials."""
from pathlib import Path
p=Path(__file__).parent
s=(p.parent/'partial_product_candidate.py').read_text()
old='        return super()._gate(kind, *inputs, absorption=absorption or self._USE_ABSORPTION)'
variants={
 'common': '''        if kind in ('OR', 'AND') and len(inputs) == 2:
            a, b = inputs
            inner = 'AND' if kind == 'OR' else 'OR'
            an, bn = self.nodes[a], self.nodes[b]
            if an.kind == bn.kind == inner:
                common = set(an.inputs) & set(bn.inputs)
                if common:
                    shared = next(iter(common))
                    left = next(x for x in an.inputs if x != shared)
                    right = next(x for x in bn.inputs if x != shared)
                    combined = super()._gate(kind, left, right, absorption=True)
                    return super()._gate(inner, shared, combined, absorption=True)
''',
 'demorgan': '''        if kind in ('OR', 'AND') and len(inputs) == 2:
            a, b = inputs
            if self.nodes[a].kind == self.nodes[b].kind == 'NOT':
                opposite = 'AND' if kind == 'OR' else 'OR'
                inner = super()._gate(opposite, self.nodes[a].inputs[0], self.nodes[b].inputs[0], absorption=True)
                return self._not(inner)
''',
 'complement': '''        if kind in ('OR', 'AND') and len(inputs) == 2:
            a, b = inputs
            inner = 'AND' if kind == 'OR' else 'OR'
            for first, second in ((a,b),(b,a)):
                node = self.nodes[second]
                if node.kind != inner: continue
                for factor in node.inputs:
                    fn = self.nodes[factor]
                    if fn.kind == 'NOT' and fn.inputs[0] == first:
                        other = next(x for x in node.inputs if x != factor)
                        return super()._gate(kind, first, other, absorption=True) if kind == 'OR' else super()._gate(kind, first, other, absorption=True)
''',
}
# complement identity: a | (~a & b)=a|b; a & (~a | b)=a&b
for name, code in variants.items():
 (p/(name+'.py')).write_text(s.replace(old, code+old))
