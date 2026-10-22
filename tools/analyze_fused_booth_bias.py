"""Distribution screen for exact fused-Booth carry nodes."""
from multiplier.initial_solutions import candidate_exact_fused_booth_probe as m
from collections import Counter


def deps(c,n,memo):
 if n in memo:return memo[n]
 x=c.nodes[n];r={c.input_ids.index(n)} if x.kind.startswith('IN_') else set() if x.kind in ('ZERO','ONE') else set().union(*(deps(c,i,memo) for i in x.inputs));memo[n]=r;return r


def main():
 c,cols=m.build_partial_product_layout(); memo={}
 for k,b in enumerate(cols):
  for n in b:
   if c.nodes[n].kind!='AND':continue
   ds=sorted(deps(c,n,memo)); hist=Counter()
   for mask in range(1<<len(ds)):
    vals={x:(mask>>i)&1 for i,x in enumerate(ds)}
    def ev(q,cache):
     if q in cache:return cache[q]
     x=c.nodes[q]
     if x.kind.startswith('IN_'):v=vals[c.input_ids.index(q)]
     elif x.kind=='ZERO':v=0
     elif x.kind=='ONE':v=1
     elif x.kind=='NOT':v=1-ev(x.inputs[0],cache)
     else:
      a=ev(x.inputs[0],cache);b=ev(x.inputs[1],cache);v=a&b if x.kind=='AND' else a|b if x.kind=='OR' else a^b
     cache[q]=v;return v
    hist[ev(n,{})]+=1
   p=hist[1]/sum(hist.values()); print(dict(column=k,node=n,deps=len(ds),p1=p,zero_mismatch=p,one_mismatch=1-p))


if __name__=='__main__':main()
