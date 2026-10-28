# CUDA reprofiling after ten retained optimisations

**Do not retain either experimental change.** The ten-optimisation solver remains
byte-for-byte unchanged. Fresh profiling identified substantial density/lambda,
correction and neighbour costs, but the tested scheduling and lookup-cache changes
did not establish a useful complete-solver improvement across the requested workloads.
The cache improved GPU fill time and the large effects workload, while three workload
medians regressed. Keeping it would exchange demonstrated regressions for a narrow gain.

The [evidence package](/docs/project/development/milestones/05/assets/reprofile-ten-v1/README.md) retains source exports, raw observations,
commands, identities, failed diagnostics, timelines, independent readers and checks.
There were no commits, branches, tags, pushes or parent-gitlink changes. Maelstrom HEAD
remains `1e0085926d05c42949bb76b55d177d42a1f8f94f`; EPQ HEAD remains
`1f76097a218266822cdf344c38db75ed128628a8`. The control's 191-file manifest exactly
matches the [tenth retained candidate](/docs/project/development/milestones/05/assets/orchestration-v1/candidate-source.json).
These exports identify existing uncommitted source, not new historical boundaries.

## Method and environment

Measurements used the primary PC through `ssh pc`: Ryzen 9 7900X, RTX 4070 12 GB,
driver 610.88, CUDA 13.3.73, GCC 13.3, Rust 1.96.0 and WSL2 kernel 6.6.87.2.
All four workloads start new simulations: CUDA 0, block 128, refinement 4, eight Jacobi
iterations and 480 unpaced steps, without graphics. Effects enable XSPH 0.01 and
vorticity confinement 0.1. The bundled 20-cubed block and counted 48-cubed capacity
block retain the established configuration. Small primary and regression runs request
checkpoints 0/1/120/240/480; large runs request final state. Complete-step timing includes
checks, transfers, launches, waits, cancellation and acceptance; construction, teardown,
requested observations, output and evidence processing are separate.

The prospective protocol required fresh baseline collection, bounded experiments,
qualification and then one warm-up plus five alternating pairs per workload, starting
measured pairs candidate/control. No samples were discarded. Seven exact regression
pairs completed before primary timing. Exploration, primary comparisons, ordinary CUDA
traces and rich CPU captures remain separate datasets; earlier task samples were not pooled.

Only existing diagnostic software was used: Nsight Systems 2026.1.3 and Compute
Sanitizer 2026.2.1. Nsight Compute 2026.2.1 returned `ERR_NVGPUCTRPERM` on an actual
one-step profiling attempt. Nsight Systems GPU metric discovery independently reported
insufficient privilege. No GPU cache, bandwidth, warp-stall or achieved-occupancy counters
were obtained. The underlying one-step CLI completing does not make that profiler run a pass.

No software was installed or configured, and no driver, registry or security settings were
changed. There was no reboot/reset. Changes were task-owned exports, builds, inputs,
traces, per-process environment/instrumentation and normal context allocations. The control
and diagnostic builds reused previous task Cargo target directories; ordinary build/JIT
cache contents may change. No cache policy or system configuration changed.

## Fresh timelines and bottlenecks

Initial collection rebuilt the frozen control and diagnostic exports, verified source and
embedded precise compute_89 PTX identities, and collected one warm-up plus three baseline
samples, three ordinary/diagnostic pairs and eight full-trajectory captures. Profiler overhead
was variable. A short prototype build overlapped part of this exploratory collection, so
those captures are explicitly perturbed evidence. The later eight matched ordinary CUDA
captures and four clean rich CPU captures ran without concurrent task builds or GPU tests.
Clean captures followed completion of the independent CPU audit and resource queries.

Clean rich captures of the retained solver give the following mean milliseconds per step.
Idle means absence of this solver's kernels/copies/memsets within the labelled step, not
measured device-wide inactivity. Wait/copy/launch idle are disjoint subsets of all idle;
CPU descheduling overlaps wall categories and must not be added to them.

| Workload | All solver-GPU idle | Inside waits | Inside copies | Inside launch APIs | Host descheduled |
|---|---:|---:|---:|---:|---:|
| 8000 | 1.441 | 1.015 | 0.176 | 0.131 | 0.004 |
| 110592 | 2.253 | 1.177 | 0.295 | 0.163 | 0.010 |
| 8000-effects | 1.225 | 0.843 | 0.157 | 0.124 | 0.003 |
| 110592-effects | 1.969 | 1.018 | 0.266 | 0.151 | 0.010 |

The previous 1.750 ms large-step estimate is not a constant of the implementation.
Fresh clean captures measure 2.253 ms without effects and 1.969 ms with effects;
initial perturbed captures were higher still. Different overhead and scheduling conditions
prevent treating those changes from the old number as a production regression. Ordinary
unprofiled measurements determine application performance. Clean rich-trace overhead against the same diagnostic build’s adjacent ordinary run
was 10.15%, 1.38%, 6.22% and 5.02% for small, large, small-effects and large-effects
respectively. These single-run estimates are variable observations, not correction
factors. Earlier overhead pairs and all raw trace totals remain available.

Density/lambda is the largest GPU computational stage at large size, followed by correction
and neighbour construction. Host descheduling is small. Input validation, materialisation
and output validation remain source-required host consumers. The existing 21 waits per normal
step, or 26 with effects, enforce CFL/bounds/allocation, ordered error/cancellation boundaries
and final host acceptance. That does not prove every microsecond inside their API intervals
is unavoidable. Residual driver/launch scheduling gaps remain incompletely attributed;
unresolved driver stacks and denied GPU counters do not justify inventing a lower-level cause.

The five explicit readbacks have consumers: two compact summaries, the neighbour total,
and final positions/velocities. Moving checks across those boundaries would require preserving
their diagnostic and cancellation priority. This investigation found no measured orchestration
change that justified such a redesign. It made no floating-point or convergence changes.

## Bounded experiments

A first isolated scheduling probe assigned numerical rows to spatially ordered lanes,
retaining identity-indexed outputs and each row's accumulation order. One warm-up and two
alternating exploratory pairs per workload produced mixed/slower results, including both
large pairs and both effects pairs at each size being slower. Its solver register requirement
remained 52. It was rejected before production qualification and never copied into the live tree.

The selected lookup experiment addressed proven redundant integer work: count and fill each
perform nine lower-bound searches against the same sorted cells. Count cached eight column
starts in the dead ping-pong half of the cell allocation. A private fill operation reused
those eight starts and searched the ninth normally. Per-row searches therefore changed 18→10,
with eight stores/loads; distance calculations, traversal, support tests and identity sorting
remained unchanged. The existing fill operation remained available as the uncached path.
Normal Rust discovery selected cached fill only after successful checked count/prefix,
without intervening position/cell/width changes. No capacity limit was introduced.

There was no new allocation, transfer, launch or wait. The cache uses eight u32 columns per padded
particle inside existing sort scratch:4 MiB of the existing 8 MiB cell allocation at large size.
Valid-row logical stores/loads total3,538,944 bytes each at 110,592 particles, or256,000 bytes
each at 8,000. These are source-level access counts, not measured DRAM traffic. Sort scratch
is overwritten before its next sort use. Failure before completed counting cannot enter
normal cached fill; accepted state and rollback remain independently owned.

## Complete-solver comparison

Seconds over 480 steps. Positive change means slower. Ranges and every paired value are
retained in `measurements/summary.json`; slower samples were not replaced.

| Workload | Control median s | Cache median s | Time change | Slower pairs |
|---|---:|---:|---:|---:|
| 8000 | 0.925003 | 1.027124 | +11.04% | 4/5 |
| 110592 | 3.433547 | 3.561523 | +3.73% | 3/5 |
| 8000-effects | 1.074168 | 1.125114 | +4.74% | 2/5 |
| 110592-effects | 3.435644 | 3.368426 | -1.96% | 0/5 |

| Workload | Control range s | Cache range s | Paired reductions %, collection order |
|---|---:|---:|---|
| 8000 | 0.920489–0.997843 | 0.927328–1.070663 | -11.21, -7.30, +4.57, -13.03, -3.42 |
| 110592 | 3.306454–4.146385 | 3.275989–3.980840 | -0.16, +0.92, +3.99, -3.39, -5.90 |
| 8000-effects | 1.043400–1.187036 | 1.041393–1.163600 | -7.83, -7.07, +3.80, +1.97, +0.24 |
| 110592-effects | 3.407810–3.813748 | 3.335141–3.382646 | +2.96, +1.20, +2.93, +1.16, +11.56 |

The large-effects gain is consistent across its five pairs, but does not offset the
small-scene and ordinary large-scene regressions. The final large-effects control sample
was 3.814 s, with an unestablished cause; it remains included. Candidate medians are not
presented as proof of significance or performance on other devices. Whole-child,
construction and teardown observations remain available separately.

## Matched GPU results and resource cost

Ordinary-binary full-trajectory Nsight captures, mean GPU milliseconds per step.
Iterative rows include all eight iterations. These are separate from primary timing.

| Stage | 8,000 | 110,592 | 8,000 effects | 110,592 effects |
|---|---:|---:|---:|---:|
| Density/lambda + validation | 0.258883 → 0.257522 | 1.892193 → 1.708420 | 0.269129 → 0.260694 | 1.833105 → 1.716757 |
| Position correction | 0.295529 → 0.295391 | 1.733825 → 1.514162 | 0.307186 → 0.299119 | 1.704187 → 1.589159 |
| Neighbour count | 0.132059 → 0.131636 | 0.547550 → 0.533985 | 0.133473 → 0.129960 | 0.530245 → 0.548339 |
| Neighbour fill | 0.138451 → 0.128316 | 0.601726 → 0.546439 | 0.140244 → 0.126181 | 0.579546 → 0.560892 |
| Row sorting | 0.006542 → 0.006860 | 0.091188 → 0.076876 | 0.006857 → 0.006959 | 0.081036 → 0.084609 |
| Spatial sort | 0.041222 → 0.040891 | 0.215170 → 0.214050 | 0.042763 → 0.041377 | 0.214967 → 0.212775 |
| All kernel execution | 0.936691 → 0.927383 | 5.232198 → 4.747277 | 1.049317 → 1.013156 | 5.664346 → 5.435713 |

The targeted fill saving is real in these captures, but unmodified numerical kernels also
shift substantially. Attributing all their movement to better data locality or the cache
would exceed the evidence. With effects, fill changes 0.140244→0.126181 ms at small size
and 0.579546→0.560892 ms at large size. GPU-stage improvements do not establish a useful
whole-solver improvement when the primary comparisons disagree.

Driver-loaded static solver resources change 52→60 registers/thread, with zero reported
local/shared bytes. Sort remains 28 registers/8,208 shared bytes, summaries 26/8,192 and
prefix 36/2,048. This demonstrates a resource trade-off, not achieved occupancy or a
proven cause of the wall-time regressions. The resource probe initially failed compilation
because its include path omitted `native`; fixing that task-only path produced the queries.
No failed setup is counted as a performance sample.

Launches stay 65/69 per small/large normal step, or 70/74 with effects. Stream waits remain 21/26.
Explicit DtoH copies remain 5 per step: 196,056 bytes at small size and 2,709,528 at large size.
Initial HtoD uploads, error-only mapped diagnostics, cancellation polls and acceptance remain.
The experiment adds neither a new steady transfer nor a new diagnostic-copy failure point.

## Correctness and decision

Qualification passed the full CUDA-enabled release suite, 34 explicit CUDA component checks,
two boundary and seven execution checks, strict Clippy, formatting, and both control/candidate
native ASan/UBSan suites. Seven 64–8,000-particle trajectories matched accepted state,
requested checkpoints and ordered diagnostics exactly. Device memcheck covered all 34 CUDA
components; race/sync/init checks passed the discovery fixture across its block/shape cases.
These diagnostics do not establish recovery after actual device loss.

The independent main audit verifies 166 exact solver outputs and raw process hashes;
a separate clean-trace audit verifies eight additional outputs against already audited
controls, for 174 unique exact records. Timing and build revision alone are excluded from
physical comparisons; signed zero, configuration, diagnostics and accepted snapshots remain.
Source reconstruction and archive/member checks are independent of mutable worktrees.

**Do not retain.** The cache removed repeated searches and reduced fill time, but did not
establish a useful application improvement across the requested workloads. It adds scratch-lifetime
obligations and higher shared-entry register requirements. The earlier lane-scheduling probe also
failed to demonstrate benefit. No experimental implementation was installed in production;
all ten existing optimisations and the exact control source remain. Further arithmetic,
layout or execution changes would need a separate measured hypothesis and qualification.
