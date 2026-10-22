# Mixed Booth synthesis probe

The exact synthesizer was run on the signed radix-8 window
`(q[i+2], q[i+1], q[i], q[i-1])` with digit
`-4*q[i+2] + 2*q[i+1] + q[i] + q[i-1]`.

The independent one-hot output minimums found by the tool were:

| output | minimum gates |
|---|---:|
| negative | 4 |
| magnitude 1 | 4 |
| magnitude 2 | 3 |
| magnitude 3 | 3 |
| magnitude 4 | 5 (within the tested bound) |

The five-output shared problem reached a timeout at the 9-gate bound. These
functions are therefore not a drop-in win over the existing radix-4 selector:
the complete radix-8 row still needs magnitude generation, sign inversion,
and correction injection. The next useful synthesis target is the low-slice
carry function only, with multiplicand bits included as inputs.
