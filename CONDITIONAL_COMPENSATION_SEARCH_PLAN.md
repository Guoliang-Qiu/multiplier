# Conditional Compensation Search: Current Algorithm Understanding

## 1. Objective

The goal is to find a multiplier candidate that simultaneously satisfies:

```text
EVM < -57.61590546455796 dB
nonconstant partial-product count < 88
```

The successful replacements started from
`initial_solutions/candidate_-58.183307_1006.py`: 88 nonconstant
pre-compression slots, gate cost 1006, EVM -58.18330682718984 dB. Its accuracy
margin permits a simpler approximate low-column compressor while remaining
better than the `candidate_g0000_0001.py` reference (-57.61590546455796 dB,
88 nonconstant slots, cost 1000). Another possible starting point is:

```text
initial_solutions/candidate_-57.852454_978.py
```

Its measured properties are approximately:

```text
EVM:                         -57.852454 dB
nonconstant partial products: 87
gate cost:                    978
```

This gives the search more performance margin than starting at -57.61 dB.

The objective is not simply to delete partial products. The actual objective
is to discover a cheaper implementation of a low-bit compression behavior:

```text
original partial-product group
    -> exact full-adder compression

possible replacement
    -> delete selected partial-product slots
    -> observe useful retained signals X
    -> synthesize a low-cost compensation function G(X)
```

The compensation is intended to exploit the distribution and correlations of
the low-order bits. It may deliberately differ from the exact deleted sum if
that gives a better final quantized result or corrects an existing bias in the
candidate.

## 2. What is being optimized

For a selected set of original pre-compression slots, let `T = a*b + c*d` be
the exact integer reference. Form the original pre-compression array, delete
the selected slots, and **insert compensation into that same array before
running the original compressor and CPA**.
For selected compensation columns `k_0, ..., k_(m-1)`, the synthesized logic
produces Boolean outputs `G_0(X), ..., G_(m-1)(X)`, and the compensation value is:

```text
C(G, X) = sum_j G_j(X) * 2**k_j
```

For each proposed output code `y` and input sample, the error-table model
constructs and simulates the complete modified array:

```text
array_y = original_array - removed_slots + compensation_slots(y)
raw_y = original_CPA(original_compressor(array_y))
Y = floor(raw_y / 128 + 0.5)
error = T - 128*Y
```

Do **not** compute `deleted_raw + C(y)` at the final output instead: dropping
low columns or using approximate compressors makes that different from
inserting compensation before compression. `compensation_error_table.py` and
`export_candidate.py` now share the `precompression_append_v1` insertion
contract in `array_compensation.py`. The exporter rejects older tables built
under the obsolete output-addition contract.

The optimization therefore has two coupled parts:

1. choose an output code for each observed state `X`;
2. implement all output bits as a shared low-cost Boolean DAG `G(X)`.

The state-wise best compensation is only an information/oracle reference. It
is not the final result, because it may require an expensive truth table. The
SMT stage must find a realizable shared circuit under the deletion-saving
budget.

## 3. Partial-product deletion model

Deletion is performed on original pre-compression slots, represented as:

```python
removed_slots = [(column, position), ...]
```

Important consequences:

- slots may come from different columns;
- the number of deleted slots is not fixed at three;
- repeated uses of the same node are distinct arithmetic slots;
- only columns 0 through 5 are currently accepted by
  `build_experiment()`;
- deletion changes the actual compressor/carry path, so the resulting raw
  output must be simulated rather than replaced by a purely symbolic `P-D`
  assumption for final evaluation.

Count partial-product **bit slots in the original pre-compression array after
deletion and insertion**. The frozen exported DAG contains final output bits,
not the original array, so counting its 19 output buckets is invalid. Count
constant-one, constant-zero, and genuinely nonconstant slots separately;
record deleted slot positions, compensation positions and G's actual truth
tables as provenance. Evaluate the reachable full-graph gate cost separately.

## 4. Choosing X: information first, implementation second

### 4.1 Initial X seed

For a proposed deletion group, begin with the direct dependency nodes of the
deleted partial-product nodes. These nodes are a natural initial observation
set because they usually make the deleted contribution conditionally simple.

For a deleted node `p`, inspect its immediate Boolean inputs and collect its
nonconstant dependencies, regardless of reachability after physical deletion. This gives a
seed set:

```text
X_seed = direct dependencies of deleted nodes in the original graph
```

This is preferable to selecting arbitrary global node IDs.

### 4.2 Local add/delete heuristic

The seed is not automatically the final X set. It can have low conditional
variance but still be expensive for `G(X)` to use. Starting from `X_seed`, use
a local heuristic that proposes:

- adding a nearby dependency or shared intermediate node;
- removing a redundant node;
- replacing a low-level node with a more interpretable shared parent;
- limiting the total X width;
- preferring nodes whose Boolean cones are shallow and cheap.

The candidate universe is ALL nonconstant nodes in the original pre-compression
graph, including the deleted partial-product nodes themselves. Removing a slot
removes its weighted arithmetic contribution; it does not prohibit observing
that signal or its dependencies. Structural proximity may prioritize proposals,
but must not restrict eligibility to a local neighborhood or to nodes reachable
after deletion. Useful proposal priorities include:

- direct inputs of deleted nodes;
- one or two levels of their fan-in cone;
- nodes shared by several deleted slots;
- low-column signals that also feed neighboring compression terms.

The search score should combine:

```text
information quality
+ X-width penalty
+ estimated logic/explainability penalty
+ preference for shared nodes
```

The information metric is used only to rank X proposals. In particular,
`information_evm_db` or conditional variance is not a proof that a final
compensation circuit exists.

### 4.3 Required node-information measurements

For each candidate X set, record at least:

- `information_mse`;
- `information_evm_db`;
- `baseline_conditional_variance` using the same X;
- `removed_conditional_variance`;
- `conditional_variance_gap`;
- whether any selected X node becomes unreachable after physical deletion;
- X width and a structural implementation-cost estimate.

Comparisons must use the same X when comparing baseline and deletion
statistics. The linear model is useful because it isolates information value,
but it is only a screening approximation.

## 5. Compensation columns

Compensation columns must be chosen from the numeric scale of the deleted
behavior, not fixed globally.

For deleted slots with columns `c_i`, first inspect the actual weighted
contribution range:

```text
D(s) = sum_i 2**c_i * p_i(s)
```

Then choose one to three compensation columns whose representable values have
similar range and granularity. For example, a mixed deletion involving
columns 4 and 5 may justify candidates such as:

```text
[4, 5]
[5, 6]
[4, 5, 6]
```

but this must be tested from the actual error table. Compensation columns are
not required to be equal, and repeated columns are allowed by the tool.

The purpose is not necessarily to reconstruct `D(s)` exactly. The useful
compensation may also move the result across the final rounding boundary or
remove a systematic error already present in the starting candidate.

## 6. Correct end-to-end workflow

For every deletion/X/column proposal:

### Stage A: structural proposal

1. choose a starting candidate with accuracy margin;
2. inspect low-column slots and their Boolean dependencies;
3. choose an arbitrary cross-column deletion set;
4. form the direct-dependency X seed;
5. apply local add/delete/replacement moves to X.

### Stage B: information screening

Run `node_set_information.py` or its Python API with:

```python
deletion_model="linear"
```

Use the result only to rank X sets and deletion groups. Reachability after
deletion is a cost-accounting attribute, NOT an eligibility constraint. An X
node that becomes unreachable may be retained or rebuilt for G. Charge the
union of its required fan-in cones, accounting for sharing with the deleted
circuit and other X nodes; do not reject it merely because it is unreachable.

The current error-table and exporter accept all nonconstant original prefix
nodes, even when physical deletion makes their cones unreachable from the
uncompensated outputs. Once used by G, their reachable gates are included in
the exported candidate's measured full gate cost.

### Stage C: physical deletion and insertion check

For shortlisted proposals, construct the original array snapshot once per
action, remove the same original `(column, position)` slots, append each
compensation output in its specified column, and run the **original candidate's**
compressor and CPA. Original slot positions must not be reinterpreted after
earlier deletions; delete in descending position order within each column.

Table action bits may be constant while exported G bits vary by X. To prevent
constant-aware compressor dispatch from changing the circuit topology between
table and export, both sides append an opaque `OR(bit, ZERO)` node. This is
charged in the final graph; subsequent *whole-circuit* Boolean cleanup can
remove redundant gates once the approximate arithmetic stages have finished.

### Stage D: real error table

For the exact selected tuple:

```text
(implementation, removed_slots, node_ids, compensation_columns)
```

run `compensation_error_table.py`. Do not reuse an error table from another X,
deletion set, or compensation-column set.

### Stage E: SMT synthesis

Run `synthesize.py` with the deletion saving as the available implementation
budget. The SMT problem must jointly select:

- truth-table behavior of G for every X state;
- shared Boolean implementation of G;
- weighted gate cost;
- compliance with the integer error budget.

An unrestricted state-wise table that satisfies the error threshold is not
enough. The synthesized DAG itself must satisfy the budget.

### Stage F: export and authoritative validation

Only SAT results proceed to `export_candidate.py`. Then measure the exported
candidate with the authoritative tools:

```bash
python eval.py exported_candidate.py
python gate_cost.py exported_candidate.py
```

Finally count the actual nonconstant slots in the modified **pre-compression**
array (the frozen exported netlist has no recoverable slot layout) and check:

```text
final EVM < starting-target threshold
final nonconstant partial products < 88
```

The exported candidate is the only basis for claiming success.

## 7. Interpretation of failure

There are several distinct failure modes:

1. **Poor information:** even an unrestricted compensation table cannot reach
   the target error. Change the deletion group or X set.
2. **Good information, expensive G:** the error table is feasible, but SMT
   cannot find a low-cost shared circuit. Simplify or restructure X; prefer
   shared interpretable nodes.
3. **SMT timeout:** preserve the hard instance and try a better X width,
   compensation encoding, or gate cap.
4. **Exported candidate fails:** confirm that the table and exporter used the
   same slot order and `precompression_append_v1` model. Verify the integer
   squared-error sum by independently simulating all samples. The full
   reachable graph cost, including X, G, compressor and CPA, is authoritative.

The desired result is specifically the second type of architectural win:

```text
several exact low-bit compressor inputs
    -> fewer retained partial-product terms
    -> a small, interpretable X set
    -> a cheaper shared G(X)
    -> equal or better final quantized accuracy
```

## 8. What actually worked: from 88 to fewer low-column bit slots

The decisive improvement was **not deleting bits alone**. It was replacing a
group of several column-4 operands, which otherwise burden the compressor,
with a much simpler **conditional carry-like bit in column 5**. A good X set
included shared prefix signals explaining when that carry is useful. The
replacement is intentionally approximate: `G(X)` is optimized against the
error of the *complete modified circuit*, not forced to reconstruct the exact
sum of the deleted terms for every possible input.

The two verified refinements start from the same 88-nonconstant-slot,
-58.183307 dB candidate:

| Experiment | Removed original slots | X (original prefix node IDs) | Compensation columns | Full EVM | Cost before/after exact cleanup |
|---|---|---|---|---:|---:|
| Four-slot replacement | `(4,0),(4,1),(4,2),(4,5)` | `152,234,568,707` | `5,6` | -57.72353155447783 dB | 985 / 980 |
| Five-slot replacement | `(4,0),(4,1),(4,2),(4,3),(4,5)` | `152,234,425,568,707` | `5,6` | -57.624495003558984 dB | 987 / 982 |

The synthesized networks are remarkably small: in the four-slot case the
column-5 G output is `X[1] OR X[3]`; in the five-slot case it is
`X[4] OR X[0] OR X[2]`. In **both** cases the column-6 G output is identically
zero. This second output was retained as an opaque insertion slot because it
changes compressor scheduling; it is **not** a nonconstant partial product.
The intermediate shorthand `88 - 4 + 2 = 86` and `88 - 5 + 2 = 85` counts
two *inserted structural slots*, including the constant-zero slot. The actual
nonconstant counts, after inspecting the pre-compression array and G truth
tables, are **85 and 84**, respectively. In both modified arrays there are six
constant-one slots and one opaque constant-zero slot. Preserve both counting
conventions and never label the opaque zero a nonconstant bit.

The verified full gate costs after Boolean cleanup are **980** for the
85-nonconstant-slot version and **982** for the 84-nonconstant-slot version.
The latter consumes almost all of the EVM margin relative to the reference;
the former retains more accuracy margin. Cost savings do not follow slot count
monotonically: retaining/rebuilding X cones, compensation logic, and changed
compressor/CPA scheduling can outweigh the gates saved by another deletion.

The cleanup is a separate, **exact-equivalence** step after compensation:
constant folding, hash-consing and Boolean rewrites on the completed graph
reduced the costs by five without changing any output bit. A 36-input-bit to
19-output-bit SAT miter returned `unsat` for each cleanup. This proves the
readable implementations match their cleaned-up frozen graphs, not that they
match the original 88-slot approximation. Authoritative `eval.py` and
`gate_cost.py` measurements, plus equality of the full-workload table's
integer error sum and the exported circuit simulation, verify the claimed
performance and costs.

The inspectable implementations and verification artifacts are:

```text
refined_solutions/readable_pp86_evm57_723532_cost980.py  # 85 nonconstant slots
refined_solutions/readable_pp85_evm57_624495_cost982.py  # 84 nonconstant slots
experiments/conditional_compensation/structured_below87/candidate_-58.183307_1006.py_4_15/
experiments/conditional_compensation/structured_below86/candidate_-58.183307_1006.py_16_6/
```

`pp86` / `pp85` in the historic filenames are **conservative total inserted
slot counts**, not the true nonconstant counts. The readable implementations
name the original AB/CD column-4 terms rather than depending on frozen DAG
IDs. Boolean cleanup occurs only *after* their original compressor and CPA:
folding before those stages can change their approximate dispatch and thus
change arithmetic behavior.
