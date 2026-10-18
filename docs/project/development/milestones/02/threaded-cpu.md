# Threaded CPU evaluation and CUDA handoff

## Outcome and evidence boundary

Threading distributes independent Jacobi particle work while preserving both serial searches and
the reference calculation. The assessed implementation is Maelstrom
[`60b9a767636428a26f39a1901e2cac4276c75c83`](https://github.com/Mahkrab/Maelstrom/tree/60b9a767636428a26f39a1901e2cac4276c75c83).
The [correctness evidence](/docs/project/development/milestones/02/assets/verification-v1/README.md)
retains 36 complete comparisons with exact binary32 agreement, including signed zero. The
[primary-PC campaign](/docs/project/development/milestones/02/assets/performance-scaling-pc-v1/README.md)
adds 245 exact, warning-free, complete benchmark attempts across seven sizes and seven execution
settings. No numerical contract, fixture, golden or comparison budget changed.

Threading helps the larger tested workloads with suitable worker counts. At 8,000 particles twelve
workers reduce median solver time from 64.527357 s to 21.592798 s, a **2.988×** gain against the fresh
serial grid. Small inputs expose overhead, and doubling twelve workers to twenty-four worsens that
median. These findings concern this source, workload and PC; the capacity-based default is not an
empirically optimal worker selection rule.

## Requirement assessment

The [milestone plan](/docs/project/development/milestones/02/plan.md) owns the required outcomes.
Agreement with the reference establishes preservation of its calculation, not greater physical
accuracy. The [reference evaluation](/docs/project/development/milestones/00/serial-brute-force.md#evaluation-and-limitations)
still owns the modelling limits, including fixed prediction membership, empirical correction,
eight Jacobi iterations, simple plane contact and the absence of CFD or visual validation.

| Outcome | Assessment and evidence | Boundary |
| --- | --- | --- |
| Numerical agreement | Met for the tested requests: [complete component comparisons](/docs/project/development/milestones/02/assets/verification-v1/report.json), PC snapshot hashes, audits and every CFL outcome agree exactly | Compact hashes establish equality only; they cannot admit tolerance differences |
| Repeatability | [Golden, instrumented and replay tests](https://github.com/Mahkrab/Maelstrom/blob/60b9a767636428a26f39a1901e2cac4276c75c83/tests/reference_verification.rs) repeat across workers 1, 2, 3 and 7; PC settings 1, 2, 4, 8, 12 and 24 agree with serial controls | Tested builds and counts support repeatability; no cross-platform bitwise guarantee follows |
| Transactional safety | [Independent concurrency and failure tests](https://github.com/Mahkrab/Maelstrom/blob/60b9a767636428a26f39a1901e2cac4276c75c83/tests/threaded_execution.rs) cover barriers, error precedence, every cancellation poll, rollback/retry and independent simultaneous solvers | Cancellation is cooperative; long stages delay polling. Pool spawn failure is injected, not actual OS exhaustion |
| Public usability | [CLI tests](https://github.com/Mahkrab/Maelstrom/blob/60b9a767636428a26f39a1901e2cac4276c75c83/tests/cli_workflow.rs) cover explicit/default workers, invalid combinations, environment independence and replay; the [usage guide](https://github.com/Mahkrab/Maelstrom/blob/60b9a767636428a26f39a1901e2cac4276c75c83/docs/usage.md#threaded-cpu-execution) documents the supported interface | Workers are software resources, not reserved cores; valid counts are not a measured useful range |
| Performance | Met as a measurement outcome: the [raw campaign and independent audit](/docs/project/development/milestones/02/assets/performance-scaling-pc-v1/README.md) retain overhead, spread, throughput and saturation as well as gains | Three samples, one family and one PC do not establish significance or universal scaling |

## Work distribution and ownership

The [Jacobi path](https://github.com/Mahkrab/Maelstrom/blob/60b9a767636428a26f39a1901e2cac4276c75c83/src/fluid.rs)
uses separate complete passes for current-distance filtering, density/constraint/multiplier
calculation, and correction calculation. Each pass reads immutable inputs; all multipliers exist
before corrections begin. Rayon schedules indexed particle ranges, while each particle retains its
ascending binary32 reductions. Prediction membership is built once per timestep, then filtered
against current distances without adding new neighbours during iteration.

The [execution resource](https://github.com/Mahkrab/Maelstrom/blob/60b9a767636428a26f39a1901e2cac4276c75c83/src/execution.rs)
owns a private reusable pool. Indexed results are joined before errors are inspected, retaining
serial pass/particle precedence. Returning the first arriving worker error or fusing passes could
change that precedence; deliberate competing-error controls test these hazards. Independent equation
and asymmetric-timestep controls also distinguish stale distances, in-place updates and missing
iterations. These are safeguards, not evidence that those incorrect variants were shipped. No new
solver defect was diagnosed or contract revision made during this evaluation.

Grid discovery, prediction, acceleration/CFL, candidate formation, ordered plane projection,
acceptance and fresh brute-force audits remain serial. The measured Jacobi bottleneck motivated
this boundary; it leaves serial work exposed as Jacobi accelerates. The
[implementation record](/docs/project/development/milestones/02/phases/phase-00-threaded-cpu.md)
owns the detailed scheduling and dependency decision.

## Performance interpretation and limits

The AMD Ryzen 9 7900X PC exposed twelve cores and twenty-four logical processors under WSL2 Ubuntu
24.04.5. Rust/Cargo 1.98.1 built one standard release binary. Each setting used the unchanged
480-step, eight-iteration, factor-four-refined request, one warm-up, three primary samples and a
separate profile. The [report](/docs/project/development/milestones/02/assets/performance-scaling-pc-v1/report.md)
retains every worker count, sample range, standard deviation, throughput and invocation median.

| Particles | Serial median (s) | Lowest threaded median (s) | Workers | Gain against serial |
| ---: | ---: | ---: | ---: | ---: |
| 64 | 0.327190 | 0.561333 | 2 | 0.583× |
| 216 | 1.263188 | 1.224147 | 2 | 1.032× |
| 512 | 3.281100 | 2.314932 | 4 | 1.417× |
| 1,000 | 6.842994 | 3.830030 | 4 | 1.787× |
| 1,728 | 12.508839 | 6.156865 | 4 | 2.032× |
| 4,096 | 30.966757 | 12.634991 | 12 | 2.451× |
| 8,000 | 64.527357 | 21.592798 | 12 | 2.988× |

These are observed minima among tested settings. Serial/two-worker ranges overlap at 216, as do
eight/twelve-worker ranges at 4,096. Counts 512–8,000 show clearer benefit with suitable settings;
the data do not define a precise crossover or an automatic selection policy. One worker is slower
than serial throughout. At 64, the observed default of twenty-four workers takes 15.896396 s;
non-empty work always uses its pool, with no hidden serial fallback.

At 8,000, twelve-worker samples span 21.564121–21.594882 s, with sample standard deviation 0.017190 s;
serial spans 62.904964–64.913885 s, with standard deviation 1.065937 s. Throughput rises from 59,510
to 177,837 particle updates/s. Scaling against one threaded worker is 3.038×, or 25.32% when divided
by twelve requested workers. That efficiency is not physical-core utilisation. Twenty-four workers
take 27.019083 s, showing diminishing returns and a reversal within the tested sequence.

Separate 8,000-particle profiles put serial Jacobi/search at 56.097061/7.269254 s
(85.87%/11.13%) and twelve-worker Jacobi/search at 11.326829/8.065548 s (52.05%/37.06%). Search
therefore becomes a larger remaining cost. Dispatch, barriers, validation and repeated allocation
are inside solver timing; their individual costs were not isolated. Load imbalance, shared-memory
bandwidth, cache effects and host scheduling are possible limits, not established causes of the
twenty-four-worker slowdown. No tuning was performed.

Dense support still permits quadratic interaction storage and work; uneven row lengths can give
particles unequal work. Memory use, allocation volume and adversarial performance were not measured.
The largest tested size is 8,000, not an established capacity ceiling. Fresh independent brute-force
audits, snapshots, output and one-time pool setup/teardown sit outside solver totals; invocation time
is separate, so solver gains are not whole-application gains. No fresh brute-force campaign supports
an overall original-method ratio. Fixed collection order, shared load and thermals remain confounders.
Two retained backward UTC transitions have an unknown cause; durations use monotonic clocks.

## Supported execution and reproduction

Serial brute force remains the default; serial grid is independently selectable. Use
`--backend uniform-grid --execution threaded --threads N` for an explicit pool of 1–256 workers.
Omitting `--threads` selects process-visible available parallelism capped at 256. Construction must
honour that count or fail; Rayon environment settings do not override it. Pool/query failures are
input errors, incompatible CLI options are usage errors, and numerical failure or cancellation
preserves the last accepted step. Replay restores the recorded backend and worker count.
Library callers use `ExecutionOptions` or the execution-aware `Simulation` constructors; the
[pinned usage guide](https://github.com/Mahkrab/Maelstrom/blob/60b9a767636428a26f39a1901e2cac4276c75c83/docs/usage.md)
owns examples, APIs and complete failure/publication semantics.

The [evaluation record](/docs/project/development/milestones/02/phases/phase-02-evaluation-handoff.md)
records fresh local verification and commands. The two evidence READMEs above give reproduction
commands, hashes and the original environments. Re-auditing retained PC data locally does not
constitute a new PC measurement or hosted validation.

## CUDA handoff

Preserve the assessed CPU implementation and both serial controls, frozen fixtures/goldens,
component reports, raw campaigns and their provenance. CUDA implementation remains future work.

| Responsibility | Inherited obligation |
| --- | --- |
| Physical identity and numerical work | Preserve the [numerical contract](/docs/project/development/milestones/00/phases/phase-00-design-contract.md) and [frozen manifest](https://github.com/Mahkrab/Maelstrom/blob/60b9a767636428a26f39a1901e2cac4276c75c83/reference/manifest.json): input/configuration hashes, binary32 equations, timestep/refinement, eight iterations, ordered planes and particle identities |
| Membership and stage snapshots | Preserve strict support, no self/duplicates, rounded-arithmetic coverage and once-per-prediction membership with current-distance filtering. Carry forward the [independent geometry tests](https://github.com/Mahkrab/Maelstrom/blob/60b9a767636428a26f39a1901e2cac4276c75c83/tests/uniform_grid.rs) and [stage oracle/controls](https://github.com/Mahkrab/Maelstrom/blob/60b9a767636428a26f39a1901e2cac4276c75c83/tests/support/serial_oracle.rs); complete position/multiplier snapshots must precede dependent work |
| Acceptance and diagnostics | Retain independently owned state, atomic whole-step acceptance, rollback/retry, coordinated cancellation and failure classification, every CFL/warning outcome and independent fresh density audits |
| Numerical comparison | Apply [reference-comparison-v1](/docs/project/development/milestones/00/reference-verification.md) to every required component/checkpoint and diagnostic, retaining exact structural obligations. Unchanged reduction order requires exact agreement; any changed order needs explicit qualification under the quantity-specific parallel budgets and full disagreement reports. Unequal compact hashes cannot establish tolerance acceptance |
| Public records | Keep physical identity separate from execution identity; identify backend, device/resource settings, source/build and request sufficiently for replay and interpretation |
| Measurement | Use fresh same-PC controls under a declared [protocol](/docs/project/development/milestones/00/measurement-protocol.md). Account explicitly for device setup, transfers, launch, synchronisation and repeated allocation; time completed work with an appropriate elapsed boundary. Retain invocation time, raw failures/timeouts and separate profiles |

The private Rayon pool, CPU worker limits, indexed task scheduling, host layout and choice to keep
discovery serial are CPU implementation decisions, not GPU requirements. Different GPU storage and
scheduling must still satisfy the inherited semantics. Any changed arithmetic or common numerical
repair must follow the plan's revision procedure and regenerate affected verification and measurements;
it cannot be reported as acceleration of the unchanged experiment.

## Gate and checkpoint status

G00 and G01 retain their local completion checkpoints. The evaluation and CUDA handoff are prepared
and locally verified; **G02 remains open for the separately authorised completion checkpoint**.
The [phase record](/docs/project/development/milestones/02/phases/phase-02-evaluation-handoff.md)
names the assessed revision and intended annotated tags. The existing EPQ gitlink already identifies
that revision. No commit, tag, gitlink change, publication or GPU infrastructure is included here.
