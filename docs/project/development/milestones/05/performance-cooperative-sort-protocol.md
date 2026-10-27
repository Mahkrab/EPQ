# Cooperative neighbour sorting protocol

Test cooperative integer row sorting against the retained
[gradient-prefix implementation](/docs/project/development/milestones/05/performance-gradient-reassessment.md).
Both repositories remain on `phase/05-03-optimisation`. The control is the uncommitted
179-file tree `a10a3f67d77ebf7d0ac0e8163e2fecd72981cc3f9d6b8851b48491762715d0e1`,
based on Maelstrom `87145510a9e5d812066138c35f1fac82e4f593b0`. Preserve that change and its evidence.

## Candidate and invariants

Keep count and fill geometry unchanged. Replace each fill thread's heapsort with a subsequent
warp-per-row sort. Try a register sorting network for up to 256 integer identities; retain the
existing heapsort for larger rows. The bound selects an implementation, not a neighbour cap.
Pad the network with an unused maximum identity and never write padding into the accepted row.

Every participating row gets a complete warp, including the last launch block. All named lanes
must execute each shuffle consistently; shuffles do not replace memory ordering. The preceding
fill kernel and following numerical kernels retain their stream dependency.<sup><a href="#ref-s012">S012</a></sup>
Skip sorting after failed fill, validate row bounds before access, and preserve deterministic
failure precedence, context invalidation, cancellation, retry and accepted-state semantics.
No floating-point calculation, reduction order, membership, allocation or numerical setting changes.

One additional kernel per nonempty step is allowed, with no additional host completion or readback.
Measure its cost together with fill. Source-level sorting work or a faster isolated kernel cannot
alone justify retention. Keep any register/code-size effects on other passes visible.

## Qualification and fixed comparison

Freeze control and candidate source exports and hashes. Use separate Cargo target directories,
locked offline release CUDA builds, compute target 89 and the existing precise arithmetic flags.
Independently compile each source's CUDA code and verify its bytes inside the corresponding binary;
require distinct control and candidate code. Leave ordinary PC repositories and installed binaries alone.

Run both release suites, explicit CUDA library/application checks, strict Clippy, formatting and
native address/undefined-behaviour sanitiser tests. Add hardware coverage for empty/single rows,
31/32/33, 63/64/65, 127/128/129 and 255/256/257 entries, dense fallback rows, mixed lengths,
permuted discovery order, final partial blocks and 32/64/128/256-thread launches. Derive sorted
identities independently. Inject failures at either launch and retain earlier fill errors.

Use the primary PC and the preceding three workloads without pooling historical samples:

| Workload | Particles | Steps | Checkpoints | Fluid effects |
| --- | ---: | ---: | --- | --- |
| Bundled falling-block-20 | 8,000 | 480 | 0/1/120/240/480 | Disabled |
| Capacity-block-48 | 110,592 | 480 | None | Disabled |
| Same capacity geometry | 110,592 | 480 | None | XSPH 0.01 and confinement 0.1 m/s enabled |

Use refinement 4, eight Jacobi iterations, CUDA device zero, block size 128 and no pacing/rendering.
Each case gets one warm-up per variant and five alternating measured pairs, control first on odd
pairs and candidate first on even pairs. Keep every sample. Require exact physical records and
warning schedules, including the larger workloads' existing warnings. Also compare the seven bundled
64–8,000-particle trajectories. Solver, construction/teardown and whole-command timings stay separate.

Retain commands, exits, raw outputs, source/binary/input/protocol/collector hashes, environment and
GPU/Linux readings outside timed invocations. Require 4 GiB available guest RAM and 2 GiB free GPU
memory before collection. Bound simulations to 120 seconds plus 30 seconds cancellation grace.
Stop and retain a failed or incomplete request rather than retrying it away.

After ordinary samples, capture separate full-motion disabled-effect profiles. The candidate should
add 480 sort kernels to the control's 99,360, retaining 24,481 stream completions and identical
transfer counts/bytes. Independently check raw kernel correlations, launch dimensions, integer-sort
and fill costs, early/evolved windows and unrelated numerical passes. Unavailable profiling is a limitation.

## Decision and evidence

Use the [assessment policy](/docs/project/development/milestones/05/performance-assessment.md).
Weigh exactness, whole-solver and invocation effects, paired consistency, small-scene costs, memory
and implementation complexity. Conclude retain, do not retain, or needs more evidence in prose;
no fixed percentage or range-overlap rule decides the outcome. Do not infer final fluid quality
from warning-bearing timing comparisons. Preserve source patches, failures and private-report hashes;
sanitise shared profiler metadata without changing analytical rows. Independently reject altered
timing, physical and profile summaries. No Git checkpoints or publication are authorised here.

## References used

<a name="ref-s012"></a> **S012** — NVIDIA, *CUDA C++ Programming Guide*, Release 13.2, §10.22.2.
[Source record](/docs/research/sources/012-nvidia-cuda-programming-guide-release-13-2.md).
