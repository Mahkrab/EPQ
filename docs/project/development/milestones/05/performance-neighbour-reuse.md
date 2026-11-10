# Neighbour construction and numerical traversal reassessment

**Reject all three prototypes; retain the current implementation.** A fresh RTX 4070
comparison finds no useful complete-viewer gain from cooperative discovery, spatially
grouped tiles or exact per-membership geometry caching. These are implemented and tested
experiments, preserved as reconstructible patches. None replaces production CUDA code.
The real-time objective remains unmet.

The [evidence collection](/docs/project/development/milestones/05/assets/neighbour-cooperative-v1/README.md)
contains the prospective protocol, source/executable/PTX identities, all requested samples,
full-motion attribution, qualification and rejected patches. It extends the
[tiled-row assessment](/docs/project/development/milestones/05/performance-timestep-critical-path.md)
without replacing its results or pooling its samples.

## Fresh baseline and measurement boundaries

Both repositories began with existing uncommitted work, including the reviewed tiled rows
and their parent tooling/evidence. Parent HEAD is `e7664ee354246507928ac0d80758cffceef0072d`;
Maelstrom HEAD is `6bf2682325b7665e48f8a8647ce087d48ff13f0b`. Neither commit alone identifies
the measured source. The frozen 266-file working export, its control patch and independently
verified embedded source/PTX identify this control. Its source digest is
`89ad00ed994f82d6c052e5bbebe9a5eec4f581cdc53293250244fc8fa412a529`.

Measurements use the primary PC through `ssh pc`, hardware X11/GL, analytic sphere impostors,
1280×720, CUDA device 0/block 128 and the existing 8,000/32,000/110,592-particle inputs.
Every ordinary invocation starts a new simulation and accepts 1,200 timesteps: experimental
240 Hz, eight Jacobi iterations, correction 0.25 and relaxation 20. No steps are dropped.

Fresh control warm-ups/samples precede the prototypes. Each prototype then receives a
large-scene warm-up pair and two alternating measured pairs. The least-regressing prototype,
spatial tiles, additionally receives a separate warm-up plus three alternating pairs at
all three counts. This completes the requested size coverage without reopening its rejection
based on smaller workloads. Sample order, slower runs and command times remain visible.
No task build, test or diagnostic collection overlaps ordinary PC measurements.

Complete solver clocks include validation, CUDA submission/completion, materialisation and
acceptance. Viewer advancement is actual simulated seconds per monotonic wall second,
measured from accepted progress in the existing frame traces. Command time, snapshot copying,
frame cadence and instrumented traces remain separate. Surface presentations do not establish
physical scan-out or input latency. Absolute control rates differ from the previous session;
that change is not credited to an optimisation.

## Where the remaining work goes

The fresh control's separate full-motion trace gives these GPU milliseconds per timestep:

| Stage | 8,000 | 32,000 | 110,592 |
| --- | ---: | ---: | ---: |
| Density and multipliers | 0.2655 | 0.4424 | 1.3305 |
| Position correction | 0.2884 | 0.5132 | 1.7497 |
| Neighbour count | 0.1069 | 0.2114 | 0.7316 |
| Neighbour fill | 0.1192 | 0.2670 | 0.8967 |
| Spatial sort | 0.0417 | 0.0743 | 0.2303 |
| Row identity sort | 0.0066 | 0.0688 | 0.2693 |
| Tile prefix | — | 0.0164 | 0.0621 |
| All solver GPU activity, including copies | **0.9070** | **1.7143** | **5.5555** |

At the large size, density/correction occupy 3.0802 ms and count/fill 1.6283 ms:
about 55% and 29% of solver GPU activity. These remain the principal device costs.
Counting and filling each perform the same nine sorted-column searches and checked candidate
distances. Identity sorting and checked prefixes are smaller costs; simply removing those
stages would not close the gap. The numerical stage visits fixed prediction-time rows,
recalculates current geometry and preserves ascending identity accumulation. The density
pass also revisits the higher-identity squared-gradient suffix. Across eight iterations,
those numerical traversals visit about twenty times the directed fixed membership count.
This is a logical-work count, not measured DRAM traffic.

The full large timestep still submits **70 kernels and 21 stream waits**, in every prototype.
Its instrumented control takes 8.2592 ms, including 5.5555 ms of solver GPU activity and
2.7037 ms outside that activity. Those two disjoint quantities reconcile the interval.
Inclusive wait/API durations must not be added again. The ordinary 7.8140 ms solver median
below is the performance measurement; the traced interval includes instrumentation and a
different collection window. No bandwidth, cache-hit, warp-stall or achieved-occupancy counter
was obtained or inferred.

## Implemented experiments and decisions

The exploratory large-scene results below use the median of each prototype's two measured
pairs; their warm-ups and final spatial comparison are separate datasets.

| Prototype | Complete solver ms, control → prototype | Viewer simulated s/wall s, control → prototype | Decision |
| --- | ---: | ---: | --- |
| Warp-cooperative neighbour discovery | 7.7431 → 11.9312 | 0.53241 → 0.34662 | **REJECT** |
| Spatially grouped tiled rows | 7.7511 → 8.8079 | 0.53219 → 0.46817 | **REJECT** |
| Exact weight/gradient cache | 7.7650 → 11.2282 | 0.53069 → 0.36779 | **REJECT** |

**Cooperative discovery** assigns a warp to each spatially scheduled owner. Lanes evaluate
consecutive candidates and use integer ballots to count/compact members, preserving visit
order, checked distances, unrestricted rows and deterministic errors. A dedicated entry
avoids changing the numerical kernel. It adds no neighbour cache or allocation. Both measured
pairs regress: viewer ratios are 0.6550 and 0.6471. The separate trace places count/fill at
2.9331/3.0712 ms, against 0.7316/0.8967 ms in control. Parallel candidate checks do not earn
their extra execution/mapping cost on this workload. The exact hardware cause is unresolved.
No smaller cooperative widths were pursued.

**Spatial tiles** retain identity-indexed logical offsets but group physical tiled rows by
the existing cell permutation. An inverse map in unused sort scratch connects identity to
physical row. Numerical lanes follow the same spatial groups; each row still accumulates
identical members in identical identity order. This differs from the earlier rejected
spatial-only scheduling trial because membership storage changes with scheduling.

It nevertheless regresses both exploratory pairs. The trace shows density/correction at
1.4734/1.8247 ms, tile prefix at 0.3226 ms and additional costs in lightweight scattered
publication, candidate and projection passes. Together these explain a complete cost increase;
no exclusive cache-level explanation is established. A narrower scheduling variant was not
pursued: removing the measured lightweight-pass overhead alone would not establish an
end-to-end gain, and the expensive traversals themselves are slower.

The requested three-size final comparison confirms this decision:

| Particles | Complete solver ms, control → spatial | Viewer simulated s/wall s, control → spatial |
| ---: | ---: | ---: |
| 8,000 | 2.086412 → 2.092717 | 2.025582 → 2.019445 |
| 32,000 | 3.173592 → 3.559222 | 1.314189 → 1.172100 |
| 110,592 | 7.813976 → 8.735378 | 0.527010 → 0.471978 |

All three large final pairs regress, with viewer ratios 0.8843, 0.8907 and 0.8956.
Raw samples, ranges, command times and frame tails remain in the comparison receipt.
No formal statistical-significance or other-machine claim follows from three pairs.

**Exact geometry reuse** stores the already rounded Poly6 weight and Spiky direction in a
16-byte per-membership record during grouped density evaluation. An inactive sentinel keeps
strict support membership; the multiplier suffix and correction reuse values while positions
remain immutable. Standalone component calls retain the original path. Self insertion,
ordered sums, artificial-pressure arithmetic, staged error priority and barriers remain.

The cache appends records after the membership indices in the same checked allocation and
only applies at tiled sizes. It removes repeated expressions but adds record traffic and
resource demands. Both exploratory viewer ratios regress, to 0.6912 and 0.6950. Separate
GPU density/correction costs rise to 4.1662/2.3657 ms; all solver GPU activity rises to
9.0157 ms. Fewer calculations are not a throughput result. This representation is rejected;
no cache-width or layout variants were pursued.

| Separate full-motion GPU trace, ms/step | Control | Cooperative | Spatial tiles | Geometry cache |
| --- | ---: | ---: | ---: | ---: |
| Density/multipliers | 1.3305 | 1.3339 | 1.4734 | 4.1662 |
| Corrections | 1.7497 | 1.7795 | 1.8247 | 2.3657 |
| Count + fill | 1.6283 | 6.0043 | 1.6384 | 1.5903 |
| All solver GPU activity | 5.5555 | 9.9795 | 6.5272 | 9.0157 |

These traces cover all 1,200 steps, including evolved motion. They explain the measured
regressions and are not ordinary benchmark samples.

Driver-loaded resource queries report 59 registers/thread and 16 local bytes for the
control, cooperative-build and spatial-build general solver; the dedicated discovery entry
uses 54 registers and no local bytes. Geometry caching raises the general solver to 63
registers, with the same 16 local bytes. Spatial sort and prefix resource requirements
match. These are static requirements, not achieved occupancy or proof of a regression's
exclusive hardware cause.

## Memory and capacity

Separate storage-instrumented trajectory runs reproduce the same accepted-state witnesses;
they are not performance samples. Their fresh measurements are:

| Representation | Particles | Mean tile padding | Peak reserved neighbour bytes |
| --- | ---: | ---: | ---: |
| Current compact | 8,000 | 0% | 1,233,072 |
| Current identity tiles | 32,000 | 21.50% | 8,366,400 |
| Current identity tiles | 110,592 | 15.64% | 28,785,024 |
| Rejected spatial tiles | 110,592 | 12.85% | 29,251,584 |
| Rejected geometry cache | 110,592 | 15.64% | 143,925,120 |

These are neighbour-allocation reservations, including geometric growth slack, not total
context memory. Spatial grouping reduces average padding but does not reduce peak retained
reservation: its changing row sizes lead to a different growth history. Its inverse map
uses 442,368 bytes inside existing sort scratch at 110,592; no new allocation is needed.
The geometry cache grows each physical slot from 4 to 20 bytes, multiplying the actual peak
neighbour reservation by five. None of these memory costs buys a throughput gain.

Current tiles still have a pathological padding bound approaching 32 times compact rows
when one identity per tile has a much larger degree than its peers. This investigation does
not remove that existing capacity risk. There is no neighbour cap or approximate selection.
Rust size/capacity checks and recoverable allocation exhaustion remain in current production.

## Verification and limitations

All three prototypes passed 34 explicitly enabled CUDA component tests before their admitted
viewer measurements. Existing independent CPU bit oracles cover density, constraint,
multiplier and correction, including strict support, signed zero, changed snapshots,
dense fallback, sparse/empty/tail rows, extreme geometry, error ordering and retries.
The spatial prototype also checks its physical rows and inverse mapping against a CPU
cell-order oracle; it does not use its own GPU membership as the expected result.

Seventeen control/spatial trajectory pairs cover 6,960 accepted timesteps per build:
experimental runs of 1,200 steps at each size; reference, fast, paper-baseline and scene
runs of 240 steps at each size; and experimental effects runs at both larger sizes.
Every accepted-state raw-bit digest and per-step CFL record agrees. Cooperative discovery
and geometry caching each additionally match the control's complete 1,200-step large
trajectory. Agreement preserves observed fluid behaviour; it is not a new independent
physical-quality qualification.

Fresh production qualification passes 356 ordinary release tests, with 67 opt-in tests
ignored in that invocation; 34 explicitly enabled solver CUDA checks; one device-boundary,
seven CUDA execution, two hardware graphics and 12 viewer-model checks. These groups overlap
the ordinary suite. Strict all-target CUDA/viewer Clippy and native injected-driver ASan/UBSan
checks pass. Compute Sanitizer memcheck reports zero errors for empty/tail/zero-allocation
rows, independent tiled intermediates and complete cancellation/retry attempts at 32,000.
The fault suite covers allocation exhaustion, failed submission/completion/binding, resource
poisoning and recovery boundaries through injected drivers, not actual device loss.
Twenty-one local parent timing/viewer/render reader tests also pass.

`cargo fmt --check` reports exactly the pre-existing trailing space on `Settings.count` in
`src/cuda/solver.rs`; that user change is preserved. The rejected prototypes do not receive
a production-retention claim from these checks or a complete device-sanitiser qualification.

Two recorded-input reruns recompute all 1,200 large-scene steps with control and spatial
executables and match the saved states and complete diagnostics exactly. The actual
hardware impostor harness yields 27 identical pixel/state records across all three counts,
steps 0/240/1,200 and three cameras. These are offscreen hardware comparisons, not physical
desktop scan-out witnesses. Their test-only renderer selection overlay is recorded separately
and never enters production source.

The first spatial preflight exposed a new dependency on completed cell-sort scratch in a
standalone prefix fixture that deliberately poisoned that scratch. The rejected prototype
now diagnoses out-of-range cell indices before offset access; the valid fixture builds
its required cell permutation with an explicit valid width. The invalid-count assertion
still rejects before scratch reuse. The failed runs and the subsequent 34/34 passing run
are retained, including the initial device-fault cascade. No test was weakened or disabled.

A prior executable was rejected before fresh baseline collection because its source receipt
differed by a pre-existing trailing space. A fresh build was used. A later trajectory build
reused a stale shared Cargo artefact; the embedded-source check caught it before comparison.
Explicit build-script refresh and receipt verification repaired that witness. Ordinary
measurement binaries all passed their source and embedded-PTX checks. The failures remain
in the evidence and are not counted as qualified comparisons.

## Real-time assessment

With no new production optimisation retained, the fresh final control advances
**0.527010 simulated seconds per wall second** at 110,592 particles. It needs another
**1.8975× actual viewer throughput** to reach real time. Its complete solver median is
**7.813976 ms**, **3.647309 ms above** the 4.166667 ms timestep budget, before separate
observation publication. There is no performance improvement to claim from this work.

The existing tiled representation, all previously retained CUDA optimisations, numerical
modes, renderer, compilation/parallel encoding, canonical hashes, scene/replay compatibility
and accepted-state recovery remain in production. All prototype source changes stay in
reconstructible rejected patches. No installed executable, ordinary PC checkout, driver,
clock/power setting, branch, commit, tag, remote or parent gitlink changed. Hardware-loss
recovery and sustained real-time capacity remain unqualified.
