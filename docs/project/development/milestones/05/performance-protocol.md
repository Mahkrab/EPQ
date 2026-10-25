# Performance diagnosis protocol

This specifies the first investigation in the [performance plan](/docs/project/development/milestones/05/performance-plan.md).
It is declared before collection, not reconstructed from favourable timings. Use committed Maelstrom
`c17d8c586eba7455582ad9597cb23d7addc3c6d9` unchanged, a release CUDA-enabled binary shared by
the CPU and GPU controls, default build flags, device zero/128 lanes and twelve CPU workers.
The primary device is the PC reached through `ssh pc`. Record actual source, executable, tool,
protocol and input hashes, compiler/toolkit/driver, CPU/GPU, guest memory and environment.
An isolated temporary source export is a build convenience, not a new historical checkpoint.

## Original-workload baseline

Keep the seven existing sizes, 480 steps, factor-four refinement, eight iterations and checkpoints
0, 1, 120, 240 and 480. Use explicit serial grid, twelve-worker grid and CUDA in that fixed order,
with no rendering, pacing or resource auto-selection. Each size has one ordinary warm-up, three
fresh-process total-only samples and one separate stage profile. Keep the original 120-second
invocation timeout and 30-second interrupt grace. Failed/warning-bearing warm-ups prevent primary
sampling; retain one diagnostic profile and all failed attempts. Do not introduce a fresh
brute-force speedup claim: the reference oracle and existing goldens establish correctness.

Require exact binary32 agreement, including signed zero, against fresh serial-grid observations
and the frozen small goldens. Verify actual backend, resource, request, release and source metadata.
Never admit incomplete, warning-bearing, wrong-resource or mismatching results as primary timings.
Keep raw per-step times and observations. Reports separate solver construction, first-step storage,
steady stepping, shutdown and whole-invocation elapsed time. Solver timers retain all host checks,
transfers, launches, completion and atomic acceptance. Audits and encoding remain outside those timers.

## Capacity and observation cost

The separate `capacity-block-v1` family has sides 20, 32, 48, 64 and 80: 8,000, 32,768, 110,592,
262,144 and 512,000 particles. Copy `defaults-v4.toml` unchanged and refine by four at invocation.
Generate a counted-half-open X/Y/Z lattice, identities from zero, spacing 0.05 m, origin
[0.2, 0.4, 0.2] m, zero velocity and no randomness. Let L = side × 0.05 m. Box lower faces are
zero; upper faces are [L + 0.4, L + 0.6, L + 0.4] m. Keep +X, −X, +Y, −Y, +Z, −Z plane order.
Bounds are written as exact decimal literals. The side-20 geometry equals the original 8,000-particle
input; its separate name does not turn the editable playground into an evidence fixture.

Run a four-step CUDA pilot before a 480-step capacity request. The pilot timeout is 30 seconds with
10 seconds' grace. Longer requests retain 120/30 seconds. Do not start a long run when pilot solver
time extrapolates beyond 90 seconds; this is an admission estimate, not a measured 480-step result.
Use no checkpoint audits for the core-throughput request, retaining ordinary diagnostics, complete
initial/final state and solver measurements. First compare this policy against the original
observation-rich 8,000-particle request for exact final-state/diagnostic agreement. Report their
different observation policies and invocation costs explicitly. Larger core cases are capacity
diagnostics, not independent density qualification or proof of real-time quality.

Before each pilot, bound the source-derived device allocation by the smallest of 6 GiB, 60% of
device memory and currently free device memory minus 2 GiB. The allocation model is
`4 × N × ceil(N/32) + 88 × N + 32 × next_power_of_two(N) + 16 × planes` bytes.
It covers the thirteen solver slots, not driver/JIT/context allocations or a measured peak.
Require at least 4 GiB guest memory available before launch. Skip unsafe sizes with the estimate,
current capacity and reason retained. Never claim an estimated skip as observed exhaustion.
Sample device-wide memory in separate diagnostic invocations where supported, recording unrelated
use and sampling limitations; do not add monitoring overhead to primary samples.

## Attribution and profiler admission

Collect bounded whole-run CPU/CUDA timelines through Nsight Systems, including four-step pilots
and a core 480-step 8,000-particle run where supported. The latter includes early and post-impact
motion. Preserve raw reports, tool version, command, exit, stderr and available summary exports.
Use the original stage-profile per-step records to compare steps 1–120 with 241–480; do not infer
that a cold four-step profile describes settled motion. Check the PC's actual profiler capabilities
before choosing further options. Record unsupported counters/features as unavailable, never passed.
Do not install global tools, alter permissions/security, or change drivers to obtain a profile.

Keep profiler runs separate from primary timings. Distinguish CUDA API host time, device kernel/copy
time, idle gaps and overlapping intervals; their sums are not additional elapsed time. Attribute
transfer count/bytes, synchronization count, bitonic sort passes and expensive solver operations.
Use Nsight Compute or generated PTX only for a kernel hypothesis requiring more detail. No arithmetic
substitution, removed validation, changed iteration count or less frequent state acceptance belongs
in this diagnosis. A deliberately changed diagnostic configuration must have its own identity.

Where host sampling or GPU metrics are unavailable, use source-validated operation/byte models and
available API/kernel timelines, labelling each observation, derivation and unresolved attribution.
In particular, binary64 power arithmetic is a candidate cost, not a conclusion from GPU model alone.

## Comparator and quality admission

Use the pinned [SPlisHSPlasH PBF source](/docs/research/sources/060-splishsplash-pbf-implementation.md)
as the primary runnable comparator. Specify single precision, fixed timestep equal to Maelstrom's
resolved refined value, eight PBF iterations (minimum equals maximum), first-order velocity update,
gravity [0, −9.81, 0], particle radius 0.025 m and no optional viscosity/vorticity/surface-tension
effects. Start with an explicitly counted Cartesian block or imported positions, not a block generator
assumed to share endpoint rules. Record actual support, neighbour counts, kernel, boundary density,
clamping/relaxation, build options and thread count. Its solver is not bitwise equivalent to ours.
Select PBF by its resolved method identity; do not benchmark the upstream DFSPH example accidentally.<sup><a href="#ref-s060">S060</a></sup>

Separate a fixed-work diagnostic (same timestep/iterations) from any later fixed-quality study.
The fixed-work comparison still requires a mismatch table and cannot supply a universal speedup.
For unchanged-contract Maelstrom, require exact controls, finite state, zero CFL warnings, full
completion, plane compliance and unchanged density audits. For later cross-solver quality tuning,
predeclare a one-second and ten-second test: full completion, no non-finite state or escape, zero
time-dependent numerical failure, maximum positive density excess ≤5% and volume-weighted mean
positive excess ≤1% at declared checkpoints after contact. Measure free-surface under-density
separately rather than treating every boundary deficit as compression. These provisional engineering
quality targets are not a validated physical model; assess reference attainability before tuning,
retain any miss and obtain an explicit decision if the study must revise them.

Run the same-PC external comparator if its pinned build can be obtained within the available
environment without global changes. Otherwise retain the precise unsupported/build requirement and
the reproducible specification; contextual paper timings do not become fresh measurements.
The original paper's GTX 680 scenes, GPUSPH's WCSPH method and CompactNSearch's search-only scope
remain distinct, as recorded in the plan. This protocol does not authorise numerical optimisation.

## References used

<a name="ref-s060"></a> **S060** — Bender and contributors, *SPlisHSPlasH*, pinned PBF implementation and method registration.
[Source record](/docs/research/sources/060-splishsplash-pbf-implementation.md).
