# Architectural PBF investigation protocol

Declared before new measurements on 28 October 2026. Production Maelstrom remains
unchanged; this study does not select an eleventh local kernel optimisation.

## Controls and timing

Freeze the live Maelstrom source manifest and both repository states. Verify that
the control preserves all ten optimisations. Important measurements run through
`ssh pc` on CUDA device zero (RTX 4070), without concurrent builds or GPU tests.
Retain commands, exits, monotonic durations, raw failures, source/binary/input
hashes and environment. Do not change drivers, registry, security or system settings.

New simulations use the established 8,000 and 110,592 particle blocks, strict
support radius 0.1 m, spacing 0.05 m, eight immutable Jacobi iterations,
refinement four, 480 unpaced steps, with graphics disabled. Record resolved dt,
correction scale, mass, density and regularisation; refinement can change more
than dt. Effects-disabled cases are the attribution control; explicitly labelled
effects-enabled checks use XSPH 0.01 and confinement 0.1.

Production complete-step totals retain the existing measurement boundary. A
separate native driver replays the same device algorithms and inputs, with
control/candidate boundaries explicitly named. Its totals must never replace
production solver timings. Confirm the checked driver's trajectory against
production at 1/120/240/480 steps before interpreting it. Separately measure
ordinary production and native control (warm-up plus five samples).

Use one warm-up and five alternating pairs for each admitted architectural
comparison, reversing order between pairs. Retain every sample. Report median,
range, individual pairs and final-state agreement. Keep timelines and quality
observation runs separate from uninstrumented timing. Nsight Systems is the
existing available timeline tool; retain denied-counter evidence if relevant
without changing permissions.

## Isolated experiments

1. Checked native control: the same device arithmetic, ordered rows and stage
   launches, explicit group completions, compact summaries and CPU snapshots.
   Fixed conservative private neighbour allocation is disclosed as a harness
   difference and bounded/audited; it is not a production capacity improvement.
2. Deferred diagnostics: retain computations and copies, observe numerical
   diagnostics at step completion. This relaxes immediate failure/cancellation
   semantics. It does not remove Jacobi dependencies.
3. Device-owned snapshots: omit per-step CPU vectors and materialisation, keeping
   group completions. Retain final observations outside timing. This changes the
   observation/acceptance API.
4. Resident control: combine deferred observations with device-owned vectors,
   fixed validated cell width and conservative row allocation. Observe completion
   once per step; never report asynchronous enqueue time as completed work.
5. Arithmetic: compare retained exact guarded quartic, forced binary64 reference
   power, experimental binary32 quartic, and FMA contraction separately. Quantify
   the remaining binary64 cell arithmetic separately. The binary32 and FMA paths
   may lose bitwise equivalence and must pass independent health assessment.
6. Layout: component SoA for current/accepted positions only, with unchanged sums,
   rows and equations. Include packing/readback in the checked boundary and test
   exactness. A combined relaxed path is a separate interaction experiment.
7. Independent PBF: inspect and pin a CUDA implementation; where feasible run a
   headless adapter on this PC with matched initial particles, support, dt and
   iteration count. Document every adapter change, missing self terms, constraint,
   pressure, neighbourhood, boundaries, row caps and timing differences. A fast
   but unhealthy or truncated run is not an equivalent solver result.

## Independent numerical assessment

Use an independently implemented binary64 current-position neighbour/density
reader, including self-density, strict support and the resolved mass/rest density.
It must not use solver density outputs or frozen membership to establish quality.
Retain current neighbour distributions at initial/early/evolved checkpoints,
prediction-time row distributions, density ratios and positive/absolute density
error, nearest separation/coincidence, finite state, boundary violation, maximum
speed, centre of mass and kinetic/gravitational energy. Compare per-identity
position/velocity RMS/max errors and exact component counts with the control.
Absolute density error includes free-surface deficiency and is not alone an
incompressibility test.

For relaxed arithmetic, report errors at all retained checkpoints and over an
extended trajectory, including whether differences grow. A predeclared screening
bound is no nonfinite state or coincident particles, boundary violation <= 1e-6 m,
and p95 positive density error <= 5%. This is a health screen, not a proof of
physical accuracy. Independent ballistic and density-oracle fixtures must pass.
Compare iteration/timestep costs only alongside error curves; include a more
resolved control. Do not claim a lower-work configuration equivalent merely
because it is stable or passes the screen. Source equality is regression evidence,
not independent fluid qualification.

Rollback is removal of the task-owned exports/processes; no experimental file is
copied into Maelstrom. A timeout uses the existing collector's SIGINT/grace/SIGKILL
policy and retains the incomplete attempt. Git history, branches, tags, installed
commands and the parent gitlink remain untouched. Conclusions separate measured
causes, bounded ceilings, experiments with changed semantics and unresolved causes.
