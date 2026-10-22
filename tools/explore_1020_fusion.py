"""Source-level adder alternatives and exact AB/CD column regrouping probes.

No synthesis engine: each cell preserves sum+2*carry for all inputs.
Speculative gates/caches are rolled back before trying the next alternative.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from collections import Counter
from itertools import permutations
import json
import numpy as np
from multiplier.initial_solutions.candidate_dist_recoded1020 import Candidate as Parent


class Candidate(Parent):
    choose_cells = False
    normalize = False
    cell_records = None

    def _fa(self, a, b, cin):
        if not self.choose_cells:
            return super()._fa(a,b,cin)
        start = len(self.nodes)
        cache = self._gate_cache.copy()
        best = None
        # Equivalent majority/parity networks with differing sharing/polarity.
        for mode in range(3):
            for order in permutations((a,b,cin)):
                self.nodes[start:] = []
                self._gate_cache = cache.copy()
                x,y,z = order
                if mode == 0:
                    result = super()._fa(x,y,z)
                elif mode == 1:
                    s,c = super()._fa(self._not(x),self._not(y),self._not(z))
                    result = self._not(s), self._not(c)
                else:
                    both = self._and(x,y)
                    either = self._or(x,y)
                    parity = self._and(either,self._not(both))
                    result = self._xor(parity,z), self._or(both,self._and(either,z))
                used=set(); stack=list(result)
                while stack:
                    n=stack.pop()
                    if n<start or n in used:continue
                    used.add(n);stack.extend(self.nodes[n].inputs)
                cost=sum(self.components.require(self.nodes[n].kind).gate_cost for n in used)
                if best is None or cost<best[0]:
                    best=(cost,list(self.nodes[start:]),self._gate_cache.copy(),result,mode)
        self.nodes[start:]=best[1]
        self._gate_cache=best[2]
        if self.cell_records is not None:self.cell_records.append((a,b,cin,*best[3],best[4]))
        return best[3]

    def _build_circuit(self, layout_only=False, columns=None):
        if not self.normalize:
            return super()._build_circuit(layout_only=layout_only,columns=columns)
        # Build the layout on a separate instance: never initialize self twice.
        layout, buckets=Parent()._build_circuit(layout_only=True)
        buckets=[list(b) for b in buckets]
        for k in range(len(buckets)):
            counts=Counter(n for n in buckets[k] if n!=layout._zero)
            for n in list(counts):
                node=layout.nodes[n]
                if node.kind=='NOT':
                    other=node.inputs[0];pairs=min(counts[n],counts[other])
                    counts[n]-=pairs;counts[other]-=pairs;counts[layout._one]+=pairs
            buckets[k]=[n for n,count in counts.items() if count%2]
            if k+1<len(buckets):
                buckets[k+1].extend(n for n,count in counts.items() for _ in range(count//2))
        return super()._build_circuit(layout_only=layout_only,columns=buckets)


def main():
    rng=np.random.default_rng(102010)
    inputs=rng.integers(-256,256,(16384,4)).tolist()
    edge=(-256,-255,-128,-1,0,1,127,254,255)
    inputs += [[a,b,c,d] for a in edge for b in edge for c in edge for d in edge]
    reference=Parent()._build_circuit()
    expected=reference.simulate_many(inputs)
    rows=[]
    for choose,normalize in ((False,False),(True,False),(False,True),(True,True)):
        c=Candidate();c.choose_cells=choose;c.normalize=normalize;c.cell_records=[]
        c=c._build_circuit()
        actual=c.simulate_many(inputs)
        row=dict(choose_cells=choose,normalize=normalize,cost=c.gatecost().total,
                 cases=len(inputs),mismatches=sum(a!=b for a,b in zip(actual,expected)),
                 selected_modes=dict(Counter(r[-1] for r in c.cell_records)))
        rows.append(row);print(json.dumps(row),flush=True)
    Path('/tmp/opencode/explore1020.json').write_text(json.dumps(rows,indent=2))


if __name__=='__main__':main()
