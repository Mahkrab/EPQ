# Ordered gradient reuse reassessment protocol

This resumes the [performance plan](/docs/project/development/milestones/05/performance-plan.md)
after scene usability. The starting commits are EPQ `3d043355c9744dee9355b5e045217e3c46a9124d`
and Maelstrom `87145510a9e5d812066138c35f1fac82e4f593b0`, on
`phase/05-03-optimisation`. Branch creation does not establish a completion checkpoint.

## Change and correctness

Reassess the [earlier prefix trial](/docs/project/development/milestones/05/performance-gradient-reuse.md)
against the current solver. Reuse lower-identity squared gradients during owner accumulation,
preserve their original addition order, finish owner checks, insert self, then traverse the suffix.
Deferred prefix failures must not mask owner failures. No full pair cache, changed equations,
approximations, neighbour ordering, allocation, launch or cancellation boundary is intended.

Freeze separate control and candidate source exports and hashes before collection. They are
temporary build inputs, not Git checkpoints. Use separate Cargo target directories and identical
locked, offline release CUDA builds with precise arithmetic and compute target 89. Independently
compile each source's PTX and verify its complete bytes occur in that executable; the two kernels
must differ. Keep ordinary PC repositories, installed binaries,
user scenes and display settings unchanged. Run both variants sequentially on the primary PC.

Run the complete release CUDA test suite and explicitly select the hardware library and
application-boundary checks. Existing ordered-prefix tests cover owner-error precedence, overflow,
self position, inactive neighbours, changed snapshots and 32/64/128/256-thread blocks. Include empty
input. Run formatting, strict CUDA Clippy and native address/undefined-behaviour sanitiser checks.
Compare the seven bundled 64–8,000-particle, 480-step trajectories exactly between variants.

## Workloads fixed before timing

Use the existing falling-block geometry, reference configuration, timestep refinement 4,
eight Jacobi iterations, CUDA device zero and block size 128. Disable pacing and rendering.

| Workload | Particles | Steps | Observations | Fluid effects |
| --- | ---: | ---: | --- | --- |
| Bundled falling-block-20 | 8,000 | 480 | 0, 1, 120, 240, 480 | Disabled |
| Existing capacity-block-48 family | 110,592 | 480 | No checkpoints | Disabled |
| Same capacity-block-48 inputs | 110,592 | 480 | No checkpoints | XSPH 0.01 and confinement 0.1 enabled |

The enabled workload is a separate comparison identity. Its results cannot replace historical
disabled-effect timings. Preserve any CFL warnings and require exact matching physical results,
diagnostics and warning schedules within each workload; agreement alone does not qualify fluid quality.

Each workload receives one untimed warm-up per variant and five alternating measured pairs.
Start odd pairs with control and even pairs with candidate. Keep every requested sample, failure
and slow run. Do not change the sampling plan after viewing timings. Bound each simulation to
120 seconds plus 30 seconds cancellation grace; a timeout stops collection for assessment.
Require at least 4 GiB available guest memory and 2 GiB free GPU memory before the campaign.

Retain source, binary, input, protocol and collector hashes; toolchain, GPU, driver and CPU
identity; commands, exits, raw output and monotonic wall durations. Capture GPU/Linux telemetry
outside each invocation. These readings cannot establish all Windows background activity.
Keep solver-step totals, construction, teardown and full invocation durations separate.

After ordinary samples, collect separate full-motion Nsight Systems traces for the disabled
110,592-particle control and candidate. Check launch/transfer/completion counts and early/evolved
multiplier costs. Unavailable profiling is a recorded limitation, not a reason to invent attribution.

## Assessment

An independent reader must reconstruct totals, medians, pair ratios and exact physical agreement
from raw results; deliberately altered timing and physical summaries must fail verification.
Keep profiler environments and personal paths out of published evidence. Retain hashes for private
originals and sanitise analytical exports without changing their measured rows.

Follow the [assessment policy](/docs/project/development/milestones/05/performance-assessment.md).
Weigh whole-solver and invocation savings, individual pairs, workload variation, component evidence
and the small implementation's maintenance cost. Conclude retain, do not retain, or needs more
evidence. Range overlap and any fixed percentage are not independent rejection rules. The original
trial remains a historical rejection; this is a new assessment, not a retrospective relabelling.

No commits, pushes, tags, merges or gitlink changes are authorised by this protocol.

## Collection correction

The first collection was disqualified after profiling: sharing a Cargo target directory reused
the control's PTX in the candidate executable despite a changed Rust build identifier. A fresh
candidate compile matched neither measured executable. Preserve that campaign as an invalid build
comparison; its near-equal timings cannot assess gradient reuse. The corrected collection uses
the separate targets and embedded-code guard above, with a regression test for stale native code.
It compares canonical physical records exactly, including signed zero, excluding only timings and
the build identifier. This avoids constructing unnecessary tolerance reports between identical
CUDA schemas. All workloads, samples, ordering and the retention policy remain unchanged.
