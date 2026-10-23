# Correction and host costs in evolved motion

The [performance plan](/docs/project/development/performance-plan.md) next needed a full
large-scene profile after the [reservation trial](/docs/project/development/performance-reservation-reuse.md).
The [protocol](/docs/project/development/performance-correction-protocol.md) kept numerical
work unchanged and specified a bounded trial of power-table placement.

**Outcome: the table-placement candidate was rejected.** The original tables are restored.
The retained work is a broader numerical check, reproducible profiling tools and evidence
that ranks correction, evolved neighbour construction and host acceptance more clearly.

## What the profiles established

An initial 110,592-particle, 480-step CUDA trace covered early and post-contact motion.
Correction was the largest individual kernel: 2.553 s in a 12.394 s instrumented window.
Even an ideal removal of that entire kernel would bound this window at about 1.26×;
the power function alone cannot explain the overall performance gap.

Grouping the neighbour-building kernels changes the ranking as the fluid evolves:

| Steps | Correction per step | Neighbour construction per step | Device-idle window per step |
| --- | --- | --- | --- |
| 1–120 | 4.19 ms | 3.94 ms | 8.81 ms |
| 241–480 | 5.74 ms | 7.80 ms | 8.77 ms |

Neighbour construction includes cell keys, cell sorting, counting, filling and row sorting.
Idle intervals are gaps in recorded device activity; they are not automatically removable
CPU work. These kernel-boundary windows are separate from primary solver timings.

Nsight Compute 2026.2.1 was installed outside PATH, but the first counter capture failed
with `ERR_NVGPUCTRPERM`. Further counter attempts stopped without changing security or
clock settings. Per-function power cost, bandwidth, cache behaviour and achieved occupancy
remain unmeasured.

Separate user-space CPU sampling retained 4,115 instruction-pointer samples. Of these,
4,109 had broken backtraces, preventing reliable caller-level attribution. The strongest
resolved leaf was [Plane::contains](https://github.com/Mahkrab/Maelstrom/blob/5120acfbcb07e94ebefd5957ad8f9afa47888be7/src/boundary.rs#L153), with 845 samples. That is a sample count over the
whole invocation, not a percentage of solver wall time. Kernel-mode samples were unavailable.

A separate stage profile recorded 3.106 s in acceptance during a 15.592 s instrumented
run. This stage includes velocity reconstruction, readback, particle reconstruction and
host finite/plane checks. Its roughly 6.5 ms per step remained stable across the windows.
It supports investigating acceptance next, without assigning all of that cost to plane
checks or combining timings from different runs.

## Why try table placement?

The existing power approximation reads two fixed tables whose indices depend on each pair.
NVIDIA describes constant-memory requests splitting when threads request different addresses;
that made placement a reasonable hypothesis, not an established Maelstrom bottleneck.<sup><a href="#ref-s012">S012</a></sup>

The candidate changed only those tables to immutable global storage. Their initialisers
and the entire binary64 power-function body remained identical. Generated PTX changed three
`ld.const` loads to three `ld.global.nc` loads. Both comparison exports shared the new tests,
leaving `native/power.cuh` as their sole source difference. No approximation, reassociation,
solver work, neighbour order, cancellation point or acceptance check changed.

## Matched result and decision

Both variants received a warm-up and five alternating samples at each declared size,
with 480 refined steps, eight iterations and device zero/128 lanes. The larger case
retained its 259 CFL-warning steps and omitted checkpoint audits.

| Particles | Control median | Candidate median | Control range | Candidate range |
| --- | --- | --- | --- | --- |
| 8,000 | 2.076 s | 2.071 s | 2.064–2.105 s | 2.044–2.109 s |
| 110,592 | 12.604 s | 12.545 s | 12.497–15.543 s | 12.481–15.460 s |

Both median changes were below 0.5%, both ranges overlap, and neither met the prospective
1.05× admission criterion. Slow large samples remain on both sides; none was removed or
replaced. The independent reader confirmed rejection. This does not establish that global
table storage is always slower or that constant-memory serialisation dominated these runs.

## Verification and next priority

Both PC CUDA suites passed 258 tests with the same three existing automatic-backend CLI
failures. Strict Clippy, formatting and native ASan/UBSan passed. The new hardware check
matches exact ordered CPU corrections across varied exponents, divergent distances, all
four block sizes, tail sizes, coincident particles and inactive fixed neighbours. It passes
with either table placement and remains in the source. Local checks passed 239 CPU and
37 parent tests, Python compilation and formatting.

The independent audit passed 26 observation-rich comparisons, five fresh serial/CUDA
capacity pilots, five complete capacity comparisons and 12 larger paired observations.
Physical results and warnings matched exactly; deliberately false timing and decision
summaries were rejected. Full before/after timelines and sanitised analytical exports
are retained in the [evidence bundle](/docs/project/development/assets/power-tables-v1/README.md).

The final source matches the independently tested comparison control, including the new
tests. The next implementation priority is host acceptance/validation overhead, followed
by evolved-state neighbour construction. Preserve checks and error ordering when testing
either. Individual power attribution and large-fluid quality remain open, including CFL
warnings. No hosted, other-platform, actual device-loss or passing device-memory-sanitiser
qualification follows. Both repositories remain uncommitted on their existing branches.

## References used

<a name="ref-s012"></a> **S012** — NVIDIA (2026), *CUDA C++ Programming Guide*, Release 13.2, §8.3.2, Constant Memory.
[Source record](/docs/research/sources/012-nvidia-cuda-programming-guide-release-13-2.md).
