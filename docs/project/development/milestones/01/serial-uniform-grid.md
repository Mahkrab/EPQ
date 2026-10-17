# Serial CPU uniform-grid evaluation and handoff

## Outcome and evidence boundary

The serial grid replaces neighbour discovery while retaining the brute-force reference and one
shared PBF timestep. The assessed numerical implementation is Maelstrom
[`b179e6e42b4efd6e269d6eb35fbee50dba4fcfa1`](https://github.com/Mahkrab/Maelstrom/tree/b179e6e42b4efd6e269d6eb35fbee50dba4fcfa1).
The [implementation record](/docs/project/development/milestones/01/phases/phase-00-serial-uniform-grid.md)
and [retained exact outputs](/docs/project/development/milestones/01/assets/verification-v1/README.md)
establish the correctness boundary. The public application selects either search and restores that
selection during replay without changing physical input identity.

The [paired PC campaign](/docs/project/development/milestones/01/assets/performance-comparison-pc-v1/README.md)
establishes exact full-request agreement at all seven sizes through 8,000 particles. Grid medians
are slightly slower through 1,000 particles, then faster at 1,728 and above, reaching **1.618×** at
8,000. Evaluation and the local completion checkpoint are complete; remote publication remains separate.

## Design decisions and diagnosed problems

The [search boundary](https://github.com/Mahkrab/Maelstrom/blob/b179e6e42b4efd6e269d6eb35fbee50dba4fcfa1/src/neighbours.rs)
selects discovery from a complete prediction snapshot. The solver, numerical configuration,
Jacobi stages, boundary projection, audits and acceptance path remain shared. This confines the
experiment to search rather than introducing a second simulator that could drift numerically.

The [grid](https://github.com/Mahkrab/Maelstrom/blob/b179e6e42b4efd6e269d6eb35fbee50dba4fcfa1/src/neighbours/grid.rs)
sorts occupied-cell entries, searches 27 adjacent cells and restores each interaction row to particle
order. Sparse storage avoids allocation proportional to empty domain volume. A power-of-two width
at least the support radius, `2^-72` and the largest coordinate magnitude times `2^-50` makes cell
mapping exact in binary64 while leaving membership arithmetic in binary32. The minimum covers
squared-distance underflow; coordinate-dependent enlargement bounds checked cell indices.
Using the support radius alone would not cover every pair admitted by the actual rounded arithmetic.

Pruning distant cells could hide distance overflow that the reference rejects. A finite bounding-box
diagonal proves pair arithmetic safe; otherwise an actual-pair pass checks distances in reference
order. This preserves the first numerical failure without rejecting a harmless empty box corner.
These decisions address search implementation problems; they do not revise the inherited physics.

The implementation record also retains two verification corrections: an initial rebuilding fixture
was unsuitable because projection reconstructed a separating velocity, and a replay diagnostic lost
supported-version context. The fixture now uses approaching particles, and the diagnostic was
restored. No golden, tolerance, numerical setting or sampling policy was relaxed.

## Requirement assessment

These judgements refer to the outcomes in the [milestone plan](/docs/project/development/milestones/01/plan.md),
within the supported serial environment and tested workloads.

| Outcome | Assessment | Evidence and limit |
| --- | --- | --- |
| Correct strict-support discovery | Met | [Independent geometry and generated cases](https://github.com/Mahkrab/Maelstrom/blob/b179e6e42b4efd6e269d6eb35fbee50dba4fcfa1/tests/uniform_grid.rs) cover all adjacent directions, negative boundaries, coincidence, extreme values and invalid input; rows agree with brute force |
| Deterministic simulation equivalence | Met within tested envelope | [Full-run, measured and family comparisons](https://github.com/Mahkrab/Maelstrom/blob/b179e6e42b4efd6e269d6eb35fbee50dba4fcfa1/tests/reference_verification.rs), retained goldens and signed-zero checks; all 70 PC benchmark attempts agree exactly across the complete 480-step requests |
| Public usability and independent state | Met | [CLI](https://github.com/Mahkrab/Maelstrom/blob/b179e6e42b4efd6e269d6eb35fbee50dba4fcfa1/tests/cli_workflow.rs), [workflow](https://github.com/Mahkrab/Maelstrom/blob/b179e6e42b4efd6e269d6eb35fbee50dba4fcfa1/tests/headless_workflow.rs) and [transaction](https://github.com/Mahkrab/Maelstrom/blob/b179e6e42b4efd6e269d6eb35fbee50dba4fcfa1/tests/serial_simulation.rs) tests cover selection, replay, cancellation, rollback, warnings and publication |
| Measured performance and scalability | Met for the declared family and PC | [Raw results and independently checked summaries](/docs/project/development/milestones/01/assets/performance-comparison-pc-v1/README.md) show mixed small-size performance and increasing benefit at larger sizes; 8,000 is the largest tested member, not a discovered ceiling |

Exact agreement establishes preservation of the reference calculation, not greater physical fluid
accuracy. The [reference evaluation](/docs/project/development/milestones/00/serial-brute-force.md#evaluation-and-limitations)
still owns the accepted modelling limits: fixed prediction membership, empirical correction settings,
eight fixed passes, simple plane contact, free-surface density deficiency and no CFD or visual validation.

## Performance interpretation

The primary PC is an AMD Ryzen 9 7900X running WSL2 Ubuntu 24.04.5. The campaign used Rust/Cargo
1.98.1, one standard release binary and the unchanged sampling policy. Every size completed one
warm-up, three primary samples and one separate profile for each search. There were no warnings,
failures or timeouts. Raw files retain invocation wall time separately from solver time.

| Particles | Brute-force median (s) | Grid median (s) | Solver speedup |
| ---: | ---: | ---: | ---: |
| 64 | 0.256858 | 0.268774 | 0.956× |
| 216 | 1.040863 | 1.097272 | 0.949× |
| 512 | 2.659407 | 2.673178 | 0.995× |
| 1,000 | 5.905200 | 5.921604 | 0.997× |
| 1,728 | 11.568858 | 10.851780 | 1.066× |
| 4,096 | 34.933192 | 26.231439 | 1.332× |
| 8,000 | 90.021109 | 55.621480 | 1.618× |

The observed median crossover lies between 1,000 and 1,728, rather than at a precisely established
threshold. Sample ranges overlap at 512 and 1,000, where median differences are very small. At
8,000 the brute-force range is 89.523530–92.218484 s, with sample standard deviation 1.434040 s;
the grid range is 55.458316–55.814149 s, with standard deviation 0.178120 s. Corresponding throughput
is 42,657 versus 69,038 particle updates/s. The backend reports retain spread and throughput at every size.

The separate profiles explain the trend. At 64 particles grid discovery costs 0.021465 s against
0.008348 s for brute force: discovery overhead outweighs pruning. At 8,000 discovery
falls from 43.587817 to 7.344727 s. Its instrumented share falls from 48.57% to 13.71%, while Jacobi
becomes 82.83% of the grid profile. Removing pair discovery therefore exposes the unchanged solver
as the main bottleneck. No further neutral optimisation was made: the profiles justify measuring
parallel stage work next, not changing equations or reduction order to improve these results.

The earlier [PC baseline](/docs/project/development/milestones/00/assets/performance-baseline-pc-v1/README.md)
is retained independently. The new paired denominator uses the same source and binary as the grid;
differences from the older campaign also include build/source overhead and uncontrolled host conditions.
Brute-force-first order, scheduler migration, thermal state and shared load limit causal precision.
Three samples do not establish statistical significance. Both searches completed the largest requested
size within budget; no larger series or universal practical limit was established.

## Limitations

Dense or coincident support can still require quadratic candidate work and interaction storage.
Clustering increases occupancy; extreme coordinate magnitudes enlarge cells and reduce pruning.
Sorting entries and rows and finding adjacent-cell ranges add overhead, especially for small inputs.
The exceptional pair-validation path is quadratic. These are consequences of the implementation;
no separate adversarial performance campaign quantifies their costs.

Occupied-cell entries are temporary and rebuilt each step. Fixed interaction rows survive the Jacobi
passes within that step; neither search retains a cell cache between steps. Checkpoint copies and
diagnostics remain owned by the workflow. Fallible search reservations report capacity failure but
do not impose a process memory budget. Memory use, allocation volume and peak resident storage have
not been measured. Fresh independent brute-force audits are outside solver timing and can reduce
end-to-end throughput; solver speedup must not be described as whole-application speedup.

## Multithreading handoff

The next objective is to parallelise the established grid-based execution while preserving the
experiment. Keep both serial searches as independently owned controls. Reuse the existing
`SearchBackend`, immutable stage inputs and execution workflow where they fit; no threaded backend
or concurrency framework is implemented here.

| Inherited responsibility | Owner and obligation |
| --- | --- |
| Physical inputs and numerical work | [Numerical contract](/docs/project/development/milestones/00/phases/phase-00-design-contract.md) and [manifest](https://github.com/Mahkrab/Maelstrom/blob/b179e6e42b4efd6e269d6eb35fbee50dba4fcfa1/reference/manifest.json): preserve binary32 equations, `defaults-v4`, matched refinement, ordered planes, eight Jacobi passes and the seven-size family |
| Membership and stages | [Neighbour and timestep contract](/docs/project/development/milestones/00/phases/phase-00-design-contract.md#neighbour-set-contract): discover once from complete prediction, strict support, no self or duplicates, stable identity, immutable position/multiplier snapshots and current-distance filtering |
| State, diagnostics and replay | Retain atomic whole-step acceptance, independent solver state, cancellation/failure history, CFL warnings, fresh brute-force audits, backend identity and existing schema/publication guarantees |
| Acceptance | [Comparison policy](/docs/project/development/milestones/00/reference-verification.md): retain exact serial controls; apply the declared parallel quantity-specific limits to every component/checkpoint and diagnostic, with exact structural and warning/failure agreement |
| Measurement | [Protocol](/docs/project/development/milestones/00/measurement-protocol.md): use fresh same-PC controls, include construction, ordering, synchronisation and repeated work inside the appropriate timers, keep profiles separate, and retain failures/timeouts |

A changed reduction order must be visible and checked against the existing parallel budgets; those
budgets do not authorise changed equations, fewer iterations, altered support or adaptive timesteps.
Any common numerical repair requires the plan's explicit revision procedure, new affected reference
evidence and rerun comparisons. Preserve the serial code, fixtures, exact outputs and datasets so
later measurements can distinguish threading benefit from a changed experiment.

## Gate and checkpoint status

G00's correctness checkpoint is retained and G01's same-device evidence is satisfied. The requirement
assessment, accepted limitations and multithreading handoff satisfy G02 with the local completion
checkpoint. Annotated `milestone-01/phase-02/complete` and `milestone-01/complete` tags retain the
exact parent pairing with Maelstrom
[`2156bdca7f6702cea18030a8b0c603dfa393e036`](https://github.com/Mahkrab/Maelstrom/tree/2156bdca7f6702cea18030a8b0c603dfa393e036),
which adds documentation without changing the measured source, tests, inputs or reference outputs.
The [evaluation record](/docs/project/development/milestones/01/phases/phase-02-evaluation-handoff.md)
records fresh verification and that boundary. The [completion plan](/docs/project/development/milestones/01/plan.md)
owns the implementation-first checkpoint sequence. Remote publication remains separate; this evaluation does not
claim completion of the wider project.
