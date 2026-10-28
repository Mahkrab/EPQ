# CUDA active-distance validation assessment

**Retain.** Sharing validation with the existing density/lambda traversal preserved
all observed numerical and diagnostic results while reducing complete-solver median
time by 4.76% at 8,000 particles and 11.10% at 110,592. The change costs four bytes
of reusable device storage per particle and one additional register per solver
thread. One small-workload pair regressed; every large-workload pair improved.
This is a bounded primary-PC result, not a claim for other devices or workloads.

The [evidence and reproduction instructions](/docs/project/development/milestones/05/assets/active-distance-v1/README.md)
retain the [prospective protocol](/docs/project/development/milestones/05/assets/active-distance-v1/protocol.md),
source hashes/deltas, raw observations, stage activities, qualification logs and
independent readers. The control is exactly the retained 188-file
[density/lambda candidate](/docs/project/development/milestones/05/performance-density-lambda.md).
It was still uncommitted when this investigation began. Both source trees are
reconstructible from Maelstrom `1e0085926d05c42949bb76b55d177d42a1f8f94f`
and recorded patches; the candidate has 189 files. Existing density work and EPQ
evidence remain intact. No commits, branches, tags, remotes or gitlinks changed.

## Diagnosis and implementation

Before implementation, fresh ordinary-control profiles covered complete 480-step
trajectories at both sizes. Active-distance validation consumed 0.090321 and
1.007791 GPU ms per step across eight iterations; density/lambda consumed
0.247545 and 1.801390 ms. Source inspection identified a complete redundant row
traversal: validation checked displacement, ordered squared length and rounded
square root for every fixed neighbour; density/lambda immediately calculated
exactly that geometry again from the same immutable positions. Correction also
uses distances, but combining validation with density/lambda removes the earlier
traversal without carrying geometry across the multiplier barrier.

The grouped validation kernel now calculates numerical results speculatively using
the density/lambda traversal. A separate first-error accumulator receives only
geometry errors, in the original neighbour order, even after an earlier numerical
expression has failed. Three numerical scalars and their deferred error word go
into private candidate scratch. Only geometry failures enter the validation slot.
The following kernel checks that completed slot globally before publishing density,
constraint and multiplier, then exposes the deferred numerical error in its own
slot. Correction and physical-density checking follow in their original slots.

A geometry failure at a later particle therefore still precedes any numerical
failure at an earlier particle. Validation failure leaves all numerical output
buffers unchanged. Numerical errors still select the original expression and
particle, suppressing dependent stages. Standalone validation and numerical calls
retain their separate behaviour. Every subtraction, finite check, ordered dot
product, rounded root, support comparison, dependent addition, division and
subsequent numerical expression remains; none is approximated or reassociated.
Self insertion and the higher-identity squared-gradient suffix are unchanged.

Each producer owns one private record. A stream-ordered kernel boundary separates
validation writes from global diagnostic reads and separates multiplier publication
from correction's peer reads. Positions remain immutable throughout. Host completion,
cancellation, acceptance and rollback boundaries are unchanged. Failed scratch never
becomes accepted state and is overwritten before reuse. Speculative arithmetic can
perform more work on a failing attempt; worst-case cancellation latency was not
measured.

Candidate scratch grows from 12 to 16 bytes per particle: 32,000 additional bytes
at 8,000 and 442,368 bytes (432 KiB) at 110,592. No additional allocation slot,
per-neighbour cache or capacity cap is introduced. Writing and reading each 16-byte
pending record adds 32 logical bytes per particle per iteration relative to direct
publication; actual DRAM traffic was not measured. The bridge checks the larger
grouped capacity before submission; Rust retains checked size arithmetic.

## Measurements

The primary PC had a Ryzen 9 7900X, RTX 4070, driver 610.88, CUDA 13.3.73,
GCC 13.3 and Rust 1.96.0. Separate precise `compute_89` release builds used locked,
offline dependencies. Fresh PTX was checked inside each executable. Source, binary,
input and environment identities were retained and source hashes rechecked afterwards.

Every request started a new, unpaced simulation: CUDA device 0, block size 128,
refinement four, eight fixed iterations and 480 steps, without graphics. Five
alternating measured pairs followed a separate warm-up pair for each workload.
The small scene retained checkpoints 0, 1, 120, 240 and 480; the large scene used
a counted 48-cubed block and no checkpoints. Effects enabled XSPH 0.01 and confinement
0.1. No sample was replaced or pooled with earlier campaigns.

Completed-step clocks include preparation, validation, transfers, launches,
completion, cancellation and acceptance. Construction, teardown, output, storage
and correctness audits are separate. Medians describe five observations, without a
statistical-significance claim.

| Workload | Control median (s/480 steps) | Candidate median | Less solver time | Speedup |
| --- | ---: | ---: | ---: | ---: |
| 8,000 | 1.172103 | 1.116272 | 4.76% | 1.050x |
| 110,592 | 4.275596 | 3.800911 | 11.10% | 1.125x |
| 110,592 with effects | 4.663998 | 4.179186 | 10.39% | 1.116x |

Small-workload paired reductions were 2.77%, 6.67%, 5.78%, 4.66% and **-7.99%**.
The slower candidate took 1.270852 s against 1.176775 s; it remains in the evidence
without an assigned cause. Large paired savings ranged from 10.67–11.75%, and
effects savings from 10.27–11.64%, with all ten pairs improving. Raw values,
ranges and order are retained. No CPU affinity, clock locking or exclusive-machine
qualification was performed. A short pre-change evidence-reader execution overlapped
collection; its effect was not isolated or used to explain any sample.

Separate ordinary-binary Nsight profiles covered full motion. These are summed
GPU kernel intervals per step across eight iterations, excluding host gaps, rather
than primary medians or standalone synthetic-kernel measurements.

| Stage (GPU ms/step) | 8,000 control | Candidate | 110,592 control | Candidate |
| --- | ---: | ---: | ---: | ---: |
| Separate distance validation | 0.095697 | — | 1.006654 | — |
| Density/lambda; candidate also validates | 0.262083 | 0.256347 | 1.800007 | 1.794653 |
| Publish pending results | — | 0.011138 | — | 0.023842 |
| **Validation + density/lambda including publication** | **0.357780** | **0.267486** | **2.806660** | **1.818494** |
| Position correction | 0.305129 | 0.298966 | 1.886305 | 1.878180 |
| Physical-density check | 0.011390 | 0.011769 | 0.019631 | 0.021051 |
| Candidate position | 0.010965 | 0.010827 | 0.025853 | 0.026001 |
| Plane projection | 0.015790 | 0.015693 | 0.035060 | 0.035203 |
| **All numerical iterations** | **0.701055** | **0.604740** | **4.773510** | **3.778931** |

The combined stage saved 25.24% and 35.21% (1.338x and 1.543x), including publication.
All numerical kernels saved 13.74% and 20.84%. Early/late combined intervals also
improved: at large size, 1.618781→1.079945 ms for steps 1–120 and
3.398723→2.184639 ms for steps 241–480. Individual iterations are in the audit.
Small regressions remain visible in some unchanged kernels, particularly the
physical-density check (+0.000379/+0.001420 ms). Single captures do not establish
their cause or uncertainty; no cache, bandwidth or achieved-occupancy counters
were collected.

Launches remain six per iteration, 48 numerical launches per step and 65/69
complete-step launches. The audit reconstructed all 31,200/33,120 launches per
trace, 21 explicit waits per step, 26 downloads, zero steady uploads and unchanged
196,480/2,709,952 steady transferred bytes. Three initial uploads remain separate.
Driver-loaded solver resources changed from 51 to 52 registers per thread, with
zero local/shared bytes in both cases; other functions' resource attributes matched.
These are function requirements, not measured occupancy or a cache analysis.

## Correctness and retention limits

All 50 final regression, warm-up and measured outputs matched exactly in canonical
physical/configuration data and ordered diagnostics, excluding only timings and
build revision. Seven regression sizes covered 64–8,000 particles. Both profiler
pairs also matched exactly, as did the four pre-change warm-up/profile records.
This qualifies the recorded checkpoints/final states and diagnostics, not every
unobserved intermediate position or independent fluid quality.

PC verification passed 292 ordinary release tests (37 intentionally ignored),
31 explicitly selected CUDA library tests, two CUDA boundary tests, seven CUDA
execution tests, strict Clippy, formatting and native ASan/UBSan. Local CPU feature
isolation passed 290 tests with invalid CUDA/toolchain settings. New tests cover all
four block sizes, empty/single/tail rows, strict support, coincident and signed-zero
positions, repeated reuse, first-expression/particle/stage priority, unchanged
outputs on validation failure, rejection of acceptance and clean retry. Existing
independent CPU density/constraint/lambda/correction bit oracles and cancellation,
rollback, diagnostic and fault-injection tests also passed.

Both new fixtures passed a separate retained-control build with only the test module
overlaid, establishing the expected original behaviour. An initial new fixture failed
because its three-particle case accidentally referenced itself; correcting that
fixture changed no production code. Its failure, correction and subsequent checks
are retained. A native test rejects the former 12-byte candidate capacity before
launch and verifies successful reuse after growth.

Compute Sanitizer exited 97 with sixteen WDDM debugger/device-support errors even
though its two selected tests passed. This is **not** a device-memory diagnostic
pass; racecheck was not run. Other GPUs, compilers, block-size performance, actual
device-loss recovery and worst-case cancellation latency remain unqualified.

Under the [assessment policy](/docs/project/development/milestones/05/performance-assessment.md),
the consistent large-workload benefit, smaller-workload median gain, exact observed
results and small reusable memory cost justify retention. The explicit publish
boundary makes error precedence reviewable without extra launches, host transfers,
per-neighbour storage or changed solver work. The small slow pair, minor component
regressions and unavailable device diagnostics bound this decision rather than
being treated as passes or discarded.
