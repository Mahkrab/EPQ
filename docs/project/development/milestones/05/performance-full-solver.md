# Complete CUDA solver profile and deferred containment

**Retain the deferred containment certificate.** The primary-PC comparison reduced
complete solver time by 8.50% at 110,592 particles and 7.07% with velocity effects.
The 8,000-particle medians improved slightly, but individual regressions and wide
candidate ranges make a reliable small-workload gain uncertain. No further GPU
numerical rewrite was justified by the available evidence.

The control is exactly the 189-file retained
[integer-quartic candidate](/docs/project/development/milestones/05/assets/correction-integer-v1/candidate-source.json).
All eight previous optimisations remain: stream batching, cooperative spatial
sort, compact state observations/residency, spatial neighbour scheduling,
guarded quartic evaluation, density/owner fusion, deferred active-distance
validation and integer reconstruction of the quartic fast path. The new
190-file candidate changes only final containment and its supporting storage,
Rust result, tests and documentation. Frozen manifests and patches, rather than
new Git checkpoints, identify both builds. EPQ remains at
`1f76097a218266822cdf344c38db75ed128628a8`; Maelstrom remains at
`1e0085926d05c42949bb76b55d177d42a1f8f94f`. Existing dirty work is preserved;
no branch, tag, remote, commit or parent gitlink changed.

The [evidence package](/docs/project/development/milestones/05/assets/full-solver-v1/README.md) includes the prospective protocol,
raw outputs, commands/exits, source/binary/PTX identities, sanitised device and
CPU activities, independent readers and reconstruction checks.

## Workload and measurement boundary

Every request starts a new simulation on the PC reached through `ssh pc`:
Ryzen 9 7900X, RTX 4070 with 12 GB VRAM, driver 610.88, CUDA 13.3.73,
Rust 1.96.0 and GCC 13.3. Measurements use WSL2 kernel 6.6.87.2 on Windows
build 26300.0. Release CUDA targets compute_89 with precise arithmetic,
CUDA device 0/block 128, timestep refinement 4, eight Jacobi iterations and
480 unpaced steps, with no graphics. The small scene is the bundled 20-cubed
falling block; the large scene is the retained counted 48-cubed block. Effects
mean XSPH coefficient 0.01 and confinement strength 0.1, both enabled.

The primary campaign has one warm-up and five alternating pairs per workload,
starting measured pairs candidate/control, plus seven separate regression pairs.
The 8,000-particle primary/effects runs and regression scenes retain checkpoints
0, 1, 120, 240 and 480. Large runs retain final state and ordered step diagnostics.
The 62 final outputs agree exactly after excluding only measurements and build
revision. An independent reader also checks 146 solver outputs across the
baseline, diagnostic, exploratory and final campaigns. Different campaigns
are not pooled for timing.

Completed-step time includes preparation, all checks, transfers, launches,
completion, cancellation and acceptance. Solver construction, teardown, output,
requested observation copies, hashing and evidence storage remain separate. Admission required
4 GiB available host memory and 2 GiB GPU memory. Ordinary runs were bounded at
120 seconds; qualification and counters at 600 seconds; traces at 240 seconds.
All requested slow samples, warnings and failed tool/collector attempts remain.

## Remaining cost before the change

These are **disjoint diagnostic wall-time contributions**, in ms per step. GPU
kernel/copy intervals have priority; CUDA API durations have their overlapping
GPU intervals removed; named host ranges then exclude both. The remainder
includes framework work, queue gaps and instrumentation. It is not a claim that
all remaining time is CPU computation. Named CPU ranges and sampled stacks
support the host attribution; sampling alone does not measure GPU stalls.

| Contribution | 8,000 ms (% wall) | 110,592 ms (% wall) |
|---|---:|---:|
| GPU-idle time inside waits/readbacks | 1.277 (50.2%) | 1.622 (20.2%) |
| Density/lambda and fused active validation | 0.253 (10.0%) | 1.800 (22.4%) |
| Position correction | 0.291 (11.4%) | 1.525 (19.0%) |
| Neighbour construction, excluding spatial sort | 0.279 (11.0%) | 1.143 (14.3%) |
| Host plane containment | 0.048 (1.9%) | 0.676 (8.4%) |
| Other named host work | 0.029 (1.2%) | 0.424 (5.3%) |
| GPU-idle time inside launch APIs | 0.162 (6.4%) | 0.210 (2.6%) |
| Spatial sort | 0.040 (1.6%) | 0.214 (2.7%) |
| GPU copy execution | 0.028 (1.1%) | 0.127 (1.6%) |

The measured roots were 2.544 and 8.016 ms. At 8,000, driver wait/readback cost
ranks first, followed by correction, neighbour construction and density/lambda.
At 110,592, density/lambda ranks first, then driver wait/readback cost,
correction, neighbour construction and CPU containment. Input/output particle
checks cost 0.118/0.121 ms at large size and materialisation 0.178 ms; these
remain. Fused validation cannot be assigned a separate exclusive density or
active-distance duration without another experimental variant. The separate
publication and physical-density checks total 0.045 ms at large size, and
candidate/projection kernels total 0.061 ms across all eight iterations.

With effects, wait/readback cost is 1.570/1.929 ms at small/large size; density
is 0.260/1.785, correction 0.298/1.508 and neighbour construction 0.279/1.130.
GPU velocity/effects total 0.083/0.567 ms. At large size the effect kernels are
curl 0.199, confinement 0.163, XSPH 0.195 and replacements 0.0058 ms.

The host thread is scheduled out for only 0.0011/0.0118 ms per step without
effects. Its on-core duration includes CUDA waiting while the GPU executes;
that overlapping work cannot be counted again as extra solver time. In the
large diagnostic capture, 67.8% of CPU samples are in the stream-completion
range and 9.2% in diagnostic readback. Many driver leaves are unresolved;
explicit ranges establish the phase attribution more reliably than those
individual unresolved addresses.

Launch APIs occupy 0.171/0.231 ms inclusive. After launch return and completion
of earlier device activity, measured GPU-idle gaps total 0.802/0.943 ms per
step. These overlap the wall categories above. Summed positive launch-return
to GPU-start latency is 4.432/14.324 ms because queued kernels overlap one
another's latency; it must not be treated as another additive wall cost.
GPU kernel execution includes any internal memory stalls, which were not
separately measurable with the denied counters.

## Focused change and correctness

The avoidable CPU containment scan takes about 0.676 ms per large step even
though final positions are already available to velocity reconstruction. The
candidate evaluates the same ordered binary32 plane predicate in that existing
kernel. Projection resets an aligned private failure record before the
stream-ordered reconstruction launch. An atomic minimum records the earliest
row/plane without changing any numerical vector. Velocity effects touch only
the numerical prefix. The existing final velocity copy returns a 16-byte
trailer, so no new launch, transfer or wait is needed.

Host finite-state and identity validation still run. A failed certificate
executes the original ordered host containment loop at its original boundary,
retaining the exact numerical error, particle/plane priority and priority of
earlier velocity-effect errors. Cancellation polls, final acceptance and
rollback are unchanged. Both accepted/working velocity allocations include the
trailer and swap their pointers and capacities together. The empty case reads
or writes no trailer. No host pointer is retained asynchronously and context
thread ownership is unchanged. The [argument](/docs/project/development/milestones/05/assets/full-solver-v1/containment-proof.md) covers arithmetic,
alignment, initialisation, lifetime and retry details.

The successful large host range falls from 0.675789 to 0.000166 ms; the small
range falls from 0.048360 to 0.000165 ms. Those are diagnostic range timings,
not standalone application speedups. In the candidate large diagnostic root
(7.299 ms), density/lambda contributes 24.8%, GPU-idle waits/readbacks 22.0%,
correction 21.0% and neighbour construction about 15.8%. Requested device storage increases by
32 bytes and the final host velocity buffer by 16 bytes for a non-empty solver;
physical allocation granularity is not measured by those requested sizes.

## Complete-solver comparison

Seconds for all 480 accepted steps; ranges contain every measured sample.

| Particles/effects | Control median [range] s | Candidate median [range] s | Median reduction | Slower pairs |
|---|---:|---:|---:|---:|
| 8000 | 1.108612 [1.098559, 1.147518] | 1.084611 [1.081089, 1.214463] | 2.16% | 2/5 |
| 110592 | 3.636510 [3.618938, 3.696097] | 3.327306 [3.295063, 3.334109] | 8.50% | 0/5 |
| 8000-effects | 1.278020 [1.255208, 1.292822] | 1.267908 [1.235475, 1.418042] | 0.79% | 2/5 |
| 110592-effects | 3.998367 [3.967903, 4.022984] | 3.715594 [3.700458, 3.772464] | 7.07% | 0/5 |

| Workload | Paired reductions %, in collection order |
|---|---|
| 8000 | +3.13, +5.48, +1.59, -0.25, -9.55 |
| 110592 | +8.38, +9.39, +8.00, +9.98, +8.77 |
| 8000-effects | -10.96, +0.07, +4.44, +1.79, -0.22 |
| 110592-effects | +7.34, +7.83, +6.36, +5.65, +7.01 |

The worst small pairs regress by 9.55% without effects and 10.96% with effects;
their cause was not established. No sample was replaced. Seven single-pair
regression scenes agree exactly; the 1,000-particle candidate is 0.34% slower
in its one check. Those individual checks are not a precise performance study.

## GPU stages and interface costs

Ordinary-binary CUDA traces, mean ms per step across each complete 480-step
trajectory. Eight-iteration rows include all eight launches. These are separate
from the primary timing samples.

| Stage | 8,000 control | 8,000 candidate | 110,592 control | 110,592 candidate |
|---|---:|---:|---:|---:|
| Spatial sort | 0.042685 | 0.043449 | 0.212998 | 0.215700 |
| Neighbour cell build | 0.003242 | 0.003300 | 0.017510 | 0.017716 |
| Neighbour count | 0.136347 | 0.138708 | 0.497993 | 0.504560 |
| Prefix passes | 0.004719 | 0.004804 | 0.007773 | 0.007854 |
| Neighbour fill | 0.143626 | 0.145741 | 0.541420 | 0.547601 |
| Row sort | 0.006827 | 0.006958 | 0.071700 | 0.072564 |
| Density/lambda + active validation | 0.268229 | 0.273285 | 1.787522 | 1.806151 |
| Publication | 0.011624 | 0.011826 | 0.023815 | 0.024221 |
| Position correction | 0.307517 | 0.311890 | 1.514461 | 1.533438 |
| Physical density check | 0.012277 | 0.012491 | 0.020970 | 0.021328 |
| Candidate position | 0.011282 | 0.011468 | 0.025901 | 0.026003 |
| Projection and marker reset | 0.016378 | 0.017113 | 0.035109 | 0.036274 |
| Velocity reconstruction / containment | 0.001545 | 0.002249 | 0.003678 | 0.005212 |

Total kernel execution changes 0.970→0.987 ms at 8,000 and 4.771→4.829 ms at
110,592 without effects; with effects it changes 1.068→1.002 and 5.326→5.323 ms.
The single captures show broad shifts even in unchanged kernels. They do not
establish causal improvements or regressions for those kernels. The new
velocity work costs approximately 0.0007/0.0015 ms; projection reset also adds
a small cost. Complete-solver benefit, rather than an assumed numerical-kernel
speedup, supports retention.

Launch counts stay 65/69; effects add five. Explicit stream waits stay 21;
effects add five. DtoH copies stay 26; effects add five. At small/large size,
DtoH bytes per step change 196,480→196,496 and 2,709,952→2,709,968; effects add
40 bytes in both builds. The only HtoD copies are initial state/plane uploads;
there are no steady uploads. The solver still returns the accepted host
snapshot required by its public API. This experiment does not redesign that API.

Driver-loaded static resources are identical: solver 52 registers, zero local
and shared bytes; sort 28 registers/8,208 shared bytes; observations 26/8,192;
prefix 36/2,048. These are static resource attributes, not achieved occupancy,
cache traffic or memory-stall counters.

## Profiling tools, overhead and platform limits

Nsight Systems 2026.1.3, Nsight Compute 2026.2.1 and Compute Sanitizer 2026.2.1
were available on the PC. Installed Linux perf tools 6.8.12 work with the WSL2
6.6 kernel; MinGW GCC 13 supplies the Windows diagnostic build. CPU stacks use
frame pointers and a diagnostic build with symbols. Production source has no
NVTX dependency. The diagnostic CUDA PTX is checked against its corresponding
ordinary executable.

Three interleaved unprofiled pairs quantify annotation/frame-pointer overhead;
full captures also add stage clocks and profiling. Changes below compare with
the unprofiled ordinary median and are descriptive, not correction factors.

| Workload | Diagnostic build only | CUDA trace + stage clocks | CPU/NVTX/CUDA capture |
|---|---:|---:|---:|
| 8000 | -0.45% | +2.79% | +7.10% |
| 110592 | +1.13% | +4.26% | +6.72% |
| 8000-effects | +0.77% | +10.95% | +11.72% |
| 110592-effects | +0.61% | +5.04% | +6.44% |

Linux perf reports user-mode hardware events for the **whole child**, including
startup and JSON output: cycles/instructions are 9.201/32.350 billion at 8,000
and 19.240/43.310 billion at 110,592, IPC 3.52/2.25 and cache-miss fractions
2.91%/2.46%. Effects yield IPC 3.39/2.41 and miss fractions 2.59%/3.04%.
The raw reports show 100% event running time. These are WSL CPU counters,
including driver polling, and cannot establish GPU memory efficiency.

GPU counters still fail with `ERR_NVGPUCTRPERM` for both ordinary and WSL-root
invocations after the documented permission/debugger settings. Nsight Systems
GPU-metric discovery also reports insufficient privilege for ordinary and root
invocations. No achieved
occupancy, DRAM/L2 throughput, cache-hit or warp-stall metrics were obtained.
A driver reload may be required; none was performed because it could interrupt
the desktop and other GPU applications. The [NVIDIA permission guidance](https://developer.nvidia.com/nvidia-development-tools-solutions-ERR_NVGPUCTRPERM-permission-issue-performance-counters)
is the relevant tool requirement. Memory-stall optimisation therefore remains
a hypothesis requiring counters or a separate controlled experiment.

A separate same-source Driver API microbenchmark compares WSL Linux and native
Windows on the same GPU, one warm-up and five alternating pairs per count and
context policy. At 110,592 with the solver's AUTO policy, native/WSL medians
are 25.225/31.216 µs for launch+wait, 30.813/43.195 µs for six launches+wait,
24.792/28.476 µs for a 32-byte bound readback and 116.746/135.107 µs for a
1,327,104-byte readback. Context push/pop is about 0.062/0.064 µs. Blocking-sync
results and all 8,000-particle samples are retained separately. Windows thread
CPU clocks are too coarse for some short cases; zero readings do not mean no
CPU work. These small kernels/copies quantify boundary differences, not a
Windows speedup for the full solver. Its CUDA build currently supports Linux
x86_64; no Windows production port was introduced. A first microbenchmark
campaign is also preserved, but only the second, with explicit compiler
receipts, supplies these figures.

During tool setup, an erroneous registry `New-Item -Force` command removed
seven existing NVIDIA driver branches. Work stopped until 233 keys and 501
values were recovered from the saved live hive, independently matched to the
existing shadow backup, restored and checked byte-for-byte, including ACLs.
The driver remained running; baseline collection began after restoration.
The privacy-limited receipt is retained; private hives and values are excluded.
Three intentionally configured profiling values remain, with a value-only
rollback script. The temporary GUI process/task and recovery-hive mount were
removed. No reboot or driver reset occurred.

## Validation and retention assessment

The isolated release suite passed 292 tests, with 39 hardware/viewer checks
ignored in that ordinary run. Explicit CUDA library hardware selection passed
28 ignored tests; full component memcheck passed 33 tests. CUDA boundary and
execution suites passed 2 and 7, including hardware checks. The two new tests
cover all block sizes, empty/odd/even and reused capacities, signed zero,
subnormal/boundary/overflow cases, velocity replacement, numerical error
priority, all cancellation boundaries and repeated failure/retry. The public
error fixture also passes the retained build. Clippy, formatting and both
native ASan/UBSan fault-injection executables pass. Local CPU-only release
verification passed 290 tests. The power implementation is byte-identical to
control; its earlier exhaustive proof is preserved, not presented as rerun here.

Device memcheck reports no access errors; racecheck, synccheck and initcheck
report no hazards/errors for the new path. Full leak checking exits 86 because
it reports allocations still owned when each private context is destroyed.
The unchanged teardown deliberately releases these through context destruction.
The retained and candidate failure fixture both report 480 allocations over
32 contexts, with exactly 1,024 additional candidate bytes, matching the two
16-byte trailers per context. This optional leak classification is not reported
as a passing leak check. NVIDIA's [sanitizer documentation](https://docs.nvidia.com/compute-sanitizer/ComputeSanitizer/index.html)
defines that check at context destruction. Initial malformed installed-scene,
test-draft compilation and old-capacity fixture failures, plus corrected
collector bookkeeping failures, are retained and explained in the evidence notes.

**Retain.** The consistent large-workload reductions, exact numerical and
behavioural comparisons and directly measured removal of the CPU traversal
justify this small interface/storage change. Costs are a private aligned record,
minor GPU arithmetic/reset work and 16 extra transferred bytes. The small-size
benefit is uncertain, and the individual slow pairs remain limitations.
Density/lambda, correction and driver boundaries are still the main remaining
costs; no speculative memory-layout or arithmetic rewrite was retained without
supporting GPU-counter evidence. These results qualify the recorded primary-PC
build and workloads, not other devices, Windows whole-solver performance or
worst-case cancellation/device-loss recovery.
