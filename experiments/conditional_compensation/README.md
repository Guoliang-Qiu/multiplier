# Conditional-compensation experiments

Experimental configurations, measurements and error tables belong here, outside
`circuit/`. The `experiment_1015_*` results were relocated unchanged; the
configuration's implementation path was adjusted for the new directory.
These results describe the original quantized-residual experiments.

## Direct-dependency validation

Run from the repository root:

```
TAP2_COPIES=8 OPENBLAS_NUM_THREADS=1 python experiments/conditional_compensation/validate_direct_dependency_x.py
```

Results: `direct_dependency_x_validation.json`. This diagnostic does not modify
the production node-set tool. It observes immediate parents even when deletion
makes them unreachable (unlike the production retained-X constraint).

On 1,050,624 cases, deleting slots (4,0) and (4,1), X=[89,90,153,154]:

- E[Var(removed weighted sum | X)] = 0 exactly.
- Unquantized original-error conditional variance = 0.03007614084815239.
- Synthetic linear deletion has exactly the same conditional variance; adding
  back D restores the original residual sample by sample.
- Actual deletion/recompression conditional variance = 0.061668148347184475.
- Actual raw delta differs from D on 693405 cases.
- Reinserting the removed entries at their original positions before compression
  restores the exact baseline graph and output IDs.
- Independent per-state two-pass variance agrees with the tool implementation.

For X=0, D=0, input (-153,-255,142,-254) gives baseline_raw=2944 and
deleted_raw=3008. Input (-80,-256,-254,-256), with the same X and D, gives
85504 in both circuits. Thus deleting zero-valued slots can change the output:
the candidate's approximate stages depend on the compressor scheduling.

The no-floor residuals use raw/128 units. Conditional variance is not raw MSE:
the baseline raw MSE is 0.10960981412473013, of which 0.07953367327657773
is the conditional-mean-square term. Quantized EVM is a separate metric.
