# CUDA numerical-kernel investigation

**Do not retain the numerical prototypes.** The qualified combined candidate and a separate
validation-only follow-up did not improve complete solver performance consistently
across the requested workloads.
The live solver remains byte-for-byte identical to the 191-file ten-optimisation
control. All pre-existing repository source and evidence are preserved. The
[evidence package](/docs/project/development/milestones/05/assets/numerical-kernels-v1/README.md)
retains the implementations, unsuccessful experiments, qualification, raw observations,
assembly and independent checks.

The control matches the retained
[tenth optimisation](/docs/project/development/milestones/05/assets/orchestration-v1/candidate-source.json).
Maelstrom HEAD remains `1e0085926d05c42949bb76b55d177d42a1f8f94f`; EPQ HEAD remains
`1f76097a218266822cdf344c38db75ed128628a8`. Exports and patches capture existing
uncommitted work; they are not new historical boundaries. No commits, branches,
tags, pushes, remotes or parent gitlink were changed.

## Method and scope

Each request starts a new simulation on the primary PC through `ssh pc`: Ryzen 9
7900X, RTX 4070 12 GB, WSL2, driver 610.88, CUDA 13.3.73, GCC 13.3 and Rust 1.96.0.
Locked offline release builds retain precise compute_89 arithmetic: no fast maths,
changed precision, approximation, accumulation order or solver work. CUDA device
zero, block 128, refinement four, eight Jacobi iterations and 480 unpaced steps
remain fixed, without graphics. Workloads cover 8,000 and 110,592 particles, both
with and without XSPH 0.01 and confinement 0.1. Small primary/regression runs retain
checkpoints 0/1/120/240/480; large runs retain final state and ordered diagnostics.

The prospective protocol required one warm-up and two alternating exploratory
pairs per variant/workload. The selected candidate then passed qualification and
seven exact regression pairs before one warm-up and five alternating primary pairs
per workload, starting measured pairs candidate/control. No samples were removed,
replaced or pooled between experiments. GPU captures and arithmetic microbenchmarks
are separate diagnostic evidence. No builds or GPU tests overlapped timed collection.

Primary totals sum completed-step monotonic clocks, including preparation, checks,
transfers, submission, completion, cancellation and acceptance. Construction, teardown,
requested checkpoint processing, correctness audits, output and evidence compression
are separate. Profiled wall times do not replace ordinary-binary primary totals.
Source manifests, freshly compiled PTX embedded in each executable, executable/input
hashes and post-collection source checks bind the observations to their variants.

## Instruction and memory diagnosis

Fresh Nsight Compute collection returned `ERR_NVGPUCTRPERM`. No cache, DRAM,
warp-stall or achieved-occupancy counters were obtained. No driver, registry,
security, clock-locking or other system settings were changed. Existing tools,
normal task-owned contexts, per-process environment isolation and private exports
were sufficient for this investigation.

Precise compute_89 PTX and line-annotated sm_89 SASS were generated for all variants.
SASS here is toolkit lowering of the same device source and arithmetic flags;
function resource queries independently load production PTX through the driver.
It is not a capture of the production module's JIT instruction stream or a dynamic
instruction count. The assembly confirms:

- The correction loop already shares repeated displacement/length work into one
  round-to-nearest square root. Source-level repeated calls are not three hardware
  roots. Owner position and radius products are already outside the hot loop.
- Radius-only Poly6 and Spiky coefficient divisions remain inside active neighbour
  paths. The first hoisting trial removes four static `div.rn.f32` sites overall
  (30 to 26), and four `MUFU.RCP` sites in the solver SASS (31 to 27), without
  changing its 52-register requirement. This is a proven redundancy, not proof
  that those divisions dominate elapsed time.
- Precise division is more than a native reciprocal. A representative Spiky-scale
  path contains `MUFU.RCP`, `FCHK`, five refinement/result `FFMA` instructions and
  a conditional accurate slow-path call, interleaved with finite/error checks.
  Compiler-generated refinement FMAs implement division; solver expression
  contraction remains disabled. Square root also lowers to a checked/refined
  sequence. Native throughput tables alone cannot price these complete paths.
- `Checked` introduces finite predicates and first-error selection around many
  expressions. The integer diagnostic atomic is executed only by failing lanes;
  those per-expression tests still occur on successful pairs. Some later tests
  repeat facts established on the identical position snapshot.
- Position storage is 12-byte AoS. Generated neighbour gathers use separate scalar
  component loads. CSR membership is contiguous within each row; lanes traversing
  different rows generally read different row offsets and gather identity-indexed
  positions. Identity order is deterministic but does not guarantee spatial
  locality after motion. Density/lambda revisits its higher-identity suffix, and
  correction visits the same fixed membership again. There is no geometry cache
  across those passes or across changed snapshots.

Ordered density, owner-gradient and squared-gradient additions remain dependency
chains. Gathers, ragged-row divergence, dependent arithmetic and instruction issue
are plausible residual costs. Without counters, their shares and a dominant
bandwidth-versus-latency explanation remain hypotheses. The earlier
[split traversal probes](/docs/project/development/milestones/05/performance-correction-integer.md)
are contextual evidence, not new samples or additive costs in this campaign.
No SoA, shared-memory tiling or reordered floating-point reduction was retained
on an assumed bandwidth diagnosis. NVIDIA's
[best-practices guide](https://docs.nvidia.com/cuda/cuda-c-best-practices-guide/index.html)
also distinguishes native instruction throughput from complete mathematical
implementations and recommends measuring the whole application.

## Register pressure and occupancy

The control reports 52 solver registers/thread, zero local/shared bytes, and no
offline compiler spills or stack frame. The driver occupancy API permits nine
128-thread blocks per SM: 36 of Ada's 48 possible warps, or a **75% theoretical
ceiling**. At blocks 32/64/256, its limits are 24/18/4 blocks, respectively.
These are resource ceilings, not measured resident warps or evidence that a higher
block size would help. Ada's limits are documented in NVIDIA's
[Ada tuning guide](https://docs.nvidia.com/cuda/ada-tuning-guide/index.html).

The dedicated correction candidate reports 44 registers, no local/shared bytes
and no compiler spills. Its corresponding limits are 24/20/10/5 blocks at
32/64/128/256 threads. At the measured block 128 this permits 40 warps, an **83.33%
theoretical ceiling**. Density/lambda remains in the 52-register solver. Unchanged
sort, summary and prefix resources are retained in the resource receipt. Increased
theoretical occupancy alone did not justify retention.

## Bounded experiments and exact behaviour

Five private variants isolate the following changes. Every exploratory physical
record and ordered diagnostic matches its control exactly; exploratory timings
are not primary comparisons.

| Variant | Change | Disposition |
|---|---|---|
| trial-0 | Calculate rounded radius-only coefficients once per particle row; replay existing checks at use | Inconsistent application benefit; rejected |
| trial-1 | Also reuse first errors from radius-only calculations, deferred to their original logical positions | Faster arithmetic microbenchmark; inconsistent solver benefit; rejected |
| trial-2 | Reuse completed geometry validation in grouped correction, with correction-specific checks unchanged | Mixed solver results; rejected as a standalone change |
| trial-3 | Also reuse first-traversal geometry validation in the ordered density/lambda suffix | Mixed solver results; not retained independently |
| trial-4 | Give validated correction its own entry to reduce its register requirement | Selected for final qualification and comparison |

The final candidate removes the now-unused validated branch from the general
entry, adds a grouped-versus-standalone hardware fixture, checks dispatch in native
fault tests and documents the proof boundary. It has 192 source files. No geometry
cache, allocation, buffer-capacity change, launch, transfer or wait is added.

The numerical reasoning is specific. The first density traversal already checks
all pair geometry and active Spiky directions, including reciprocal-scaled
neighbour directions. Before its higher-identity suffix, any density, reciprocal,
owner or prefix error has already fixed the first diagnostic. Repeating geometry
and scaled-direction checks cannot add an earlier error; suffix dot products and
ordered additions remain checked. Grouped correction follows global validation
and numerical publication on the same stream. It checks both preceding diagnostic
slots before writing. The immutable snapshot/settings have passed every geometry,
Poly6 and Spiky check; pressure, pair multipliers, contributions, ordered sums and
correction scaling still require their original checks. Independent correction
calls retain full geometry checks. No cancellation, host acceptance, poisoning,
rollback/retry or diagnostic-priority boundary moves.

A CUDA differential probe tests 1,048,576 signed radius words per block size,
covering all exponent classes and additional mantissa endpoints. It combines
12 distance cases and two prior-error states at blocks 32/64/128/256 and compares
weight/direction bits and first errors against the retained functions: **zero
mismatches**. This is sampled coverage, not exhaustive binary32-pair qualification.
The same observable 110,592-row, 64-pair arithmetic workload has one warm-up and
15 alternating CUDA-event pairs. Its checksum/error comparisons are exact. The
final recorded rerun has medians 0.125280 → 0.103616 ms
(17.29% less time), with 0/15 slower candidate pairs. The initial
probe and its separate 15 event pairs remain available; neither is pooled with
solver timing. This shows that removing invariant arithmetic/check work can help
that synthetic workload. Its timing excludes solver traversal, real neighbour
distributions and host costs.

## Primary and GPU results

Seconds over 480 steps. Positive reduction means faster. These are descriptive
medians, not a statistical-significance claim.

| Workload | Control median s | Candidate median s | Time reduction | Slower pairs |
|---|---:|---:|---:|---:|
| 8000 | 0.921534 | 0.897730 | +2.58% | 1/5 |
| 110592 | 3.361376 | 3.446599 | -2.54% | 3/5 |
| 8000-effects | 1.084395 | 1.045911 | +3.55% | 1/5 |
| 110592-effects | 3.908866 | 3.768074 | +3.60% | 2/5 |

| Workload | Control range s | Candidate range s | Paired reductions %, collection order |
|---|---:|---:|---|
| 8000 | 0.887861–1.115130 | 0.863292–1.006003 | -9.17, +11.37, +14.42, +3.19, +1.83 |
| 110592 | 3.092488–3.487717 | 3.308360–3.797329 | -2.18, +1.18, -14.11, -22.75, +2.82 |
| 8000-effects | 1.043965–1.296897 | 0.984095–1.187868 | +2.43, -0.19, +11.76, +8.41, +4.20 |
| 110592-effects | 3.700172–4.063691 | 3.640280–3.987418 | +7.87, -2.51, -2.01, +3.29, +7.27 |

All slow samples remain. In the large workload without effects, candidate
3.797329 s followed control 3.093617 s: a 22.75% paired regression. Its cause
was not established. The three favourable medians do not offset that workload's
regression or establish a dependable benefit in this variable campaign.

Separate matched full-trajectory captures give GPU milliseconds per simulation
step. Numerical stages sum eight invocations per step; host gaps are excluded.

| GPU stage | 8,000 | 110,592 | 8,000 effects | 110,592 effects |
|---|---:|---:|---:|---:|
| Density/lambda + validation | 0.256350 → 0.238743 | 1.807889 → 1.785343 | 0.269655 → 0.233759 | 1.783770 → 1.765630 |
| Position correction | 0.292590 → 0.273947 | 1.549372 → 1.499740 | 0.308123 → 0.268593 | 1.508030 → 1.481143 |
| Neighbour count | 0.130632 → 0.130933 | 0.509438 → 0.503108 | 0.133843 → 0.125189 | 0.495833 → 0.498268 |
| Neighbour fill | 0.137200 → 0.137595 | 0.552989 → 0.548383 | 0.140679 → 0.131564 | 0.538201 → 0.542390 |
| All kernels | 0.927685 → 0.891780 | 4.855197 → 4.770382 | 1.051921 → 0.945569 | 5.317499 → 5.285480 |

The target kernels improve in these captures, but the large correction saving
is only 3.20% without effects and 1.78% with effects; density/lambda improves
1.25% and 1.02%. Small effects captures also show changes in unchanged neighbour
kernels. These single matched captures cannot assign every timing difference to
the validation change, remove clock/scheduling uncertainty or override the primary
large-workload regression. Fresh controls also differ from the preceding
1.892/1.734 ms figures; those earlier captures are not fixed kernel constants.

Launches remain 65/69 per small/large normal step and 70/74 with effects.
Stream waits remain 21/26. DtoH copies remain five per step, transferring
196,056/2,709,528 bytes at small/large size. The audit checks every kernel type
and ordered stage, copy size and wait count. Resource savings are local to the
new entry; no allocation or host-movement saving is claimed.

**Reject.** The proven redundancies, exact tested behaviour, synthetic arithmetic
gain and higher theoretical correction occupancy are useful findings. They do
not establish consistently useful complete-solver performance. A second entry
and validation-proof obligations would add maintenance cost without that benefit.
The [assessment policy](/docs/project/development/milestones/05/performance-assessment.md)
and the user's consistency requirement support keeping all ten existing
optimisations and installing none of these numerical prototypes.

## Validation-only follow-up

**Reject this variant too.** The original trial-3 improved all four two-pair
exploratory medians, making the dedicated entry's effect worth separating. A
new prospective protocol preserved the failed first campaign and selected only
validation reuse in the existing solver entry. Original dispatch, module loading,
native code and all ten retained optimisations remain. The new fixture and proof
documentation are retained in a separate 192-file export.

The follow-up repeated release/CUDA/boundary/execution/native/Clippy/fmt qualification
and seven regression pairs before a fresh warm-up and five alternating pairs per
workload, followed by eight separate GPU captures. No earlier samples were replaced
or pooled. Both final source/PTX/executable identities are independently bound.

| Workload | New control median s | Validation-only median s | Time reduction | Slower pairs |
|---|---:|---:|---:|---:|
| 8000 | 1.018939 | 0.920306 | +9.68% | 2/5 |
| 110592 | 3.499163 | 3.676865 | -5.08% | 3/5 |
| 8000-effects | 1.113461 | 1.076390 | +3.33% | 1/5 |
| 110592-effects | 4.001694 | 3.932311 | +1.73% | 2/5 |

| Workload | Control range s | Candidate range s | Paired reductions %, collection order |
|---|---:|---:|---|
| 8000 | 0.904347–1.126813 | 0.907470–1.066755 | -1.76, +10.94, +15.29, +15.80, -13.40 |
| 110592 | 3.350532–3.683062 | 3.371041–3.800453 | +0.99, -3.19, +3.66, -8.61, -9.74 |
| 8000-effects | 1.044619–1.186492 | 1.052175–1.147682 | +1.65, +9.28, +1.09, -4.02, +4.94 |
| 110592-effects | 3.639290–4.078018 | 3.740070–4.072397 | +1.73, -9.85, -10.46, +5.60, +7.38 |

Matched GPU milliseconds per step, separate from primary timing:

| GPU stage | 8,000 | 110,592 | 8,000 effects | 110,592 effects |
|---|---:|---:|---:|---:|
| Density/lambda + validation | 0.254370 → 0.239164 | 1.874852 → 1.827337 | 0.255369 → 0.241272 | 1.851834 → 1.807984 |
| Position correction | 0.289034 → 0.261020 | 1.628860 → 1.567182 | 0.288738 → 0.260830 | 1.645505 → 1.516234 |
| All kernels | 0.917648 → 0.876663 | 5.072347 → 4.951516 | 0.991384 → 0.952389 | 5.641293 → 5.417527 |

The validation-only variant retains the 52-register general entry and its 75%
theoretical ceiling at block 128. It adds no entry or module lookup. GPU savings
therefore occur without the dedicated entry's resource reduction; the available
evidence does not establish occupancy as the dominant limit. It also does not
explain why ordinary solver time regresses at large size while these diagnostic
GPU captures improve. Clock, scheduling, cache and host/driver effects remain
unresolved; trace wall times cannot substitute for the ordinary comparison.

The second large-workload regression prevents a consistent application benefit.
Removing the extra entry did not resolve the retention failure. No numerical
prototype from either campaign is installed in the live tree. The separate audit
verifies another **70 exact trajectories and 100 process hash pairs**, bringing
the study to **268 matched trajectories and 386 verified process records** across
equivalent workload groups. Follow-up memcheck passes all 35 CUDA components;
racecheck/synccheck/initcheck pass the numerical reuse fixture. All raw samples,
including slower pairs, remain available.

## Qualification, failures and limits

PC verification passed 292 ordinary release tests (41 intentionally ignored),
35 explicitly selected CUDA library checks, two CUDA boundary and seven execution
checks, strict Clippy, formatting and both control/candidate native ASan/UBSan
fault suites. Existing independent CPU intermediate-bit oracles, support boundaries,
fixed-membership, overflow-priority, cancellation and rollback/retry tests remain
unchanged. The added fixture compares grouped and independent calls across four
block sizes, row tails, inactive/coincident members, support endpoints and competing
failure quantities. It also passes against a separate retained-control export
with only that fixture and its module declaration added.

Compute Sanitizer memcheck passes all 35 CUDA components. Racecheck, synccheck and
initcheck pass both discovery fixtures and the new numerical reuse fixture in
separate recorded commands. These are actual selected diagnostic passes; the
counter-permission error remains a different, unavailable measurement.

The independent reader validates **198 exact 480-step solver outputs**, covering
120 exploratory trajectories, eight first-trial traces, fourteen regression runs,
48 final warm-up/sample runs and eight final traces. It also verifies 286 process
stdout/stderr hash pairs, independently recomputes primary statistics and checks
kernel/copy/wait accounting. Comparisons exclude only measurements and build revision;
accepted state, signed zero, configuration, requested observations and ordered
diagnostics remain. The same agreement does not independently establish fluid quality:
warning-producing trajectories remain warning-producing.

The first local follow-up replay found that extraction had not materialised its
reconstructed source inputs. The evidence reader now copies the already verified
control/candidate trees into the extraction directory, preserving its source-hash
checks; no numerical assertion or measurement was changed. The corrected complete
reproduction is checked separately from the failed attempt.

Two trial-3 export/target setup errors and the initial resource probe's missing PTX
input are retained and explained. Each was corrected before measurement; none counts
as a solver sample or diagnostic pass. The new one-step hardware-counter attempt's
permission failure is retained separately. The initial arithmetic-probe launch did
not separately record its process exit; a second full probe records command, exit
zero, raw hashes and binary/source identities, and provides the reported event medians.
No discarded slow runs or altered test tolerances follow those corrections.

Other GPUs/toolchains, performance at other block sizes, actual device-loss recovery,
worst-case cancellation latency, universal speedup and statistical significance remain
unqualified. No graphics checks or fresh CPU performance campaign were run. Ordinary
Cargo/JIT caches and previous task build directories were reused; installed commands
and system configuration were not changed. All seven original manifests and both
follow-up exports pass final source checks. The archival reconstruction and live-tree receipt separately
establish that every one of the ten retained optimisations remains in the live source.

The remaining kernel time is real. These results narrow the claim: removing repeated
divisions/checks and raising an occupancy ceiling are insufficient on their own.
A future memory-layout or cooperative pair-work experiment needs measured access
and execution evidence and must preserve the same ordered sums and error boundaries.
This investigation does not claim those untested redesigns would be faster.
