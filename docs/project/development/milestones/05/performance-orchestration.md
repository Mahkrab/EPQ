# CUDA orchestration and mapped error observations

**Retain the error-only mapped diagnostic mirror.** Against the current WSL2
control, complete solver medians improved by 20.71% at 8,000 particles and 7.94%
at 110,592; with velocity effects the reductions were 23.95% and 9.76%. All
20 measured pairs improved. The saving comes from eliminating diagnostic-copy
commands while preserving every completion, error check and cancellation boundary.

Control exactly matches the 190-file
[ninth retained candidate](/docs/project/development/milestones/05/assets/full-solver-v1/candidate-source.json).
Candidate has 191 files. The nine earlier optimisations remain, including GPU
residency, spatial and neighbour algorithms, numerical arithmetic, deferred
active-distance validation and final plane containment. No CUDA/Rust public
interface or numerical identity changes. EPQ HEAD remains
`1f76097a218266822cdf344c38db75ed128628a8`; Maelstrom HEAD remains
`1e0085926d05c42949bb76b55d177d42a1f8f94f`. These are frozen source exports,
not new commits. No history, branch, tag, remote or gitlink changed.

The [evidence package](/docs/project/development/milestones/05/assets/orchestration-v1/README.md) retains the prospective protocol,
source/command/binary/PTX identities, raw observations, rejected diagnostics,
privacy-limited timelines, independent readers and source reconstruction.

## Fresh control and actual causes

The current retained build was recompiled and bound to fresh precise compute_89
PTX. Initial sampling used one warm-up plus three ordinary runs per workload,
three alternating ordinary/diagnostic overhead pairs and eight full-trajectory
Nsight Systems captures. It reproduced 1.621 ms per large step of GPU-idle time
inside wait/readback API intervals. Matched final captures reproduce 1.620 ms.

Idle here means absence of this solver's kernel, memcpy and memset activities
inside the step range; it is not a device-wide utilisation measurement. GPU
interval unions are removed from CUDA API durations before host ranges are
counted. Overlapping waits, queue latency and GPU execution are never added as
separate wall costs. CPU samples and scheduler data distinguish on-core waiting
from descheduling; they do not reveal internal GPU memory stalls.

The control's large-step GPU-idle portions are 0.785 ms inside stream waits and
0.835 ms inside copies. Diagnostic transfers are tiny, yet a separate 32-byte
readback in the boundary capture spends about 23.6 µs in its API for roughly
0.79 µs of DMA. The CPU first waits for kernels, then submits another copy and
waits for that command. This is primarily command/submission/completion latency,
not a bandwidth problem. Jacobi's eight diagnostic copies contribute 0.261 ms
of copy-idle time and projection's eight contribute 0.175 ms.

The important dependencies remain:

| Boundary | Why the CPU observes it | Waits/step | DtoH copies, control → candidate |
|---|---|---:|---:|
| Acceleration/CFL, prediction and bounds | Numerical priority, CFL warning/limit, cancellation and cell width | 2 | 4 → 2 |
| Neighbour count/prefix/fill | Checked membership, total before allocation and fill errors | 2 | 3 → 1 |
| Eight Jacobi groups | Ordered numerical errors and cancellation | 8 | 8 → 0 |
| Eight candidate/projection groups | Ordered candidate/plane errors and cancellation | 8 | 8 → 0 |
| Velocity and optional effects | Reconstruction/effect error priority and cancellation | 1, plus 5 with effects | 1, plus 5 → 0 |
| Final vectors | Current accepted host snapshot and host validation | 0 additional | 2 → 2 |

The first two remaining data copies contain compact block summaries, the third
contains the neighbour total, and the final two contain positions and velocities.
These have real host consumers under the current API. Moving data/checks across
these boundaries could change error or cancellation priority. The selected
change does neither.

Kernel submission remains another cost: inclusive launch API time is
0.228→0.237 ms per large step, with unchanged launch count. Its disjoint GPU-idle
part falls 0.205→0.168 ms because more work overlaps; that is not evidence of
cheaper launch calls. Measured post-submission GPU-idle gaps are 0.931→0.969 ms.
Those gaps overlap the wall categories and were not eliminated. Summed queued
launch latency exceeds a step's duration because kernels overlap one another's
queue latency; it is not an additive cost.

The large host thread is scheduled out for only about 0.012 ms per step in both
captures. Required host particle validation/materialisation remains; CUDA waits
account for substantial on-core sampling while GPU work executes. Disjoint host
and DMA contributions from those rich captures, in ms per step, are:

| Contribution | 8,000 control → candidate | 110,592 control → candidate |
|---|---:|---:|
| Host input validation | 0.008775 → 0.008736 | 0.118554 → 0.118654 |
| Host output validation | 0.009435 → 0.008668 | 0.119131 → 0.119631 |
| Particle materialisation | 0.006160 → 0.006572 | 0.134886 → 0.135443 |
| Residual host/framework/instrumentation | 0.086413 → 0.054383 | 0.128610 → 0.095382 |
| Actual download activity | 0.028046 → 0.011218 | 0.127280 → 0.110573 |

The residual includes profiler/framework work and is not attributed to a single
production function. Most sampled driver leaf addresses are unresolved; phase
markers associate those samples with waits/copies without inventing internal
driver causes. The mapped packet's exclusive host observation is about 0.00119 ms
per large step across all checks, including its marker overhead. A separate
16-step all-API capture, needed because default tracing omits context binding,
finds about 28 push/pop pairs per steady step. Instrumented binding totals are
about 24/31 µs per large control/candidate step. An unprofiled empty-context
probe measures 64.9 ns per pair; its conditions and overhead differ, so it is
not multiplied into a claimed solver saving. Context binding is a small cost
here and its ownership model was retained.

## Selecting the change

Pinning alone did not materially improve the readback boundary. Reordering the
copy before the wait and pinned asynchronous copies were slower. For four short
kernels, control wait/copy costs about 56.2 µs, a graph containing the copy 59.8 µs,
and a kernel-only graph 53.2 µs. Kernel-only graphs offer only a few microseconds
while requiring parameter/cache updates and retaining readback latency. No
production implementation of those variants was added. Default graph tracing
omits node activities; absent node times are recorded as unavailable, not zero.
These decisions use ordinary microbenchmark timings.

The selected diagnostic instead mirrors errors into mapped host memory only
when they occur. A separate 1,920-case contention/reset/slot/count experiment,
including reversed order and 110,592 lanes, matched mapped and device minima to
independent expected records. Its observation boundary saved approximately
23–33 µs per group across empty and busy kernel cases. Those measurements
justified a candidate; they are not whole-solver speedups.

Four device records remain the authority for inter-kernel ordering. A failing
lane first performs the original device minimum. Only a strict decrease also
contributes to the mapped host minimum. After completion, the minimum of those
contributions equals the device minimum regardless of arrival order. Successful
lanes never access host memory. All four diagnostic-writing sites use one helper.
The CPU reads the private packet only after successful stream completion.
Caller results are published only after the context binding checks also succeed;
dirty private words cannot become caller output after failure.

CPU reads/resets never compete with GPU updates. GPU-only atomics are sufficient;
CPU/GPU system-scope atomic interoperability is not used. The measured device
reports CanMapHost=1, UVA=1 and HostNativeAtomicSupported=0. NVIDIA distinguishes
mapped-memory GPU atomics from host/other-device atomicity and requires ordered
host access; this design retains stream completion for that ordering.
<sup><a href="#ref-s012">S012</a></sup>

The context owns a 32-byte `cuMemAllocHost` packet. The device allocation grows
by eight bytes for its mapped address, uploaded once during construction. Reset
clears the four records but preserves that address. `cuCtxDestroy` owns cleanup,
including storage retained after uncertain completion; no borrowed stack or Vec
pointer is queued. CUDA explicitly includes `cuMemAllocHost` storage in context
cleanup. <sup><a href="#ref-s053">S053</a></sup>
The [invariant and lifetime argument](/docs/project/development/milestones/05/assets/orchestration-v1/mirror-proof.md) gives the details.

Remaining launch/completion/binding/data-copy errors retain precedence and
poisoning. Removed diagnostic-copy commands no longer have their own download
failure point. Native tests prove that an unused download fault does not affect
mapped observation, while a subsequent real data-copy failure still fails and
poisons the resource. Numerical failure, cancellation and accepted-state rollback
remain unchanged. Final plane containment and its velocity trailer are untouched.

## Complete-solver benchmark

The primary PC is Ryzen 9 7900X/RTX 4070 12 GB, driver 610.88, CUDA 13.3.73,
GCC 13.3 and Rust 1.96.0, under WSL2 kernel 6.6.87.2. Four workloads use CUDA0,
block 128, refinement 4, eight Jacobi iterations and 480 unpaced steps without
graphics. Effects are XSPH 0.01 and confinement 0.1. The bundled 20-cubed block
and retained counted 48-cubed block are unchanged.

One warm-up plus five alternating pairs per workload starts measured pairs
candidate/control. Seven exact regression pairs ran before primary timing.
Small primary/regression runs retain checkpoints 0/1/120/240/480; large runs
retain final state and ordered diagnostics. Step time includes preparation,
checks, transfers, submission, completion, cancellation and acceptance. Solver
construction/teardown, requested observations, JSON output and evidence audits
are separate. Admission required 4 GiB of host memory and 2 GiB of GPU memory. No other profiling/qualification
GPU job ran during primary samples. All slow samples and warnings remain.

| Particles/effects | Control median [range] s | Candidate median [range] s | Reduction | Slower pairs |
|---|---:|---:|---:|---:|
| 110592 | 3.318576 [3.309058, 3.391195] | 3.055206 [3.030446, 3.064489] | 7.94% | 0/5 |
| 110592-effects | 3.721898 [3.719727, 3.786482] | 3.358502 [3.352861, 3.368993] | 9.76% | 0/5 |
| 8000 | 1.088445 [1.075621, 1.228894] | 0.863036 [0.849123, 0.869600] | 20.71% | 0/5 |
| 8000-effects | 1.256330 [1.253655, 1.274531] | 0.955382 [0.954010, 1.022919] | 23.95% | 0/5 |

| Workload | Paired reductions %, collection order |
|---|---|
| 110592 | +7.39, +7.94, +10.64, +8.32, +7.77 |
| 110592-effects | +9.92, +10.03, +9.47, +11.33, +9.60 |
| 8000 | +21.62, +20.71, +29.24, +19.23, +21.41 |
| 8000-effects | +24.06, +23.47, +23.89, +25.04, +19.37 |

No sample was discarded. Small control includes a 1.229 s sample and small-effects
candidate a 1.023 s sample; their causes were not established. All pairs still
improve. Seven single-pair regressions agree exactly; their raw timings remain
separate from primary estimates.

Construction/teardown are not hidden. At large size their control/candidate
medians are 0.218816/0.230366 s and 0.041575/0.041911 s; with effects construction
is 0.218912/0.219581 s. Variation does not establish a fixed constructor penalty.
Whole-child medians, including startup and output, improve 2.034785→1.815727 s
at small size and 3.876596→3.614145 s at large size; with effects they improve
2.214995→1.914218 s and 4.281451→3.911792 s. These timer boundaries are distinct.

## GPU idle, execution and interface counts

Matched rich diagnostic captures, mean ms per step. All-idle is root wall minus
the union of this solver's GPU activities. Associated-idle is the disjoint
wait/readback API contribution, a subset of all-idle.

| Workload | Associated-idle control → candidate | All-idle control → candidate | GPU execution including copies control → candidate |
|---|---:|---:|---:|
| 8000 | 1.273 → 0.836 | 1.557 → 1.031 | 0.962 → 0.926 |
| 110592 | 1.620 → 1.095 | 2.345 → 1.750 | 4.956 → 4.955 |
| 8000-effects | 1.574 → 0.991 | 1.904 → 1.196 | 1.045 → 1.048 |
| 110592-effects | 1.935 → 1.219 | 2.708 → 1.944 | 5.443 → 5.444 |

At large size, associated-idle falls 32.4% and all-idle 25.4%. Copy-idle drops
0.835→0.270 ms, while retained wait-idle rises 0.785→0.825 ms. The optimisation
removes readback command latency; it does not claim to remove required waits
or every scheduling gap. Source-required host work and residual framework/queue
intervals remain.

| Workload | GPU launches | Explicit waits | DtoH copies control → candidate | DtoH bytes/step control → candidate |
|---|---:|---:|---:|---:|
| 8000 | 65 | 21 | 26 → 5 | 196,496 → 196,056 |
| 110592 | 69 | 21 | 26 → 5 | 2,709,968 → 2,709,528 |
| 8000-effects | 70 | 26 | 31 → 5 | 196,536 → 196,056 |
| 110592-effects | 74 | 26 | 31 → 5 | 2,710,008 → 2,709,528 |

Only 440 bytes per normal step, or 480 with effects, are removed. Bandwidth savings
are tiny; command savings dominate. Counts describe explicit CUDA memcpy events.
Error-only mapped accesses are genuine system-memory traffic, not memcpy events;
their bus volume was not measured. There is one extra eight-byte HtoD setup upload per
context; initial particle/plane uploads remain and there are no steady uploads.
Requested capacity increases by eight device bytes and 32 pinned host bytes per context,
including empty contexts; allocator/page-granularity footprints are not claimed.

Ordinary-binary GPU timings below cover full 480-step trajectories, separately
from primary timings and rich captures. Iterative rows include all eight calls.

| Stage | 8,000 control → candidate ms | 110,592 control → candidate ms |
|---|---:|---:|
| Density/lambda + active validation | 0.253796 → 0.255116 | 1.809036 → 1.800212 |
| Position correction | 0.290192 → 0.291757 | 1.533202 → 1.526240 |
| Neighbour construction | 0.279369 → 0.281024 | 1.149621 → 1.143587 |
| Spatial sort | 0.040532 → 0.040751 | 0.215578 → 0.214409 |
| Candidate/projection | 0.026659 → 0.026827 | 0.062256 → 0.061878 |
| Velocity/containment | 0.002101 → 0.002112 | 0.005209 → 0.005171 |

Unchanged kernels show small capture-to-capture shifts. No numerical-kernel
speedup is claimed. Static driver-loaded resources are identical: solver 52
registers/0 local/0 shared bytes, sort 28/0/8208, observation 26/0/8192 and prefix 36/0/2048.
These are not achieved-occupancy or memory-stall counters.

## Profiling overhead, tools and verification

Nsight Systems 2026.1.3, Compute Sanitizer 2026.2.1 and existing perf 6.8.12 were
used. Nsight Compute 2026.2.1 is present. GPU metric discovery still reports
insufficient privilege; no GPU cache-hit, DRAM, achieved-occupancy or warp-stall
results exist. No driver settings, registry entries or security permissions were
modified or removed. No software installation, driver reset or reboot occurred.
Only task files, per-process environment/instrumentation and normal CUDA/build
allocations changed; normal compiler/JIT caches may be populated without any
cache-policy change. No native Windows solver comparison is inferred.

Three alternating ordinary/diagnostic pairs quantify build overhead. Percentages
below compare diagnostic-only build, ordinary CUDA trace with stage clocks, and
rich CPU/NVTX/CUDA capture against the relevant unprofiled median. They are
observations, not correction factors; overhead/noise differs between variants.

| Workload | Control build / CUDA / rich | Candidate build / CUDA / rich |
|---|---:|---:|
| 8000 | -0.83% / +4.64% / +9.64% | -0.40% / +10.69% / +8.07% |
| 110592 | -0.76% / +2.37% / +4.87% | +0.49% / +2.42% / +5.98% |
| 8000-effects | +0.77% / +7.89% / +12.91% | -0.59% / +5.29% / +10.61% |
| 110592-effects | -0.18% / +4.78% / +5.43% | +0.06% / +1.67% / +5.55% |

Linux perf hardware events cover the whole child, including startup/output and
driver polling. At 8,000 control/candidate task clocks are 1896/1683 ms,
cycles 9.007/7.927 billion and instructions 31.520/29.388 billion. At 110,592 they are
3711/3411 ms, cycles 17.463/16.226 billion and instructions 37.864/35.704 billion.
All reported event running percentages are 100%. These WSL CPU counters are
not solver-only attribution or GPU memory-efficiency measurements.

The primary-PC release suite passes 292 tests, with 40 hardware/viewer checks
ignored in that ordinary run. Explicit CUDA component selection passes 34 tests;
boundary/execution suites pass 2/7. Native ASan/UBSan, strict Clippy and formatting
pass. Device memcheck covers all 34 CUDA components; race/sync/init checks pass for
the new mirror fixture. The new tests cover minima, slots, resets and retries
at all four block sizes; native tests cover partial construction, dirty mapped
storage after failed completion, binding failure, no caller publication, pointer
preservation and context-owned release. Existing cancellation/error/rollback
fixtures remain. A separate mapped probe validates 1,920 cases per execution.
Local CPU-only release passes 290 tests with deliberately invalid CUDA/CXX/AR
settings under Rust 1.98.1; this is separate from the primary-PC CUDA qualification.

An independent reader verifies 182 solver outputs in 14 equivalent input/request
groups: 178 full trajectories and four separate 16-step all-API diagnostics.
This includes all 62 final benchmark/regression outputs. Comparisons exclude only
measurements/build revision; ordered diagnostics, configuration, accepted state,
signed zero and requested checkpoints remain. Archive/member hashes and all
five source reconstructions are checked separately. One diagnostic collector
record-count mistake and an initial C++ brace warning were retained and fixed;
completed raw samples were reused or kept separate, not replaced favourably.

**Retain.** Exact behaviour checks, all-positive paired solver improvements and
the measured reduction in copy-associated idle justify the small mapped-packet
invariant and fixed memory cost. Remaining risks are device support for mapped
memory, failure-path system-memory traffic and normal profiling/platform
uncertainty. Real device-loss recovery, worst-case cancellation latency and
other devices remain unqualified. Required host boundaries, CPU state validation,
GPU launch count and the nine retained optimisations are preserved.

## References used

<a name="ref-s012"></a>
**S012.** NVIDIA (2026), *CUDA Programming Guide*, Release 13.2, §6.2.6.3
(mapped memory). [Source record](/docs/research/sources/012-nvidia-cuda-programming-guide-release-13-2.md).
The archived guidance supports ordered access and atomic scope; actual toolkit
13.3 compilation and device behaviour are verified separately in this investigation.

<a name="ref-s053"></a>
**S053.** NVIDIA (2026), *CUDA Driver API*, v13.3.0, context management,
`cuCtxDestroy`. [Source record](/docs/research/sources/053-nvidia-cuda-driver-api.md).
