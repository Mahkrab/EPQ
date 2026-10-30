# Maelstrom performance investigation plan

## Aim and starting point

Find why Maelstrom handles substantially less work than established particle-fluid solvers, then
remove the demonstrated limits before final evaluation. The aim is useful absolute performance,
not just a large speedup over our own slow baseline. The [pre-evaluation review](/docs/project/development/pre-evaluation-review.md)
owns the original concerns; the [usability revision](/docs/project/development/usability-revision.md)
addresses the interface, not those performance problems.

Planning starts from EPQ `86e4c0ee0a2c1ce3ca312870f9a752127b455e69` and Maelstrom
[`c17d8c586eba7455582ad9597cb23d7addc3c6d9`](https://github.com/Mahkrab/Maelstrom/tree/c17d8c586eba7455582ad9597cb23d7addc3c6d9).
At planning, no new benchmark or maximum-capacity result had been obtained for this revision.
The starting commits are local checkpoints; their GitHub links require publication and do not
claim hosted verification.
Follow the applicable `AGENTS.md`; internal structure, tools and implementation remain engineering choices.

There are two tracks. **Implementation optimisation** preserves the current numerical work and
observable behaviour. **Quality/performance experiments** may revise numerical choices explicitly,
with independent qualification and new comparison identities. Contracts can change with evidence;
they are not a reason to retain an inefficient design, nor permission to disguise less work as a speedup.
Rendering changes, unrelated features and final-project synthesis are outside this investigation.

The separately requested [compilation and PC graphics repair](/docs/project/development/milestones/05/performance-compilation.md)
addresses image-producing command costs. Its timings include rendering and output and do not
replace the solver baselines or change the numerical optimisation order below.

The [optimisation assessment policy](/docs/project/development/milestones/05/performance-assessment.md) owns
retention decisions. The implementing agent must assess correctness, paired measurements,
uncertainty, regressions and implementation cost, then explain whether to retain the change.
Reports describe the evidence; they do not impose automatic percentage or range-overlap vetoes.

The [26 October CUDA code audit](/docs/project/development/milestones/05/performance-cuda-code-audit.md)
reviews the current source across timestep ownership, device algorithms and compilation. It
recommends broader residency/submission and neighbour-construction comparisons alongside bounded
arithmetic work; those recommendations do not claim an implemented change or a new benchmark.

The [timing follow-up](/docs/project/development/milestones/05/performance-compilation-profile.md)
establishes fresh same-source block-size controls and a complete compilation boundary. It retains
export instrumentation, with no numerical or block-default change. Its headless and image-producing
measurements remain separate; compilation's JSON/hash and graphics interaction are application costs.

The first [accepted-device-buffer comparison](/docs/project/development/milestones/05/performance-resident-state.md)
retains accepted vectors and static planes across timesteps. It preserves current host snapshots and
all cancellation polls, with exact results and modest matched PC gains. This is a residency foundation,
not completion of device-owned execution or the real-time target.

The separately requested [architectural and numerical-policy investigation](/docs/project/development/milestones/05/performance-architecture.md)
compares isolated ownership, synchronisation, precision and layout variants with an independent
CUDA PBF path. It preserves all ten retained optimisations, rejects production adoption of the
prototypes, and identifies independent density qualification as a prerequisite to changing solver work.
Its measurements do not authorise another local kernel optimisation.

The separately requested [pressure replacement feasibility study](/docs/project/development/milestones/05/pressure-feasibility.md)
admits a compatible staggered finite-volume pressure operator for further isolated physical-model
qualification. Its flat-domain direct solve has a measured RTX 4070 pressure budget; general moving
surfaces, material transport and viscous coupling remain unqualified. Production adoption and
further performance optimisation remain blocked on those physical gates. This does not revise
the earlier PBF failures or retain a replacement in production.

The subsequent [coupled-fluid qualification](/docs/project/development/milestones/05/coupled-fluid-qualification.md)
preserves those pressure-only results but rejects the tested geometric-VOF/averaged-staggered-mass
coupling. Conservation and surface timing pass while wave velocity/energy and collision gates fail.
No coupled CUDA benchmark was admitted. Further work requires coherent interface geometry,
staggered material transport and pressure/gravity work; production adoption remains blocked.

The requested [fast-mode application integration](/docs/project/development/milestones/05/performance-fast-mode.md)
retains explicit fast/reference selectors after full regression and fresh matched physical,
headless and rendered comparisons. The earlier 5% compression target is not an application gate.
Fast improves headless throughput and bulk compression/separation, but energy/shear regressions and
the lack of a large-scene compilation gain do not justify making it the universal default.
The existing default selection remains unchanged; no further formulation work was initiated.

The subsequent [complete compilation assessment](/docs/project/development/milestones/05/performance-render-pipeline.md)
retains a bounded CPU encoding/hash worker after matched complete-command comparisons at both
particle counts and in both modes. Saved-state probes separate trajectory costs from the observed
graphics/clocking interaction. This application change preserves the numerical policies and all
ten CUDA optimisations; it does not revise the earlier mode assessment or default recommendation.

The [snapshot provenance follow-up](/docs/project/development/milestones/05/performance-snapshot-provenance.md)
retains fixed-schema buffered hashing after byte-exact saved-state checks and complete compilation
comparisons. It removes the large fast-mode output wait while preserving canonical JSON, hashes,
the parallel pipeline and all numerical policies. Its timings remain separate from the pipeline campaign.

An earlier explicit user instruction selected fast as the application default. The subsequent
instruction on 30 October 2026 restores reference as the default and saves the reference schedule
in every built-in scene package. Fast remains opt-in through `--numerical-mode fast` or the
`numerical_mode` application preference. Both presets retain their values; historical assessments
above retain their original decisions. The [catalogue record](/docs/project/development/milestones/05/builtin-scenes.md)
describes the corresponding output-stride revision.

The [built-in scene overhaul](/docs/project/development/milestones/05/builtin-scenes.md)
packages varied examples with energy colouring and fitted cameras. Its retained full-compilation
checks establish catalogue behaviour and output equivalence, without adding a physical-quality claim.

## What the external targets actually mean

The original PBF paper reports Armadillo Splash at 128k particles, two steps per 16 ms frame,
three iterations per step and 4.2 ms per step on a GTX 680. Its dam-break example uses 100k,
four steps per frame, three iterations per step and 4.3 ms per step. These are concrete reference
points, not a direct slowdown ratio for Maelstrom's different scene, refined timestep and eight
iterations. Simulation-step time, simulated frame duration and display FPS are not interchangeable.<sup><a href="#ref-s004">S004</a></sup>

Use a small, purposeful set of comparators rather than collecting impressive videos:

| Source | Role in this investigation | Important distinction |
| --- | --- | --- |
| Original PBF, S004 | Published particle-count, timing and quality targets | Reconstruct each reported workload; do not combine figures from different examples |
| SPlisHSPlasH, S060 | Primary runnable PBF comparator; study its iteration loop and OpenMP implementation | Select PBF explicitly; its convergence, constraint and boundary choices differ from ours |
| CompactNSearch, S061 | Study compact hashing, neighbour queries and spatial ordering | A search library, not a complete fluid solver or a published Maelstrom speedup |
| GPUSPH, S062 | Study an established CUDA fluid implementation's storage and execution approach | WCSPH, not PBF; use for architectural lessons, not an equivalent pressure-solver benchmark |

Those roles follow the inspected upstream README files and SPlisHSPlasH PBF implementation.<sup><a href="#ref-s060">S060</a>, <a href="#ref-s061">S061</a>, <a href="#ref-s062">S062</a></sup>
Pin upstream code and build options before testing. Inspect relevant kernels and data ownership,
not just interfaces. Record useful techniques, their trade-offs and whether they fit Maelstrom;
review licences before copying code or introducing a dependency. No upstream installation or
whole-code adoption is required merely to begin profiling.

The initial engineering ambition is sustained **100,000 or more particles at real-time simulation
speed** on the primary PC under declared quality settings. Measure real-time factor as simulated
seconds divided by elapsed seconds: at least one means keeping pace. Record solver-only and complete
headless-run factors separately. Reaching a particle count through allocation or one successful step
does not meet this ambition. Extend towards roughly 250k and 500k only when measured limits permit.
These are targets to test, not promised outcomes or retrospective acceptance thresholds.

## 1. Establish the comparison and diagnose the costs

The [diagnosis protocol](/docs/project/development/milestones/05/performance-protocol.md) specifies the initial
requests, capacity bounds, comparator admission and quality criteria before collection.
The [completed diagnosis](/docs/project/development/milestones/05/performance-diagnosis.md) records the retained
baseline, capacity decisions, comparator runs and ranked costs. Implementation optimisation remains open.

Run important measurements on the PC through `ssh pc`. First reproduce current release behaviour
with explicit backend/resources and `--unpaced`, without rendering. Preserve the existing seven-size,
480-step refined comparison as the regression anchor. Record exact source, inputs, build, driver,
hardware, observation policy and timer boundaries; do not splice old and new samples together.

Add a separately named capacity family at 8,000, 32,768, 110,592, 262,144 and 512,000 particles
(20³, 32³, 48³, 64³ and 80³). Retain spacing, support ratio and numerical configuration while
extending the block and enclosing domain. Specify geometry, plane order and checkpoints before
collection; the current playground is editable and must not become an implicit benchmark.
Pilot setup and a few steps before admitting a longer run. Predeclare memory/time ceilings and
stop unsafe or impractical sizes; retain skipped estimates, failures, timeouts and accepted prefixes.
Use representative early and settled motion, not only an initial lattice or empty neighbourhood.

Build a cost breakdown that can distinguish the following explanations:

| Suspect | Current evidence and measurement needed | Decision the evidence should support |
| --- | --- | --- |
| Neighbour storage/traversal | The [CUDA allocation](https://github.com/Mahkrab/Maelstrom/blob/c17d8c586eba7455582ad9597cb23d7addc3c6d9/src/cuda/solver.rs#L110) reserves `4 × N × ceil(N/32)` membership bytes; [iteration](https://github.com/Mahkrab/Maelstrom/blob/c17d8c586eba7455582ad9597cb23d7addc3c6d9/native/solver.cu#L60) scans row words. Measure allocated/peak memory, actual neighbour counts, words visited and traversal time as N grows | Replace all-pairs-shaped storage and scanning if they dominate capacity or repeated work |
| Host/device transfers | [Each attempt](https://github.com/Mahkrab/Maelstrom/blob/c17d8c586eba7455582ad9597cb23d7addc3c6d9/src/cuda/solver.rs#L140) repacks/uploads state and reads back intermediate state/error arrays. Count calls, bytes, packing/allocation and transfer durations separately | Keep necessary state resident, reduce diagnostic traffic and reuse storage where measured |
| Synchronisation and launches | The [native wrapper](https://github.com/Mahkrab/Maelstrom/blob/c17d8c586eba7455582ad9597cb23d7addc3c6d9/native/bridge.cpp#L180) completes its stream per solver call. Trace host submissions, waits, GPU gaps and kernel durations, including sort passes | Remove unnecessary host barriers or submission overhead without removing true data dependencies |
| Repeated arithmetic | [Numerical passes](https://github.com/Mahkrab/Maelstrom/blob/c17d8c586eba7455582ad9597cb23d7addc3c6d9/native/solver.cu#L140) revisit distances, kernels and gradients. Check generated code, instruction cost, register pressure, memory traffic and safe invariant reuse | Distinguish required recalculation after position changes from genuinely redundant work; avoid guessing that `sqrt`, division or power dominates |
| CPU coordination | Profile packing, allocation, sorting, active-neighbour filtering, multiplier/correction passes, pool barriers and serial checks | Improve CPU backends and host orchestration where they materially limit time; a busy core alone proves neither useful arithmetic nor GPU starvation |

Include the [custom power function](https://github.com/Mahkrab/Maelstrom/blob/c17d8c586eba7455582ad9597cb23d7addc3c6d9/native/power.cuh#L38)
in the arithmetic investigation: it uses binary64 intermediates to reproduce host rounding. Quantify
the cost of that compatibility policy rather than assuming all device arithmetic is binary32.
Replacing it with native `powf` or repeated multiplication needs a demonstrated equivalence or a
separately qualified arithmetic contract; similar algebra alone is not enough.

Start with a focused Nsight Systems CPU/CUDA timeline; use Nsight Compute only for expensive kernels
needing instruction, memory or occupancy evidence. Their collection modes can perturb execution,
so keep profiles separate from uninstrumented timing samples.<sup><a href="#ref-s063">S063</a>, <a href="#ref-s064">S064</a></sup>
Check availability and permissions on the actual WSL setup. If a feature is unavailable, retain the
failure and use bounded host counters/device events where supported; mark attribution unresolved.
Do not change host security, drivers or OS settings merely to obtain a profile.

Reconcile solver wall time with the timeline without adding overlapping CPU/GPU intervals twice.
Separate cold setup, steady-state stepping, audits, observation copies, output and shutdown. Establish
a no-render core-throughput case alongside the unchanged observation-rich regression case; report
any changed output contract rather than presenting the former as the historical measurement.

For external runs, record solver/version, precision, hardware, particle spacing/support and observed
neighbour counts, geometry/boundaries, timestep/substeps, iteration or convergence policy, enabled
effects, simulated duration, quality and timed scope. Prefer a same-PC headless SPlisHSPlasH PBF run.
Its PBF code has a density-error stopping condition and different constraint handling; identical N
and a method name do not establish equivalence.<sup><a href="#ref-s060">S060</a></sup>
Treat unmatched published results and other SPH methods as contextual targets, with every mismatch
visible. Define density-error, stability, boundary and long-run failure criteria before quality tuning.
Different solver formulations need declared quality bounds, not bitwise agreement with one another;
unchanged-contract Maelstrom optimisations retain their existing exactness requirements.

**Done when:** a retained baseline, comparator specification and ranked cost breakdown explain the
known limits or clearly identify what remains unmeasured. Rank by total-time share, growth with N
and achievable capacity; use the removable share to bound plausible speedup before choosing work.

## 2. Remove the dominant implementation limits

The first [compact-neighbour experiment](/docs/project/development/milestones/05/performance-compact-neighbours.md)
records the implemented storage change, necessary copy-ordering repair and matched PC evidence.
The subsequent [batched-sort experiment](/docs/project/development/milestones/05/performance-sort-batching.md)
addresses the measured per-pass host waits without changing the sort kernels.
The [diagnostic-readback experiment](/docs/project/development/milestones/05/performance-diagnostic-readback.md)
retains a modest further gain after rejecting a separate-reduction-kernel candidate.
The [logical-stage batching experiment](/docs/project/development/milestones/05/performance-stage-batching.md)
records the matched PC gain from grouped submissions at the existing Jacobi and projection
cancellation boundaries, with deterministic numerical failure handling.
The [multiplier-prefix reuse experiment](/docs/project/development/milestones/05/performance-gradient-reuse.md)
records a rejected register-only arithmetic trial: measured kernel savings did not meet
its prospective whole-solver admission criterion, so that trial restored the original multiplier.
That outcome belongs to the historical policy and remains unchanged.
The subsequent [prefix reassessment](/docs/project/development/milestones/05/performance-gradient-reassessment.md)
retains reuse after scene usability: fresh primary-PC comparisons improved both larger workloads,
including a separately identified case with both fluid effects enabled. Its record also preserves
a disqualified first campaign and the native-build verification that corrected it.
The [cooperative sorting experiment](/docs/project/development/milestones/05/performance-cooperative-sort.md)
then retains warp-per-row integer sorting for bounded rows, with unrestricted heapsort fallback.
Its matched comparisons include the extra kernel and preserve the prefix implementation in both variants.
The [host-coordination attribution](/docs/project/development/milestones/05/performance-coordination.md)
then separates bounds, CFL and prefix calculations from transfers and packing. Their small measured
share and the fresh correction ranking defer standalone device reductions/scans for now.
The [reused-reservation investigation](/docs/project/development/milestones/05/performance-reservation-reuse.md)
records a rejected host-only fast path: removing empty driver waits produced no clear
matched PC runtime gain. That trial restored the original reservation boundary. The later
accepted-buffer comparison changes fixed-lifetime preparation and state ownership together;
it does not relabel that earlier outcome.
The [correction-cost investigation](/docs/project/development/milestones/05/performance-correction-profile.md)
adds full early/evolved profiles and records a rejected power-table placement trial.
The [host-acceptance investigation](/docs/project/development/milestones/05/performance-host-acceptance.md)
measures individual components before trying inlining. Its original range-separation rule caused
a reversion despite substantial savings. The subsequent documented assessment retains the simple
inlining change: every confirmation pair improved, component probes and traces supported the
mechanism, and numerical behaviour was preserved. The original failed rule outcomes remain intact.
The [neighbour-traversal investigation](/docs/project/development/milestones/05/performance-neighbour-traversal.md)
retains a narrow cell-lookup reuse change after rejecting a merged-range scan that slowed
evolved motion. The follow-up improved every large pair with a roughly 2% median saving;
the smaller workload was mixed. Both campaigns and their differing outcomes remain intact.
The [entry-point specialisation trial](/docs/project/development/milestones/05/performance-kernel-specialisation.md)
completed both a full split and a targeted numerical-pass follow-up. Lower register counts did
not establish a useful larger-workload benefit; neither candidate is retained. Their patches,
complete measurements and written assessments remain separate from the active solver.
The [neighbour attribution](/docs/project/development/milestones/05/performance-neighbour-attribution.md)
separates evolved traversal, fill and identity sorting. Sorting is substantial; writes add
less than the checked traversal in the diagnostic export. Generated PTX already shares local
distance expressions within individual loops, leaving cross-loop reuse as the stronger arithmetic
candidate. The reviewed implementation candidates are listed below. Timing
variability must remain visible, and individual power-function cost remains unresolved.
The remaining implementation work is still open; further host/device round trips and
kernel costs still need evidence-led assessment.

Make one attributable change at a time, then reprofile. Compact neighbour storage is the leading
capacity candidate, not an instruction to ignore a different measured bottleneck. Compare compact
offset/index lists or another justified local representation; account for count/build/sort costs,
growth, dense cells and overflow. Never silently cap neighbours. Retain prediction-time membership,
strict support, self-contribution rules and identity-ordered arithmetic. Spatially reordered storage
must map back to stable identities without silently changing summation order.
Use separate build directories and verify embedded CUDA code against each source export;
source and executable hashes alone do not establish that the intended native code was rebuilt.

If the timeline supports it, retain accepted/candidate state on the device, avoid unchanged uploads,
reduce error transfers to the required deterministic result, and enqueue dependent work without a
host round trip at every kernel. Preserve atomic acceptance, error precedence, cancellation boundaries,
retry, context ownership and accepted snapshots. Do not fuse across a required Jacobi dependency
or remove checks to make a graph look faster. Qualify altered failure/observation boundaries explicitly.

Next address measured sorting, allocation, cache/layout, CPU scheduling or arithmetic costs.
Precompute only values invariant over their actual lifetime; positions change during correction,
so stale distance/gradient caching is not an optimisation. Graph submission, kernel fusion, different
sorting algorithms and launch tuning need a demonstrated cost to remove, not adoption by fashion.
Fast maths, changed reduction order, approximate powers and lower precision are numerical variants.

### Candidates after the code review

The [CUDA candidate review](/docs/project/development/milestones/05/performance-candidate-review.md) maps the
seven proposed techniques to current source, prior trials and retained profiles. They are
experiments to assess, not a requirement to apply every technique or a promise of a speedup.

| Candidate | Intended first experiment |
| --- | --- |
| Dedicated operation kernels | Full and targeted trials completed without a useful larger-workload gain; reconsider only with a new operation-specific hypothesis |
| Pair geometry reuse | Ordered gradient-prefix reuse is retained; further fusion or suffix reuse needs a separate hypothesis. Local correction-distance sharing is already present in the inspected generated PTX |
| Neighbour-loop fusion | Consider partial density/owner fusion or ordered prefix/suffix reuse; preserve the owner's insertion point and error precedence |
| Device component [SoA](https://en.wikipedia.org/wiki/AoS_and_SoA) | Compare hot position storage first, including packing/gather/readback costs; a whole-application representation rewrite is not required |
| Warp-cooperative row work | Cooperative identity sorting is retained through 256 entries, with larger rows keeping heapsort; other cooperative work needs a separate access-pattern hypothesis |
| Shared-memory tiles | Establish repeated block-local neighbour access before adding staging, barriers and shared storage |
| Validation efficiency | Prove individual redundancies or unused diagnostic writes; disabling production `Checked` changes failure handling and needs a separately revised contract |

Attribution, initial instruction inspection, the entry-point trial, prefix reassessment, cooperative
integer sorting, host-coordination attribution, compilation/block-size measurement and the first
accepted-buffer residency comparison are complete. Next prioritise a separate device cell-run indexing
comparison against repeated neighbour searches. Broader residency and larger checked submissions still
need explicit observation, rollback, cancellation, allocation and error boundaries before implementation.
Continue bounded correction-arithmetic and invariant-coefficient inspection alongside them. Keep retained
sorting, prefix reuse and accepted-buffer ownership in the control. Standalone device reductions/scans
remain deferred; this does not rule out their use within a broader residency change.
Choose further arithmetic reuse, layout and cooperative-memory work from the measured
access and sorting costs. Do not use shuffle reductions to change floating-point summation order.

Keep device-side bounds, checked integer prefixes and state residency in view: the current path
still downloads predicted positions and row counts, computes the prefix on the host and uploads
offsets. Preserve allocation/error decisions and explicitly qualify any accepted-state ownership
change. Inspect invariant kernel coefficients before introducing a full per-pair cache.

Compilation snapshot copies and image-pipeline overlap are separate application-throughput
candidates in the review; their gains cannot be reported as solver-only improvements. The fresh
profile makes bounded CPU frame preparation overlap more promising than snapshot-copy removal.
Trace the increased solver/graphics cost with every-step images before attributing its cause.

The [compiler assessment](/docs/project/development/milestones/05/performance-compiler-assessment.md)
confirms optimised release/device builds and records a separate ThinLTO/one-unit trial.
Ordinary release remains the default: the measured CUDA workloads do not establish a
broad runtime benefit. CPU profile tuning remains open; precise numerical flags stay intact.

**Done when:** each retained change passes independent normal/failure tests and matched PC comparisons,
and has a recorded speed/memory benefit or a justified capacity benefit with its runtime trade-off.
Reject noise-level wins and regressions disguised by changed work. Keep historical inputs/results intact.

## 3. Test competitive quality and capacity

Repeat the capacity ladder and the original controls after each substantial improvement. Use warm-up
and at least five independent timing samples for admitted final before/after cases, alternating their
order where practical; report median, spread, per-step distribution, real-time factor and peak memory.
Keep fixed observation schedules and check equivalent physical endpoints. At larger sizes, combine
small independent oracles, cross-backend checks where feasible and declared physical-health audits;
do not require an impractical full brute-force trajectory merely to admit a capacity test.

If implementation work alone leaves a substantial gap, run the separate quality/performance track.
Investigate why our refinement, iteration count, regularisation or convergence needs differ from
the PBF comparators. Use explicit experimental configurations and error-versus-cost curves, not a
lower iteration count selected because it looks faster. Requalify affected numerical and measurement
contracts and apply revisions to every backend in a new matched comparison. Do not replace the solver
method with DFSPH or WCSPH and still call the result a transparent PBF optimisation.

**Done when:** sustained large-scene tests quantify how close we are to the 100k-plus ambition and
the selected PBF reference workloads, with quality and timing differences disclosed. Allocation-only,
warning-producing, unstable or timeout-limited runs cannot count as achieving the target. An unmet
target needs a quantified shortfall and next decision, not a claim that the performance problem is solved.

## 4. Record the result and decide evaluation readiness

Keep a concise decision record with the culprit evidence, rejected hypotheses, individual changes,
before/after costs, correctness results, capacity limits and remaining comparator mismatches.
Retain raw commands/results/profiles, environment and exact source identities, including failed runs.
Record only checks actually performed; local tests are not hosted evidence or fresh PC qualification.

**Done when:** important performance limits are removed or explicitly dispositioned, target attainment
is honestly assessed, and the [evaluation plan](/archive/plan.md) can
select defensible new comparisons. An unexplained large performance gap remains open. This plan
does not authorise commits, branches, tags, remote changes or a final evaluation campaign.

## References used

<a name="ref-s004"></a> **S004** — Macklin and Müller (2013), *Position Based Fluids*, author preprint, §8 and Table 1.
[Source record](/docs/research/sources/004-macklin-muller-position-based-fluids.md).

<a name="ref-s060"></a> **S060** — Bender and contributors, *SPlisHSPlasH*, pinned README and PBF implementation.
[Source record](/docs/research/sources/060-splishsplash-pbf-implementation.md).

<a name="ref-s061"></a> **S061** — Koschier and contributors, *CompactNSearch*, pinned README.
[Source record](/docs/research/sources/061-compactnsearch.md).

<a name="ref-s062"></a> **S062** — GPUSPH developers, *GPUSPH*, pinned README.
[Source record](/docs/research/sources/062-gpusph-cuda-fluid-solver.md).

<a name="ref-s063"></a> **S063** — NVIDIA, *Nsight Systems User Guide*, focused profiling and CUDA tracing.
[Source record](/docs/research/sources/063-nsight-systems-profiling.md).

<a name="ref-s064"></a> **S064** — NVIDIA, *Nsight Compute Profiling Guide*, metric collection and overhead.
[Source record](/docs/research/sources/064-nsight-compute-profiling.md).
