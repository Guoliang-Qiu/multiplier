"""Exact gate conditioning by literals implied by an existing control.

For x AND f, x=1 can be assumed inside f. For x OR f, x=0 can
be assumed inside f. Conjunction/disjunction controls imply additional
literal values. No external synthesis or empirical don't-cares are used.
"""
from multiplier.experiments.conditional_compensation import candidate_x_reuse as source
from multiplier.candidate_support.staged import StagedCandidate


class Rewriter(StagedCandidate):
    _USE_ABSORPTION = True
    depth = 4

    def facts(self, n, value, result, depth=3):
        result[n] = value
        if depth == 0:
            return
        node = self.nodes[n]
        if node.kind == 'NOT':
            self.facts(node.inputs[0], 1-value, result, depth-1)
        elif (node.kind == 'AND' and value == 1) or (node.kind == 'OR' and value == 0):
            for child in node.inputs:
                self.facts(child, value, result, depth-1)

    def restrict(self, n, facts, depth):
        if n in facts:
            return self._one if facts[n] else self._zero
        node = self.nodes[n]
        if depth == 0 or not node.inputs:
            return n
        args = tuple(self.restrict(j,facts,depth-1) for j in node.inputs)
        if args == node.inputs:
            return n
        return super()._gate(node.kind,*args)

    def _gate(self, kind, *inputs, absorption=False):
        if kind in ('AND','OR'):
            for control, expression in (inputs,inputs[::-1]):
                facts = {}
                self.facts(control,int(kind=='AND'),facts)
                reduced = self.restrict(expression,facts,self.depth)
                if reduced != expression:
                    return super()._gate(kind,control,reduced)
        return super()._gate(kind,*inputs,absorption=absorption)

    def _product_columns(self,a,b,c,d,zero,one):
        raise NotImplementedError('Rewriter uses the source graph')

    def _compress_columns(self):
        raise NotImplementedError

    def _build_outputs(self):
        raise NotImplementedError


def build_variant(depth=4, prefix_only=True):
    old=source.build_circuit(); new=Rewriter(); new.depth=depth; mapping={}
    layout=source.Candidate()
    layout._product_columns(*layout.setup())
    prefix=len(layout.nodes)
    for i,node in enumerate(old.nodes):
        if not node.inputs:
            n=new.add(node.kind)
            if node.kind=='ZERO':new._zero=n
            if node.kind=='ONE':new._one=n
        else:
            args=tuple(mapping[j] for j in node.inputs)
            if prefix_only and i>=prefix:
                n=StagedCandidate._gate(new,node.kind,*args)
            else:
                n=new._gate(node.kind,*args)
        mapping[i]=n
    new.input_ids=[mapping[n] for n in old.input_ids]
    new.output_ids=[mapping[n] for n in old.output_ids]
    return new


def build_circuit():
    return build_variant(4)
