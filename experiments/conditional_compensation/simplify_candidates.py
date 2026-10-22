"""Flatten local inheritance and reuse library arithmetic; verify entire DAG.

Candidate-specific column edits are inlined in original order. No graph
serialization, external synthesis or cross-candidate dependencies are emitted.
"""
import ast
import copy
import importlib
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))


class Rename(ast.NodeTransformer):
    def __init__(self, mapping): self.mapping=mapping
    def visit_Name(self,n):
        return ast.copy_location(ast.Name(id=self.mapping.get(n.id,n.id),ctx=n.ctx),n)
    def visit_arg(self,n):
        n.arg=self.mapping.get(n.arg,n.arg)
        return n


def flatten(tree):
    methods={}; attrs={}
    for cls in [n for n in tree.body if isinstance(n,ast.ClassDef)]:
        for item in cls.body:
            if isinstance(item,ast.Assign):
                assert len(item.targets)==1 and isinstance(item.targets[0],ast.Name)
                attrs[item.targets[0].id]=copy.deepcopy(item)
            elif isinstance(item,ast.AnnAssign):
                attrs[item.target.id]=copy.deepcopy(item)
            elif isinstance(item,ast.FunctionDef):
                item=copy.deepcopy(item)
                if item.name in methods:
                    parent=methods[item.name]
                    # Overrides of product emitters have one initial super call,
                    # followed by slot edits. Inline parent rather than rename it.
                    if item.name in ('_product_columns','_one_product_columns'):
                        first=item.body[0]
                        assert isinstance(first,ast.Assign) and len(first.targets)==1
                        call=first.value
                        assert isinstance(call,ast.Call) and isinstance(call.func,ast.Attribute)
                        assert isinstance(call.func.value,ast.Call) and call.func.value.func.id=='super'
                        assert call.func.attr==item.name
                        assert isinstance(parent.body[-1],ast.Return)
                        assert isinstance(parent.body[-1].value,ast.Name)
                        mapping={a.arg:v.id for a,v in zip(parent.args.args[1:],call.args)}
                        # Parent Booth emitter uses locals named q/m/one that
                        # collide with override parameters. Alpha-rename them
                        # before inlining; argument binding must stay immutable.
                        parameters={a.arg for a in parent.args.args}
                        occupied={n.id for n in ast.walk(item) if isinstance(n,ast.Name)}
                        for local in {n.id for n in ast.walk(parent) if isinstance(n,ast.Name) and isinstance(n.ctx,ast.Store)}:
                            if local not in parameters and local in occupied:
                                target='generated_'+local
                                while target in occupied:target='generated_'+target
                                mapping[local]=target;occupied.add(target)
                        mapping[parent.body[-1].value.id]=first.targets[0].id
                        body=[Rename(mapping).visit(copy.deepcopy(n)) for n in parent.body[:-1]]
                        # Rename parent locals that would shadow override parameters
                        # is unnecessary in these emitters; graph verification guards it.
                        item.body=body+item.body[1:]
                methods[item.name]=item
    cls=ast.ClassDef(name='Candidate',bases=[ast.Name(id='MultiplierCircuit',ctx=ast.Load())],
                     keywords=[],body=list(attrs.values())+list(methods.values()),decorator_list=[])
    others=[n for n in tree.body if not isinstance(n,ast.ClassDef)]
    tree.body=[n for n in others if not (isinstance(n,ast.FunctionDef) and n.name=='build_circuit')]
    tree.body += [cls]+[n for n in others if isinstance(n,ast.FunctionDef) and n.name=='build_circuit']
    return tree


class ExactCalls(ast.NodeTransformer):
    def visit_Call(self,n):
        n=self.generic_visit(n)
        if isinstance(n.func,ast.Name) and n.func.id in ('_and','_or','_xor','_not','_add3','_full_adder'):
            name='_fa' if n.func.id=='_full_adder' else n.func.id
            obj=n.args[-1];args=n.args[:-1]
            if name=='_add3':args=args[:3]
            return ast.copy_location(ast.Call(func=ast.Attribute(value=obj,attr=name,ctx=ast.Load()),args=args,keywords=[]),n)
        return n


def simplify(text,exact):
    tree=flatten(ast.parse(text))
    cls=next(n for n in tree.body if isinstance(n,ast.ClassDef))
    if exact:
        remove={'_gate','_and','_or','_xor','_not','_add3','_full_adder'}
        tree.body=[n for n in tree.body if not (isinstance(n,ast.FunctionDef) and n.name in remove)]
        tree=ExactCalls().visit(tree)
        # The old free gate helper enabled absorption, independently of the
        # historical false class flag. Preserve that actual policy.
        for n in cls.body:
            if isinstance(n,ast.Assign) and n.targets[0].id=='_USE_ABSORPTION':n.value=ast.Constant(True)
        # Move remaining arithmetic-stage helpers into the sole Candidate.
        names={'_add_product','_compress','_outputs','_bit','_qsub'}
        funcs={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names}
        tree.body=[n for n in tree.body if not (isinstance(n,ast.FunctionDef) and n.name in names)]
        for name in ('_add_product','_compress','_outputs'):
            fn=funcs[name]
            args=[a for a in fn.args.args if a.arg!='circuit']
            fn.args.args=[ast.arg(arg='self')]+args
            fn=Rename({'circuit':'self'}).visit(fn)
            if name=='_compress':
                fn.name='_compress_columns';fn.args.args=[ast.arg(arg='self')]
                fn.body=ast.parse('columns = self._columns').body+fn.body
            elif name=='_outputs':
                fn.name='_build_outputs';fn.args.args=[ast.arg(arg='self')]
                fn.body=ast.parse('columns = self._columns').body+fn.body
            cls.body=[n for n in cls.body if not (isinstance(n,ast.FunctionDef) and n.name==fn.name)]
            cls.body.append(fn)
        class Bind(ast.NodeTransformer):
            def visit_Call(self,n):
                n=self.generic_visit(n)
                if isinstance(n.func,ast.Name) and n.func.id in names:
                    name=n.func.id
                    if name=='_add_product':n.args=n.args[:-1]
                    n.func=ast.Attribute(value=ast.Name(id='self',ctx=ast.Load()),attr=name,ctx=ast.Load())
                return n
        cls=Bind().visit(cls)
    # Remove useless return self in stage hooks, and simplify no-op branching.
    for fn in cls.body:
        if isinstance(fn,ast.FunctionDef) and fn.name in ('_build_outputs','_compress_columns'):
            if isinstance(fn.body[-1],ast.Return):fn.body.pop()
    tree.body[0]=ast.Expr(value=ast.Constant('Standalone three-stage candidate; generic arithmetic is inherited from tap2.'))
    return ast.unparse(ast.fix_missing_locations(tree))+'\n'


def graph(c):return (c.nodes,c.input_ids,c.output_ids)


def main():
    root=Path(__file__).resolve().parents[2];planned=[];report=[]
    for path in sorted((root/'initial_solutions').glob('*.py')):
        mod=importlib.import_module('multiplier.initial_solutions.'+path.stem)
        old=mod.build_circuit()
        text=simplify(path.read_text(),path.stem=='candidate_exact_rounding_optimized')
        ns={'__name__':'standalone_test'};exec(compile(text,str(path),'exec'),ns)
        new=ns['build_circuit']()
        assert graph(old)==graph(new),path
        assert old.gatecost()==new.gatecost(),path
        planned.append((path,text))
        report.append(dict(file=path.name,cost=new.gatecost().total,graph_identical=True,
                           before_lines=len(path.read_text().splitlines()),after_lines=len(text.splitlines())))
        print(report[-1],flush=True)
    # Commit text replacements only after every proposed candidate verifies.
    for path,text in planned:path.write_text(text)
    Path(__file__).with_suffix('.json').write_text(json.dumps(report,indent=2))


if __name__=='__main__':main()
