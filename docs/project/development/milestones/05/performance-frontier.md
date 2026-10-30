# Particle-PBF throughput and practical physical quality

The bounded study found a worthwhile state-ownership optimisation, but no acceptable numerical policy for the existing PBF formulation. At 110,592 particles, an isolated device-owned interface reduced five-second solver/observation cost from **3.900 to 3.628 wall seconds per simulated second**, a **7.0% reduction**. Faster numerical policies ran near or above real time, but failed the predefined density, separation, hydrostatic or energy screens. None is recommended for production.

The next implementation path is explicit GPU ownership with qualified observation/failure handling, followed by a bounded author-reference DFSPH comparison. Further custom grid-fluid development is not recommended at this point. DFSPH has not been qualified or timed on the RTX 4070 in this study.

## Scope, identities and measurement

The assessed production source was Maelstrom `250932784790ba26cdc55fc38a877ccefacbf054`, exported read-only and built afresh on the primary PC. The GPU was an RTX 4070 with 12,282 MiB reported memory and driver 610.88. CUDA and compiler identities, binary hashes, commands and logs are retained in the [evidence directory](/docs/project/development/milestones/05/assets/pbf-frontier-v1/README.md). Both repository HEADs and staged content were preserved; all 346 initially inventoried files remained byte-identical. The pre-existing test relocation and earlier investigation work were left intact.

The new scenes are declared workloads, not an attempt to reinterpret historical timings: an 8,000-particle resolved falling block; a full-width, eight-layer hydrostatic tank with 3,200 particles; a two-block collision with 3,456; a spreading free surface with 3,200; unforced shear with 8,000; and a 110,592-particle falling block. Geometry stayed fixed within each scene. The small-scene screen ran for two simulated seconds, except shear at 0.2 seconds; the large-scene screen ran for one second. Selected cases extended to five seconds. There were **121 PBF trajectories**, each with production timing and a matching native quality replay.

Production timings sum complete, ordinary, unprofiled solver calls per actual simulated second. They include checks, allocation/growth, host coordination and accepted-state installation; they exclude construction, teardown, recording, rendering and independent audits. Screen and long-trajectory costs are exploratory single measurements. The final residency comparisons used a warmup and **five independent alternating pairs**; observation costs were included. No builds, CPU audits or other GPU jobs ran concurrently with those admitted comparisons. The native recorder's timings are not production measurements.

An independently written binary64/current-neighbour audit measured density, occupied support volume, separation, containment, centre of mass, momentum and kinetic/potential energy. Every replay endpoint matched its production endpoint exactly. This establishes which trajectory was audited; bitwise agreement is not a physical acceptance criterion.

## Prospective acceptance and independent controls

The [protocol](/docs/project/development/milestones/05/assets/pbf-frontier-v1/protocol.json) preceded collection. Practical acceptance required all of:

- Sampled p95 positive compression ≤5%, maximum compression ≤25%, finite contained state, no coincidences and separation ≥0.5 particle spacings.
- Occupied-support volume error ≤10% and hydrostatic centroid error ≤10% against mass divided by physical density and tank area.
- Positive excess mechanical energy ≤10%, unforced shear-amplitude change ≤20%, and timestep-refinement changes in bulk observables ≤10%.

The 10% bulk/energy and 20% shear budgets are prospective application tolerances, not claims of a calibrated liquid. The original 5% density screen was retained. Research-grade acceptance remains separate: consistent pressure/shear response, approximately 1% physical observables and demonstrated spatial, temporal and iteration convergence. Earlier mathematical failures and stricter results remain failures. Quietness after five seconds was not substituted for conservation or velocity accuracy.

The occupied-volume observable unions particle-sized cubes, clips them at the physical container and integrates vertical intervals over horizontal samples. It is a geometric diagnostic, not an exact interface reconstruction. Halving its sampling pitch changed selected final volumes by only 0.05–0.42%, but does not eliminate representation bias. No physical-adoption decision rests on that proxy alone: the hydrostatic and energy/shear failures independently reject the candidates. Particle number and mass remained constant; an apparent occupied-volume contraction is not lost mass.

The reference anchor was 240 Hz, eight Jacobi iterations, correction scale 0.5 and `relaxation_scale=2`. Independent axes were 120/240/480/960 Hz; 2/4/8/16 iterations; correction 0.0625/0.25/0.5/1; and regularisation 0.02/0.2/2/20. Four production-policy one-factor controls completed the 18-policy screen. This is an empirical frontier, not an exhaustive search over every possible parameter combination.

Every run used schema 2 and refinement factor 1. Spacing 0.05 m, support 0.1 m, physical density 1,000 kg/m³, exact resolved mass/rest-density bits, artificial pressure, gravity, kernel pair, signed constraints, planes and particle ordering stayed fixed. The invariant audit checked every unrelated resolved numerical/derived value and all initial particle/plane bytes. XSPH and confinement stayed disabled. The production geometric mass density is approximately 990.32 kg/m³; that convention was held fixed and the hydrostatic reference used actual particle mass. Its approximately 0.98% volume offset cannot explain the much larger observed errors.

## The measured frontier

The following are selected two-second screen results; shear is measured at 0.2 seconds. Cost is for the 8,000-particle resolved scene. Full individual results and all controls are in [the CSV](/docs/project/development/milestones/05/assets/pbf-frontier-v1/policy-frontier.csv).

| Rate, iterations, correction, regularisation | Wall s / simulated s | Worst scene p95 compression | Hydrostatic centroid error | Retained shear mode |
|---|---:|---:|---:|---:|
| Production: 480, 8, 0.0625, 20 | 0.908 | 19.77% | 29.92% | 1.050 |
| 120, 8, 0.5, 2 | 0.224 | 8.29% | 31.05% | 0.912 |
| Anchor: 240, 8, 0.5, 2 | 0.442 | 6.94% | 24.66% | 0.768 |
| 480, 8, 0.5, 2 | 0.886 | 6.92% | 13.73% | 0.520 |
| 960, 8, 0.5, 2 | 1.783 | 6.91% | 7.27% | 0.195 |
| 240, 2, 0.5, 2 | 0.240 | 9.96% | 31.26% | 0.921 |
| 240, 16, 0.5, 2 | 0.719 | 6.41% | 21.25% | 0.647 |
| 240, 8, 0.5, 0.02 | 0.438 | 6.24% | 24.04% | 0.769 |

**No policy passed the combined practical screen.** This remains true if the occupied-volume proxy is omitted. Lower regularisation brought the resolved scene's p95 compression below 5%, but did not qualify hydrostatics, collision and shear together. Increasing iterations improved some density results while worsening shear response. Simply coarsening the production policy, holding its correction and regularisation fixed, produced 57.78% worst compression at 240 Hz and 128.00% at 120 Hz.

Five-second measurements preserved the distinction between transient and settled behaviour. Production hydrostatics retained a 29.90% centroid error with final p95 compression 7.64%. The stronger 480 Hz policy finished that tank with only 1.40% p95 compression, yet still had **13.71% centroid error**. Low final kinetic energy did not establish the correct equilibrium.

The unforced-shear control exposed timestep-dependent projection energy. With correction 0.5 and regularisation 2 fixed, first-step kinetic energy was 0.188534, 0.566103, 2.076347 and 8.116256 J/kg at 120/240/480/960 Hz, against 0.062500 J/kg initially. The excess approximately quadrupled with each halving of timestep. The initial sampled-density relaxation gives a position correction whose velocity contribution scales approximately as correction divided by timestep. It is not removed by more frequent projection. At 0.2 seconds, shear retention deteriorated from 0.912 to 0.195. The mean-velocity norm remained below 1.8×10⁻⁵ m/s for these controls: global momentum conservation can coexist with severe velocity-field error.

This supports, rather than repeats, the [earlier pressure diagnosis](/docs/project/development/milestones/05/pressure-projection-diagnosis.md): density residual convergence is not convergence to the correct tangential fluid response. The sweep does not separately apportion this energy between artificial pressure, signed free-surface deficits and lattice error; those physical quantities were deliberately held fixed. It establishes their combined practical consequence and the timestep/correction confounder. No new implementation defect was identified.

The [derived convergence comparisons](/docs/project/development/milestones/05/assets/pbf-frontier-v1/convergence.json) retain every adjacent timestep and iteration control. For example, changing 240 to 480 Hz changes the tank centroid by 12.67% relative to the finer value, exceeding the 10% practical convergence budget. Successive shear projections differ by 14.44, 24.81 and 32.43 percentage points of initial amplitude. Stable centre of mass and small density residuals therefore do not establish converged velocity dynamics. Existing spatial-consistency failures were reused rather than repeating an already settled refinement study.

![Measured density/cost trade-offs, timestep-dependent energy and shear, and explicit device-ownership cost.](/docs/project/development/milestones/05/assets/pbf-frontier-v1/frontier.png)

## 110,592 particles and the real-time gap

| Numerical policy | First-second cost | Five-second average cost | Worst sampled p95 compression through 5 s | Disposition |
|---|---:|---:|---:|---|
| Production 480 Hz, 8 iterations | 3.142 | 3.886 | 46.34% | Fails physical screens |
| Stronger 480 Hz, 8 iterations, correction 0.5, regularisation 2 | 3.107 | 3.362 | 3.77% | Density passes; cross-scene hydro/shear/volume fail |
| 120 Hz, 8 iterations, correction 0.5, regularisation 2 | 0.781 | 0.905 | 24.47% | Coincidences also develop |
| 240 Hz, 2 iterations, correction 0.5, regularisation 2 | 0.815 | 0.921 | 25.22% | Coincidences also develop |

Costs are wall seconds per simulated second. A value below one is real-time throughput only. It is not target attainment when the declared physical criteria fail. The production large case also recorded 404 CFL-warning steps over five seconds; the stronger case recorded 157. Warnings and slow samples are retained, not suppressed.

The production case's final predicted-neighbour list grew from 3,392,244 entries at one second to 4,089,432 at five seconds. Work evolves as the fluid compresses and settles; a first-second timing is not a sustained-throughput result. These counts support investigating evolving neighbour work, but do not apportion the whole timing increase between individual stages.

The residency results below include 60 Hz observations and use the same production policy and physical trajectory in each pair:

| Interval | Host-snapshot production path, median [range] | Explicit device owner, median [range] | Median cost reduction |
|---|---:|---:|---:|
| First simulated second | 3.130 [3.123, 3.196] | 2.857 [2.852, 2.870] | 8.73% |
| Five simulated seconds | 3.900 [3.879, 3.908] | 3.628 [3.618, 3.633] | 6.98% |

All five sustained pairs improved, by 6.35–7.38%. The five-second device-owned result advances **0.276 simulated seconds per wall second**. At 480 Hz it averages approximately 7.56 ms per step against a 2.083 ms real-time budget. It still needs a **3.63× speedup**, or **72.4% further cost reduction**, for that unchanged workload. This is the measured gap for the current numerical policy, not a prediction for a physically qualified replacement; no such replacement has established a throughput figure.

## GPU-state residency assessment

The [earlier approximately 19.9% native-driver result](/docs/project/development/milestones/05/performance-architecture.md) combined snapshot removal, fewer explicit waits and bounded/preallocated storage. It cannot be assigned to production snapshot removal alone. In the new experiment, retaining every production stage check, cancellation boundary, diagnostic reduction, dynamic cell width and dynamically growing neighbour storage yielded the smaller gains above. With no intermediate observations, the first-second large-scene reduction was 9.69%; at 60 Hz it was 8.73%. At 8,000 particles the 60 Hz comparison included two slower device samples, so a general small-workload benefit is not established.

The existing `snapshot()` and `particles()` return infallible host references. Transparently making them lazy would conceal fallible transfers and complicate rollback. The isolated prototype instead owns canonical accepted device state behind an explicit interface and provides a fallible observation. It reads the eight-byte plane trailer, retains the original ordered host fallback when necessary, and promotes working state only after final cancellation/checks. It preserves the existing `Simulation` API unchanged. All 14 native source files, including the ten retained optimisations, match the control.

Validation covered every cancellation boundary and retries on eight scene/policy inputs (21 polls with eight iterations, nine with two); all 26 polls with enabled velocity effects; empty and single-particle inputs; huge-coordinate width growth; 599 neighbours per row; numerical failure/retry; ordered plane-fallback failure/retry; and exact measured endpoints. These are useful feasibility results, not complete production qualification. Allocation/readback-failure injection, application lifecycle, device-loss recovery and record/viewer checkpoint integration remain necessary. The device path also changes who owns observable state; it must be an explicit contract, not a hidden optimisation of host snapshots.

**Assessment:** retain the isolated prototype and measurements for further implementation work. Do not integrate it yet. The sustained approximately 7% benefit is worthwhile enough to justify the focused interface/failure work, but it does not close the real-time gap or repair PBF physics.

## Established particle alternative and next decision

DFSPH combines density-drift and velocity-divergence solves, warmstarting and timestep selection to reduce expensive work per simulated second. That is a more relevant next comparison than another custom grid solver. The author paper motivates this route, but its performance results are not RTX 4070 measurements or proof of Maelstrom's physical criteria. <sup><a href="#ref-s079">S079</a></sup>

The bounded probe used the author's SPlisHSPlasH implementation at pinned commit `7586ffa25948c6ce3bc6c238cda30ad8d35f60a0`, with exact cubic kernels, geometric mass 0.125 kg, the same spacing/support, no viscosity/filter/surface-tension effects and explicit density/divergence tolerances. This changes a formulation package, not one factor of PBF. Its local four-worker CPU clocks are retained as provisional observations and are not used for a throughput comparison. <sup><a href="#ref-s060">S060</a></sup>

At 120/240/480 Hz, its unforced-shear projection was **0.9999846 / 0.9999847 / 0.9999840**, with approximately 0.0014% kinetic-energy loss and zero positive p95 compression. This is encouraging for that unloaded mode only. It does not test shear under hydrostatic pressure or guarantee a consistent gradient/divergence pair. The first sampled-wall tank began with **54.70% p95 over-density**, then failed containment and energy checks. That boundary setup was rejected before complete-model/performance qualification. It is not evidence that DFSPH itself fails hydrostatics. Initial headless-harness mistakes and include-only upstream build repairs are retained separately.

The concrete implementation sequence is:

1. Keep the production numerical policy and all ten optimisations unchanged. Do not ship a reduced step/iteration policy based on density or speed alone.
2. Develop the measured explicit device-owner interface, preserving the old host-snapshot API. Add allocation/readback/device-loss and application checkpoint tests, then repeat ordinary whole-path timings at actual observation cadences before adoption.
3. Admit an author-reference DFSPH boundary/mass convention independently, then test loaded shear, hydrostatics, collision, free surfaces, energy and timestep/iteration convergence against the same practical budgets. Stop early on fundamental failures; do not tune boundary placement to match a centroid.
4. Only after that admission, build an isolated GPU implementation reusing Maelstrom's neighbour/ownership infrastructure. Measure both pressure/divergence iterations, all neighbour work, boundaries and observations per simulated second. A 120 Hz policy allows 8.33 ms per step; 240 Hz allows 4.17 ms. Those are feasibility budgets, not predicted DFSPH timings. Adaptive timesteps must meet accuracy criteria rather than merely a CFL bound.

**Decision:** no-go for a new production PBF policy or a claim of physically acceptable real-time simulation. Go for focused residency qualification and a bounded established-particle reference comparison. A path towards real time on the RTX 4070 is computationally plausible if an accurate larger-timestep particle method qualifies, but remains unmeasured. There is no evidence yet to promise it. No further custom grid development or local CUDA arithmetic optimisation is justified by this frontier.

## Reproducibility and limitations

The evidence seal contains 7,198 files: exact production JSON, all sampled positions/velocities, independent audits, inputs, commands, failures, source patches, executable identities and every timing sample. It was read back member-by-member on the PC, mirrored locally and verified against the manifest. Both durable roots and reproduction commands are documented in the [evidence README](/docs/project/development/milestones/05/assets/pbf-frontier-v1/README.md). The first local verification ran before transfer completion and rejected a missing archive; that failed attempt is retained separately from the successful completed-copy verification.

Eight deterministic tool/oracle/integrity tests passed locally, and the explicit CUDA edge/cancellation checks passed on the primary PC. No hosted verification, production integration, full DFSPH qualification or DFSPH RTX 4070 benchmark was performed. The bounded screen is not a proof that every PBF variant is unusable; it is evidence that the measured current formulation has no admitted policy in this practical frontier. Earlier physical investigations, failed candidates and acceptance outcomes are preserved.

## References used

<a name="ref-s060"></a> **S060** — Bender and contributors, *SPlisHSPlasH*, pinned author implementation. [Source record](/docs/research/sources/060-splishsplash-pbf-implementation.md).

<a name="ref-s079"></a> **S079** — Bender and Koschier (2017), *Divergence-Free SPH for Incompressible and Viscous Fluids*. [Source record](/docs/research/sources/079-bender-koschier-divergence-free-sph.md).
