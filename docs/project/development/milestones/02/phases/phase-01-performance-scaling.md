# Phase 1 primary-PC measurement and worker scaling

## Starting point

Work began from clean EPQ `5d0f4d4c3bf1a3d9f85fc2df636b03ada38a7f6b` and Maelstrom
[`60b9a767636428a26f39a1901e2cac4276c75c83`](https://github.com/Mahkrab/Maelstrom/tree/60b9a767636428a26f39a1901e2cac4276c75c83),
identified by the existing `milestone-02/phase-01/start` tags. The
[threaded verification record](/docs/project/development/milestones/02/phases/phase-00-threaded-cpu.md)
qualified deterministic execution but retained no PC scaling campaign. All 82 recorded simulator
source hashes were checked against the current clean implementation before collection.

## Scope and outcome

The existing collector now selects explicit workers, checks their execution identity and reuses one
release binary across serial-grid and worker series. The
[scaling protocol](/docs/project/development/milestones/02/scaling-protocol.md) was written before
collection. The seven sizes through 8,000 particles, 480-step requests, refinement, checkpoints,
warm-up, three primary samples, separate profiles and timeout/grace budgets are unchanged.

The [retained PC campaign](/docs/project/development/milestones/02/assets/performance-scaling-pc-v1/README.md)
contains **245 complete benchmark attempts**, seven full correctness results and the default-worker
probe. No warning, failure or timeout occurred. Every benchmark attempt agrees exactly with its
same-size serial-grid control, and every full correctness result matches its golden.

| Particles | Serial median (s) | Fastest tested workers | Threaded median (s) | Speedup against serial |
| ---: | ---: | ---: | ---: | ---: |
| 64 | 0.327190 | 2 | 0.561333 | 0.583× |
| 216 | 1.263188 | 2 | 1.224147 | 1.032× |
| 512 | 3.281100 | 4 | 2.314932 | 1.417× |
| 1,000 | 6.842994 | 4 | 3.830030 | 1.787× |
| 1,728 | 12.508839 | 4 | 6.156865 | 2.032× |
| 4,096 | 30.966757 | 12 | 12.634991 | 2.451× |
| 8,000 | 64.527357 | 12 | 21.592798 | 2.988× |

These are the lowest observed medians, not statistically established winners. The 216-particle
serial/two-worker ranges overlap, as do the 4,096-particle eight/twelve-worker ranges. One worker is
slower than serial throughout. At 8,000, doubling twelve workers to twenty-four worsens the median to
27.019083 s, still 2.388× faster than serial. The default is therefore not automatically the fastest
setting. Its 64-particle median is 15.896396 s, exposing substantial small-input overhead.

## Decisions and implementation

### Controls, resources and acceptance

Fresh serial-grid controls supply the threading denominator; threaded one-worker results supply the
scaling denominator. Counts 1, 2, 4, 8, 12 and 24 span overhead, intermediate scaling and the observed
default. The CLI without `--threads` selected 24. WSL exposes twelve cores, twenty-four logical
processors and affinity 0–23; this does not establish unseen host topology or simultaneous service.
No fresh brute-force series was collected, so no original-method gain is inferred from older timings.

Unchanged per-particle reduction order requires exact binary32 agreement, including signed zero.
Acceptance retains physical identities, sign-sensitive snapshot hashes, checkpoint audits, every CFL
value, warnings and completion. Build, backend and worker settings are checked separately. Unequal
hashes reject acceptance; compact data never establishes tolerance agreement. Missing controls or
incomplete clean primary sets supply no ratio.

### Timing, overhead and saturation

The PC used temporary checkouts of the exact commits with the uncommitted collector overlaid. Its
existing checkout remained intact. Rust/Cargo 1.98.1, locked dependencies and one standard release
binary were used without custom flags or affinity, priority or frequency changes. No project tests
or builds ran on the PC during collection.

Dispatch, barriers, synchronisation, validation and repeated allocation remain inside coordinator
wall-clock intervals. One-time pool construction and teardown stay outside; invocation wall time
includes setup, audits and output. Profiles and residuals remain separate from primary ratios.

At 8,000, the serial profile spends 85.87% in Jacobi and 11.13% in search; twelve workers change these
to 52.05% and 37.06%. These profiles identify remaining costs, without isolating scheduling, cache or
bandwidth causes. Twelve-worker scaling relative to one worker is 3.038×; requested-worker efficiency
is 25.32%, defined as scaling divided by twelve, not physical-core utilisation. No tuning or numerical
change was introduced: the measured overhead and saturation are retained results.

## Verification

The PC passed **204 release Rust tests**, including two doctests, and **26 collector tests** before
collection. Locally, those 26 and five component-verifier tests passed. Failure controls cover changed
resources, observations and hashes, unavailable controls, source/environment mismatches, duplicates,
interruption, timeout/kill behaviour and destination preservation.

The independent audit checks raw hashes, source/collector provenance, frozen inputs, exact outputs,
primary statistics, throughput, invocation medians, stage sums/proportions/residuals and both ratios
without importing collector code. A deliberately wrong stored median is rejected even when its hash
and summary are updated. All eight current reports regenerate byte for byte on the PC and locally;
historical laptop/PC baseline and paired-search reports also regenerate unchanged. Full component
reports retain zero position/velocity errors, audits and CFL agreement for all seven correctness runs.

## Limitations and Gate G01

**G01 is satisfied by the retained PC evidence.** No larger series or memory measurement was made.
Three samples, fixed order, shared host load, scheduling and thermals limit interpretation. UTC moves
backwards by 0.547 s and 0.408 s between two successive invocation pairs; the cause is unestablished.
Elapsed measurements use monotonic clocks and the collector waits synchronously for each process.
No physical-accuracy, significance or universal scaling claim follows.

The assessed Maelstrom source and parent gitlink remain unchanged. The collector, tests and retained
campaign are committed in EPQ `ecedd30e1148b820b2f0db905f047ab37f36fb50`. Annotated
`milestone-02/phase-01/complete` tags identify the subsequently authorised local completion checkpoints
in both repositories. The retained PC files are unchanged; remote publication and hosted verification
remain separate from this checkpoint.
