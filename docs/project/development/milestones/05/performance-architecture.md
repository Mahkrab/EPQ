# CUDA PBF architecture, numerical policy and external comparison

**The ten retained optimisations and production semantics are unchanged. Do not
adopt the experimental paths into production.** The remaining gap is not principally explained by residual
FP64 arithmetic or a generic AoS-to-SoA conversion. Host observation boundaries have
measurable costs, but removing them does not provide enough throughput for real time
at the current work rate. Independent physical checks also show that the unchanged
control is not an established accuracy target.

The [protocol and evidence package](/docs/project/development/milestones/05/assets/architecture-v1/README.md)
retain the requests, variants, failures, source identities, observations and independent
audit. Production is Maelstrom `250932784790ba26cdc55fc38a877ccefacbf054`;
its 191-file manifest exactly matches the preceding ten-optimisation control.
EPQ started at `814f88a`; neither repository's history, branch, tags or gitlink changed.
Experimental code exists only in parent investigation tools and disposable exports.

## What was compared

All new GPU work ran through `ssh pc`: Ryzen 9 7900X, RTX 4070 12 GB, WSL2,
driver 610.88 and CUDA 13.3.73. There were no driver, registry, security, installed-command
or system-configuration changes. No task build or GPU diagnostic overlapped admitted
paired timing. Initial large checkpoint collection was interrupted and excluded;
its expensive audit overlapped an exploratory comparator build. That request remains
failure evidence, not a timing sample.

Each ordinary request starts a new, unpaced simulation without rendering. The two
blocks contain exactly 8,000/110,592 particles, spacing 0.05 m and support radius 0.1 m,
with the existing six-plane boxes and gravity. Main comparisons disable velocity effects;
separate exact checks enable XSPH 0.01 and confinement 0.1. Resolved configuration matters:

| Quantity | Maelstrom control and aligned CUDA comparator |
|---|---|
| Duration/work | 480 steps, eight immutable Jacobi iterations per step; approximately one simulated second |
| Timestep | Binary32 0.0020833334 s |
| Refinement consequence | Correction scale **0.0625**, as well as the smaller timestep |
| Normalised rest density | Binary32 8078.199 m⁻³; physical rest density 1,000 kg m⁻³ |
| Particle mass | Binary32 0.123789966 kg |
| Regularisation | Binary32 1999.9999 m⁻² |
| Artificial pressure | Strength 0.001 m², reference separation 0.020000001 m, exponent four |
| Membership | Prediction-time neighbourhood, rebuilt once per step; current-distance filtering during iterations |

An independent binary64 reader found initial neighbour counts min/median/p95/max
**7/28/30/32** in both blocks. At one second the large control had **0/32/37/45**;
the repaired comparator had **2/32/37/44**. The comparator's prediction-time rows at
steps 1/120/240/480 had median **28/29/41/32**, p95 **30/33/49/37**, and maximum
**32/40/57/44**. Its recorded checkpoints had no capped or duplicate rows. Counts
change during impact: matching N alone would not match neighbour work.

The published Armadillo example uses 128k particles, three iterations and an 8 ms
step; dam break uses 100k, three iterations and a 4 ms step. Reported step times are
4.2/4.3 ms on a GTX 680. Maelstrom requests 3,840 Jacobi iterations per simulated
second, versus 375/750: **10.24×/5.12× the iteration rate**, before accounting for N,
neighbours or different physics. The paper does not supply the exact support,
neighbour distributions, source or quality outputs needed to reconstruct an equivalent
benchmark. No hardware-normalised slowdown ratio is claimed.<sup><a href="#ref-s004">S004</a></sup>

## Measurement boundary and admission

Production completed-step totals include its ordinary checks, transfers, submissions,
waits, cancellation and acceptance. Construction, teardown, requested observations,
output and independent analysis remain outside that timer. Fresh production medians
were **0.842505/3.021857 s** over 480 steps; corresponding checked native-driver medians
were **0.843819/2.986749 s**. These are separate boundaries, not pooled samples.
The large production control completed with CFL warnings on 259 steps. The CLI was reused
from the previously built ten-optimisation export; its embedded `build_revision` is
null. Its complete source manifest equals the current commit, and freshly compiled
production PTX was verified inside the executable. These receipts establish source
identity; this was not a fresh Cargo build or Rust qualification.

The native driver reuses the frozen device algorithms. It matched production bits at
0/1/120/240/480 for 1,000 and 8,000 particles and at the large final state, including
separate effects-enabled final comparisons. Nevertheless it is **not the production
transactional API**: it lacks cancellation callbacks and CFL warning publication,
uses a private runtime context and preallocated host storage, and reserves a conservative
512-neighbour capacity per particle. At large size that row allocation alone is
216 MiB, with an overflow audit; production retains unrestricted compact growth.
The resident variant fixes the validated bounded-scene cell width to 0.125 m.
These differences prohibit presenting its gains as already-achieved production speedups.

Each admitted comparison retained one warm-up and five alternating pairs, reversing
order each pair. No slow samples were replaced. Medians below have their complete
ranges and individual pairs in the evidence. They are descriptive, not significance
tests. Inspection runs, parameter sweeps and timelines are separately labelled.

## Controlled architectural costs

Seconds per 480 steps, checked native control → experimental candidate. Each row has
its own fresh control. Positive speedup exceeds one; all finite-state exactness claims
refer to the tested trajectories, not general failure behaviour.

| Experiment | 8,000 s; speedup | 110,592 s; speedup | Trade-off/result |
|---|---|---|---|
| Defer diagnostic completion to step end | 0.845441 → 0.640454; 1.320× | 2.982059 → 2.754822; 1.082× | Same tested bits; changes immediate error/cancellation boundaries |
| Remove per-step CPU-owned snapshots | 0.847977 → 0.798715; 1.062× | 2.985585 → 2.700633; 1.106× | Same tested bits; removes vector readback, host finite checks/materialisation and current host observation |
| Resident vectors and deferred observations | 0.846971 → 0.501096; 1.690× | 2.986031 → 2.393095; 1.248× | Same tested bits; fixed allocation/width and changed ownership/failure API |
| Force binary64 reference power | 0.842618 → 0.992934; 0.849× | 2.991963 → 4.837292; 0.619× | Same bits; inverse probe shows the retained guarded quartic already avoids a substantial cost |
| Replace guarded power with FP32 quartic | 0.844164 → 0.807852; 1.045× | 2.984580 → 2.901524; 1.029× | Loses bitwise agreement; modest remaining arithmetic saving |
| Enable FMA contraction | 0.841836 → 0.837769; 1.005× | 2.989429 → 2.961336; 1.009× | Loses bitwise agreement; small measured effect |
| Positions in component SoA | 0.852116 → 0.850849; 1.001× | 2.991942 → 3.498439; 0.855× | Same bits; approximately 17% slower at large size, including conversion costs |
| Binary32 cell-coordinate arithmetic | 0.840840 → 0.839744; 1.001× | 2.989073 → 3.003518; 0.995× | Same tested bits in these bounded scenes; no useful measured saving |
| Disable per-expression finite checks | 0.850899 → 0.789765; 1.077× | 2.984190 → 3.015833; 0.990× | Same finite trajectory; loses checked failure semantics and does not help the large workload |

The joint FP32-power/FMA/SoA path slowed the large checked case
**2.993064 → 3.415372 s**. Its resident form reached **2.776364 s**, worse than
resident AoS. Benefits cannot be multiplied independently. A separate FP32-power
resident comparison improved **2.391547 → 2.291338 s** (1.044×). Disabling checks
as well produced **2.333489 s** against **2.986077 s** checked control (1.280×),
not a further improvement over the checked-arithmetic resident prototype.

These experiments quantify selected equivalence requirements. They do **not** measure
a universal determinism premium, or the isolated cost of arbitrary summation order,
parallel reductions or spatially reordered particle storage.

## Timelines and the remaining kernel floor

Twelve fresh Nsight Systems captures used labelled step ranges. CUDA kernel and launch
counts reconcile with source order: **65/69 launches per small/large step**, including
six numerical/projection launches per iteration. Steady explicit completions change
**21 → 1** in resident mode; explicit DtoH calls change **5 → 0**. At large size the
checked driver downloads **2,709,528 bytes per step**, including CPU position/velocity
vectors and compact summaries. These are API bytes, not measured DRAM traffic.

Large resident control: approximately **4.801 ms/step** of GPU activity and **0.192 ms**
of remaining non-GPU wall intervals in the instrumented step ranges. Main GPU costs
were density/lambda/validation **1.799 ms**, correction **1.526 ms**, neighbour count/fill
**1.046 ms**, spatial sorting **0.214 ms** and identity sorting **0.072 ms**.
Removing every remaining host interval would still leave more GPU work than the
**2.083 ms** simulated step. Ownership changes alone cannot meet real time here. GPU-idle
intervals mean absence of this process's traced activity, not device-wide inactivity;
kernel durations also include internal stalls.

Forcing reference power raised correction to **5.356 ms**; FP32 quartic reduced it
to **1.328 ms**. Position SoA instead raised count/fill to **1.546 ms**, multiplier
work to **2.076 ms**, and correction to **1.712 ms**. These measured regressions reject
this layout, not all possible GPU layouts. Cache misses, bandwidth, warp stalls and
achieved occupancy remain unmeasured: a fresh Nsight Compute attempt returned
`ERR_NVGPUCTRPERM`. No permissions were changed.

Profiling overhead varied from about −0.15% to +6.06% against adjacent ordinary runs
of the same marked binary; the negative estimate is measurement variation. Profiles
explain stages, not primary speedups. Host/GPU timestamp alignment can place kernel
tails a few microseconds beyond a host range; launch correlations retain the full
kernel sequence, while the disjoint wall partition clips activities to the ranges.

## Independent CUDA implementation

The headless adapter uses Barnden's pinned CUDA PBF constraint/correction kernels,
not a CPU solver with GPU search. Its README reports that the original renderer does not work through WSLg CUDA/OpenGL
interoperation. The adapter supplies runtime
particle allocations, matched inputs/constants, projection scaling and no rendering.
It omits the upstream constructor's 360 relaxation steps to retain the same initial
particles, raises row capacity from 256 to 512, repairs a last-bucket sentinel and
records compiler compatibility flags. All variants are headless adapters, not an
unmodified upstream application benchmark.
The original equations omit self-density; an aligned variant adds self, strict support
and prediction-time membership. A third variant filters bucket candidates by their
actual queried cell, repairing duplicate neighbours caused by hash aliases.
No upstream implementation was copied into Maelstrom.<sup><a href="#ref-s070">S070</a></sup>

The unaligned large run reached median **2.474994 s**, but had roughly 39.5% p95
over-compression and duplicate rows. This variant combines upstream formulas with
Maelstrom's constants; it is not an accuracy verdict on the original application's
own tuned scenes. The aligned search still had duplicates and is
not admitted as the comparator. Their unsuccessful results remain intact.

The repaired comparator's paired medians were **0.376793/2.035666 s**, against resident
Maelstrom **0.501243/2.390754 s**: **1.330×/1.174×**. It retains a 511-neighbour usable
row limit, different accumulation order/rounding, separate allocator/search costs,
three solver launches per iteration and no production diagnostic/rollback contract.
Its aligned formula is independently implemented; numerical and trajectory identity
are not claimed. The checked snapshots contain no truncation or duplication, not
proof that its bounded rows support every future scene. A separate full-trajectory
capacity diagnostic saw zero saturation events in six 480-step replicas per size;
a one-step cap-16 positive control triggered 7,779 events. No primary timing was
replaced, and those diagnostic clocks are not performance samples.

The search representations differ. Maelstrom sorts signed 64-bit cell-coordinate
triples with identity ties, builds compact rows through count/prefix/fill, and sorts
those rows by identity. The comparator counts/scans 32-bit hash buckets and fills
fixed-stride bounded rows once, retaining hash order. This trades generality,
determinism and capacity behaviour for less construction work. Both keep hot positions
in float3 AoS; the comparator's advantage is not a component-SoA result.

Its large GPU stages explain the observed residual advantage: constraint computation
**1.348 ms**, hash placement/scan/query approximately **1.020 ms**, and correction
**1.653 ms**. Maelstrom's correction is actually faster in these captures. The compound
advantages lie in search construction and the simpler multiplier traversal/staging;
we have not isolated every arithmetic-order, error-priority and evolved-state contribution. In the
[ordered multiplier traversal](https://github.com/Mahkrab/Maelstrom/blob/250932784790ba26cdc55fc38a877ccefacbf054/native/solver.cu#L149),
Maelstrom recomputes gradients in the greater-identity suffix to preserve the owner's
addition position. The independent kernel accumulates neighbour squares and then
adds the owner term in one pass. That is a confirmed extra traversal tied to the
rounding contract; its isolated time contribution has not been measured.
A blanket claim that native powf, unchecked arithmetic or SoA explains the gap is contradicted
by the controlled trials. The repaired comparator still simulates only about **0.49
seconds per elapsed solver second** under this fixed work policy.

## Physical and numerical qualification

The independent reader recomputes current-position, self-inclusive Poly6 density in
binary64, with a separate spatial search. It does not trust solver density arrays or
frozen prediction rows. The prospective health screen required finite state, no
coincidence, boundary violation ≤ 10⁻⁶ m and p95 positive density error ≤ 5%.
The latter is a project screen, not a claim about the published paper's quality.

| Case | p95 positive density error | Other observations |
|---|---:|---|
| Control, 8,000, one second | 8.76% | Finite, contained, no coincident particles |
| Control, 110,592, one second | 8.62% | Mean density ratio 0.9912; max positive error 20.40% |
| Repaired comparator, 110,592, one second | 8.54% | Finite/contained; similar neighbour and density distributions |
| Control, 110,592, five seconds | 20.92% | Finite/contained, but fails the density screen |
| FP32-power variant, large, five seconds | 21.13% | Similar density statistics do not establish equivalent physical accuracy |

The large control's one-second p95 errors were **11.92% within h of a wall** and
**7.39% farther away**; at five seconds they were **25.71%/19.79%**. The issue is
not exclusively a wall-layer statistic. The extended reader adds only that grouping;
all common metrics were checked identical to the original reader.

At large size FP32-power position RMS error relative to the bitwise control grew
from **4.48×10⁻¹¹ m** after one step to **0.00264/0.07324/0.34831 m** at
steps 120/240/480; maximum final displacement was **3.25 m**. FMA similarly reached
0.361 m RMS. These are trajectory differences, not errors against physical truth.
They prevent describing relaxed arithmetic as a uniformly tiny output perturbation.

Independent free-fall checks also exposed coordinate-sensitive binary32 velocity
reconstruction. Over 120 steps from y=10 m, error against the binary64 semi-implicit
recurrence was **2.448 mm in position and 0.01942 m/s in velocity**. The unchanged
kernel and relaxed variants reproduced an independently evaluated binary32 recurrence
exactly, but failed the declared 0.001 m/0.001 m/s analytic bounds. Those bounds were
not weakened. A contact fixture initially started outside its x/z planes; that setup
failure is retained, and a corrected in-bounds contact remained exactly stationary.

Parameter sweeps held simulated duration fixed, changing configurations explicitly.
These are single diagnostic runs, not final throughput comparisons:

| Large case | Resident solver s | p95 positive density error |
|---|---:|---:|
| Three iterations, refinement four | 1.421 | 26.89% |
| Four iterations, refinement four | 1.604 | 17.09% |
| Eight iterations, refinement four | 2.393, paired median | 8.62% |
| Sixteen iterations, refinement four | 4.001 | 11.50% |
| Eight iterations, refinement two | 1.192 | 8.59% |
| Eight iterations, refinement one | 0.599 | 6.96% |
| Sixteen iterations, refinement eight | 8.067 | 11.32% |

Refinement changes correction scale along with dt. More iterations/resolution did not
produce a monotonic density improvement at this endpoint, and all large cases fail
the screen. The fast coarse case is not admitted as an equivalent accurate real-time
solver. A more expensive trajectory is not automatically physical ground truth.

## Assessment and recommendation

**Do not retain these implementations in production.** This follows the user's scope and the
[assessment policy](/docs/project/development/milestones/05/performance-assessment.md),
not an automatic range or percentage veto.

1. Treat physical qualification and timestep/correction/regularisation policy as the
   next design decision. Establish density, boundary, scale-sensitive integration and
   sustained-duration error budgets before choosing fewer steps/iterations. The tested
   control itself fails the independent density screen.
2. If a new high-throughput API is wanted, design GPU-owned accepted observations and
   delayed diagnostics explicitly, with allocation, cancellation, ordered errors and
   rollback specified. The tested exact-trajectory residency experiment establishes
   about **1.25×** at large size, **not** the roughly threefold gain required by the
   current production real-time shortfall. Its fixed-capacity replay is not that API.
3. Do not prioritise removing residual FP64, global FMA contraction, disabling checks,
   or position-only SoA. Their isolated results do not support a large remaining gain;
   some lose reproducibility or regress. Preserve the retained guarded quartic.
4. Use the repaired independent solver as a reproducible experimental comparison target,
   with its remaining quality/API limits visible. Search construction and multiplier
   organisation deserve architectural study only after the numerical/ownership contract
   is chosen. The measured additional **1.17×** over resident replay is a bounded
   comparator result, not a promised production integration gain.

Other GPUs, native Linux, hardware counters, unrestricted comparator capacity,
longer independent-solver trajectories, a continuum fluid reference and an equivalent
reconstruction of the published scenes
remain unqualified. No new local kernel optimisation or production implementation
was selected. The complete independent audit, local/PC reader tests, short device
memchecks and source preservation receipts are in the evidence package. The full Rust
suite was not rerun because production code did not change; previous passes are not
represented as fresh verification.

## References used

<a name="ref-s004"></a> **S004** — Macklin and Müller (2013), *Position Based Fluids*,
Algorithm 1, §8 and Tables 1–2.
[Source record](/docs/research/sources/004-macklin-muller-position-based-fluids.md).

<a name="ref-s070"></a> **S070** — Barnden, *Position Based Fluids*, revision
`ca191d40d937a1ea44bae4032d087ac2902f9846`, README and CUDA source.
[Source record](/docs/research/sources/070-barnden-cuda-pbf.md).
