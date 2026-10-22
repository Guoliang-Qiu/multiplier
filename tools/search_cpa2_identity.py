"""Check two-bit CPA lookahead formulas against the 1065 tail."""
from itertools import product


def main():
    # p_i=x_i xor y_i, g_i=x_i&y_i; C2=g1 | p1&g0 | p1&p0&C0.
    for x0,x1,y0,y1,c0 in product((0,1),repeat=5):
        p0=x0^y0;p1=x1^y1;g0=x0&y0;g1=x1&y1
        c1=g0|(p0&c0)
        c2=g1|(p1&g0)|(p1&p0&c0)
        s0=p0^c0;s1=p1^c1
        assert x0+y0+c0+2*(x1+y1) == s0+2*s1+4*c2
    print('two-bit CPA identity exhaustive: 32/32')


if __name__=='__main__':main()
