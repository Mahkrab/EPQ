# Remaining CUDA position-correction cost, 28 October 2026

Control is exactly the retained 189-file active-distance candidate, including existing
uncommitted density/validation work, based on Maelstrom 1e0085926d05c42949bb76b55d177d42a1f8f94f
and EPQ 1f76097a218266822cdf344c38db75ed128628a8. Preserve prior work. No Git actions.

First collect new ordinary-control 480-step warm-up and Nsight profiles at 8000 and
110592, with precise compute_89 PTX embedded in the executable and source identities.
Use private, separately identified diagnostic exports to attribute correction's
geometry/traversal, Spiky/Poly6 and pressure arithmetic at large size. Diagnostic
probes may run before original correction and reuse finished candidate scratch;
original correction and error boundaries remain. Compare every physical/diagnostic
record exactly; extra launches and changed cache/resources mean probe differences
are attribution evidence, not additive production costs or application speedups.
Inspect generated compiler code/resources; no invented hardware counters.

Choose implementation after attribution. Consider identical geometry reuse, loop
invariants with deferred checks, and owner scheduling if evidence supports them.
No changed FP expression/reduction order, approximation, power semantics, fixed
capacity or neighbour membership. Preserve current active validation publication,
per-expression/per-particle/per-stage errors, barriers, cancellation and rollback.
Retain all trials, failures and slow samples. Up to three focused candidate variants
may use one warm-up and two alternating exploratory pairs per size before a final
source freeze; never pool exploration and primary measurements.

Final qualification: ordinary release, explicit CUDA library/boundary/execution,
Clippy/fmt, native ASan/UBSan, CPU feature isolation and separate device-sanitiser
attempt. New intermediate/error fixtures must also pass the retained equations.

Final primary campaign unchanged workloads: seven 64..8000 regression trajectories;
8000 with checkpoints 0,1,120,240,480;110592 counted 48-cubed block without checkpoints;
110592 XSPH .01/confinement .1 without checkpoints. All start new unpaced simulations,
CUDA0/block128/refinement4/eight iterations/480 steps, no graphics. One warm-up pair
then five alternating pairs per workload, first measured candidate/control, no
replacements. Exact physical/configuration/ordered diagnostic JSON excluding only
measurements/build_revision. Four GiB host/two GiB GPU admission; runs120s,tests600s,
traces180s. Completed-step clocks include preparation/checks/transfers/launch/wait/
cancellation/acceptance; construction/teardown/output/audits/storage separate.
Fresh separate-target locked/offline precise release builds, source/input/binary/PTX
identities before/after. Separate full480step profiles after primary timings at
both sizes/variants, per-iteration/early/late timings, launches/waits/copy schedule.
Device resource probes and independent audits after collection, no other task work
on the PC during timed samples. Retain regressions and source deltas, reconstruct
source and verify all archive hashes/readers. Assess retention under the policy,
not a percentage cutoff. Other GPUs/compilers, device loss and worst-case latency
remain unqualified unless measured. No confidence/significance claim from five pairs.
