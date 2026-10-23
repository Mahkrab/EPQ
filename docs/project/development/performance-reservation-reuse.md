# Avoiding driver calls for reused CUDA reservations

The [performance plan](/docs/project/development/performance-plan.md) leaves host
coordination open after the [gradient-prefix trial](/docs/project/development/performance-gradient-reuse.md).
This investigation removes a small piece of unnecessary repeated work without changing
the numerical passes. Its [protocol](/docs/project/development/performance-reservation-protocol.md)
sets out the comparison and admission criteria before measurement.

**Outcome: the candidate was rejected after PC qualification.** It removed redundant
driver waits but produced no clear whole-solver gain. The original implementation is
restored; the candidate, its tests and the measurements remain in the evidence bundle.

## What changed and why

The solver retains device buffers, but each fitting reservation still entered the native
driver wrapper: push the context, wait on the stream, then pop the context. Preparation,
uploads and neighbour construction make 19 reservation requests per step in the nonempty
comparison scenes. Most reuse existing capacity. This count comes from the call paths;
it is not a measurement of time saved.

The candidate returned immediately when a valid reservation fitted. Poison checks and
argument validation still ran first. Actual growth and every transfer retained the
existing wrapper, including empty transfers. Allocation sizes, copies, kernels,
arithmetic, iteration order and cancellation points were unchanged.

This deliberately changed fault observation: a fitting reservation checked retained host
metadata rather than probing device health. Earlier driver calls already completed their
streams. A newly observable fault would be detected by the next real driver operation;
already poisoned resources still failed immediately. That policy was tested with injected
faults, not actual device loss. It is part of the rejected candidate, not the restored API.

## Fresh matched PC results

Each variant received a warm-up and five alternating samples at both declared sizes.
Both used 480 refined steps, eight iterations, device zero/128 lanes and no rendering.
The smaller case retained its checkpoints; the larger had no checkpoint audits and
retained the control's 259 CFL-warning steps.

| Particles | Control median | Candidate median | Control range | Candidate range |
| --- | --- | --- | --- | --- |
| 8,000 | 1.857 s | 1.856 s | 1.831–1.914 s | 1.818–1.861 s |
| 110,592 | 12.238 s | 12.320 s | 12.207–12.366 s | 12.300–12.553 s |

The smaller median changed by about 0.08%; the larger was about 0.7% slower. Both
ranges overlap. Neither case met the prospective 1.05× gain criterion. The independent
reader confirmed rejection without trusting the collector's decision. No sample was removed.

Separate traces verified 24,481 → 15,376 explicit completions at 8,000/480, and
205 → 143 at 110,592/four. Kernels, transfer counts/bytes, reset behaviour and tracked
allocation peaks were unchanged. Generated PTX was byte-for-byte identical; entry-kernel
register use stayed at 44 per thread. These profiles are not primary timings.

The 9,105 removed fitting-reservation waits at 8,000 accounted for only about 3.25 ms
of instrumented wait-API time. Default tracing omitted context push/pop, so that is not
the complete reservation cost or an uninstrumented speedup bound. It helps explain why
a large reduction in call count did not establish a useful runtime gain.

## Verification and remaining limits

The candidate passed native ASan/UBSan checks covering all 14 slots, fitting requests,
unchanged pointers/contents, invalid input, allocation exhaustion and retry, growth,
empty transfers and poisoning. The new no-driver-call assertion failed against the
original bridge, as intended. Those feature-specific cases remain with the rejected patch.

The full PC CUDA release suite passed 257 tests with the same three automatic-backend
CLI failures reproduced in the control. Strict Clippy and formatting passed. After
restoration, the original source again passed 257 tests with those three failures, native
sanitised checks, strict Clippy and formatting. Local preparation passed 239 CPU tests,
30 parent tests, Python compilation and formatting.

The independent audit passed 26 observation-rich comparisons, five fresh serial/CUDA
capacity pilots, five complete capacity comparisons and 12 larger paired observations.
Physical results and warnings matched exactly; false timing and retention summaries were
rejected. All four earlier trace summaries also reproduced exactly. Sanitised analytical
tables were checked unchanged; original profiler reports remain private.

The [evidence bundle](/docs/project/development/assets/reserve-reuse-v1/README.md) records
the exact dirty source identities, reconstructable candidate patch, raw samples and final
source verification. PC access initially failed; after it resumed, saved PC controls were
restored byte-for-byte into an isolated workspace. No laptop timings replaced PC measurements.

This closes one bounded experiment, not the optimisation plan. Larger-scene CFL warnings
and independent quality qualification remain unresolved. No hosted, other-platform,
actual device-loss or passing device-memory-sanitiser result follows.

Both repositories remain on their existing optimisation branches with uncommitted work.
The previous trial, custom user scene, commits, tags and parent gitlink are preserved.
