"""Construct and screen actual compressor replacements, preserving descendants."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import numpy as np
from multiplier.initial_solutions import candidate_g0001_0005 as base


class Probe(base.Candidate):
    targets = ()

    def __init__(self):
        super().__init__()
        self.call_index = 0

    def _add3(self, a, b, c):
        index = self.call_index
        self.call_index += 1
        if index not in self.targets:
            return super()._add3(a, b, c)
        # Joint arithmetic encoding differs from a+b+c only on 111:
        # sum'=OR(a,b,c)&~majority(a,b,c), carry'=majority(a,b,c).
        either = self._or(a, b)
        carry = self._or(self._and(a, b), self._and(either, c))
        total = self._and(self._or(either, c), self._not(carry))
        return total, carry


def main():
    x = np.random.default_rng(213).integers(-256,256,(4096,4),dtype=np.int64)
    ref = (x[:,0]*x[:,1]+x[:,2]*x[:,3])/128
    power = np.mean(ref**2)
    def measure(c):
        raw = np.asarray(c.simulate_many(x.tolist()))
        return float(10*np.log10(np.mean((np.floor(raw/128+.5)-ref)**2)/power))
    print('baseline', measure(base.build_circuit()), flush=True)
    rows=[]
    for i in range(20):
        c=Probe(); c.targets=(i,); c=c._build_circuit()
        evm=measure(c); cost=c.gatecost().total
        rows.append((evm,cost,i))
    for r in sorted(rows):print(r,flush=True)


if __name__=='__main__': main()
