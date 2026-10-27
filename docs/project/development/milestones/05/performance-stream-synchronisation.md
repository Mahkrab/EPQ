# CUDA stream synchronisation

The requested change replaces unconditional native-call completion with explicit submission
and observation boundaries. It builds on the existing stage batching and resident accepted
buffers. The [evidence](/docs/project/development/milestones/05/assets/stream-synchronisation-v1/README.md) retains the prospective
protocol, exact source delta, commands, raw observations and an independent reconstruction.

## Execution and ownership

Unchecked kernels and diagnostic resets submit to the solver's private stream. Cell generation,
the integer sorting network and neighbour counting execute in stream order, with one completion
at the checked count. Checked Jacobi and projection groups keep their existing completion,
diagnostic selection and cancellation polls. No numerical kernel, arithmetic expression, launch
order, timestep, iteration count or neighbour rule changes.

The bridge tracks pending private-stream work. Host transfers and growing reservations complete
that work **before** copying or replacing allocations. Reservations within capacity and empty
transfers do not enter the driver. Checked observations wait after submission, then synchronously
read their diagnostics. Transfers finish their host borrows before returning; no pinned host
staging or outstanding Rust slice borrow is introduced. Pageable uploads retain the existing
legacy-stream dependency before subsequent private-stream kernels.

Immediate launch/reset failures drain submitted work. A completion fault takes precedence and
prevents host copies or allocation replacement. Uncertain driver faults poison the resource;
context destruction retains responsibility for all allocations. Allocation exhaustion remains
retryable after a successful drain. Acceptance rejects pending work, including an unobserved
reset on an empty input. Checked empty observations complete that reset and propagate errors.
The thread-local handle and separate accepted/working buffers retain their existing ownership.

## Verification and measurement

The control exactly matches all 182 files of the earlier
[resident-state candidate](/docs/project/development/milestones/05/assets/resident-state-v1/README.md),
based on Maelstrom `87145510a9e5d812066138c35f1fac82e4f593b0` plus its retained patches.
The measured candidate changes five files; per-file hashes and the incremental patch identify
these uncommitted trees. Separately compiled PTX was identical and present in both executables.

PC measurements used the Ryzen 9 7900X, RTX 4070, WSL2, driver 610.88, CUDA 13.3.73,
G++ 13.3.0 and Rust 1.96.0. Release builds used locked offline dependencies and compute_89.
Each workload started a new simulation with device zero, block 128, refinement 4, eight
iterations and 480 unpaced steps. There was one warm-up per variant and five alternating
measured pairs, with the candidate first in the first measured pair. Timings sum completed
solver steps; construction, teardown, audits, output and profiling remain separate.
The 8,000-particle workload retained checkpoints 0/1/120/240/480. The larger cases retained
final state and diagnostics without checkpoints; effects used XSPH 0.01 and confinement 0.1 m/s.

| Workload | Control median (s) | Candidate median (s) | Median reduction | Slower candidate pairs |
| --- | ---: | ---: | ---: | ---: |
| 8,000, effects disabled | 1.666983 | 1.634343 | 1.96% | 0/5 |
| 110,592, effects disabled | 8.953472 | 8.944610 | 0.10% | 2/5 |
| 110,592, both effects enabled | 9.308881 | 9.252224 | 0.61% | 1/5 |

Control/candidate ranges were 1.6513–1.7026 / 1.6303–1.6963 s, 8.9253–8.9627 /
8.8903–8.9627 s and 9.2557–9.3280 / 9.2270–9.3154 s respectively. Individual paired
reductions ranged from 0.37% to 2.45%, −0.22% to 0.57% and −0.65% to 1.04%.
The large-case changes are small relative to observed variation; five pairs do not establish
a reliable general speedup. Samples were neither removed nor replaced.

Separate eight-step Nsight traces at 8,000 particles measured **269 → 168 explicit
`cuStreamSynchronize` calls**. The first step changed from **52 → 21** and each later step
from **31 → 21**, a **32.3% steady-step reduction**. Both traces retained 1,168 launches,
208 downloads, 11 uploads, 16 allocations and one reset. Synchronous transfer waits remain;
these counts do not mean all CPU–GPU synchronisation fell by 32.3%. Instrumented durations
do not enter the timing table. The initial trace reader expected a DRIVER table; this
Nsight version stores these driver calls in RUNTIME. The reader failure and corrected
extraction are retained, without rerunning timing samples.

Verification passed 290 local CPU tests, 292 ordinary PC CUDA-feature release tests,
23 explicitly selected CUDA library tests and nine boundary/integration tests. Strict Clippy,
formatting and both control/candidate native ASan/UBSan checks passed. The new injected-driver
checks reject copies/frees during pending work, exercise delayed completion faults, empty
observations, promotion and allocation retry. Removing the pre-access completion in a separate
negative control triggered the pending-work assertion. Existing GPU tests covered all supported
blocks, numerical error priority, cancellation polls, rollback, retries and independent lifetimes.

Seven 480-step regression pairs through 8,000 particles matched checkpoints and diagnostics
exactly. All 36 warm-up/measured workload records also agreed exactly. An independent reader
reconstructed all 50 physical records, timings and API counts from retained outputs and
activity rows. The first ambient-environment PC suite hit a scene-discovery failure reproduced
on the untouched control; isolated scene/config roots passed. Both failures remain recorded.
No fresh device-memory sanitiser or actual device-loss recovery result is claimed.

## Assessment

**Retain.** The explicit dependency model removes proven redundant waits, produces a modest
consistent benefit at 8,000 particles and preserves the tested numerical, cancellation and
ownership contracts. Its cost is one pending-work flag, three native call boundaries and
focused failure tests, with no change to kernels, device storage layouts or dependencies. Large-workload
speedups remain uncertain. CPU utilisation and worst-case cancellation latency were not measured;
this result does not qualify other GPUs, full device-owned execution or real-time throughput.
Both repositories remain uncommitted, with their existing branches, tags and gitlink unchanged.
