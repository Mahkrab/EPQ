# Compact-neighbour comparison protocol

This is the first implementation experiment after the
[diagnosis](/docs/project/development/milestones/05/performance-diagnosis.md). Change CUDA membership storage
only: counted rows, checked offsets and identity-sorted indices replace the bitset matrix.
Keep equations, precision, iteration count, support tests, cancellation/acceptance boundaries,
ordinary diagnostics and explicit stage completions unchanged. Counting, prefix transfers,
allocation, filling and sorting remain inside measured neighbour-search work.

## Source and admission

Use the primary PC through `ssh pc`. Preserve the original release executable from Maelstrom
`c17d8c586eba7455582ad9597cb23d7addc3c6d9` and build the uncommitted candidate separately with
the same locked release/CUDA flags and toolchain. Retain both source manifests, executable
hashes, exact commands, environment and current collector hashes. A source manifest identifies
working bytes, not a completion commit. No ordinary PC installation or repository is replaced.

After the first candidate failed capacity qualification, a large-lattice test exposed an upload
ordering hazard: pageable copies may still be in flight on the legacy stream when a non-blocking
solver stream reads them. The revised experiment uses a private stream with legacy-copy ordering
in both the bitset control and compact candidate. No explicit barrier is removed. This common
correctness repair isolates the storage comparison; original and rejected results remain intact.
The API distinguishes staging from DMA completion and defines the stream dependency.<sup><a href="#ref-s053">S053</a></sup>

Run the feature-enabled Rust suite and explicitly selected hardware cases before timing.
The independent geometry/equation controls must cover empty, singleton, strict boundaries,
dense rows, identity ordering, fixed membership, rebuilding, reused storage, malformed internal
offsets, cancellation/retry and numerical/driver failures. Do not relax existing tolerances;
compare the retained physical documents exactly, including signed zero.

## Matched measurements

Retain the seven original sizes, 480 steps, refinement four, eight iterations and checkpoints
0/1/120/240/480. Use explicit CUDA device zero, 128 lanes and `--unpaced`, without rendering.
First take one candidate warm-up per size and compare with the fresh serial observations
retained by the diagnosis. Take a separate candidate stage profile at each size.

At 8,000 particles, take an ordinary warm-up for each implementation and five total-only
samples each, alternating old/new order between pairs. All samples must complete cleanly
and agree exactly with the same physical control. Retain every attempt, per-step timings,
median, range, construction, teardown, invocation cost and real-time factors. The previous
three-sample baseline remains intact; do not pool those samples with this paired experiment.

## Capacity and profiling

Reuse the exact `capacity-block-v1` fixtures at 8,000, 32,768, 110,592, 262,144 and 512,000.
Run four-step candidate pilots with no checkpoint audits, then admit a 480-step core diagnostic
only when the pilot extrapolates to at most 90 seconds. Pilot timeout/grace is 30/10 seconds;
compare every pilot with a fresh four-step serial-grid control before admitting a longer run.
Long requests retain 120/30. Check at least 4 GiB guest RAM and 2 GiB free GPU memory first.
Original bitset memory estimates must not be reused as candidate allocation measurements.

Before each pilot, use the lattice's geometric bound (at most 124 possible other particles
within two spacing intervals on each axis), with 1.5× index-growth allowance, to estimate initial
storage. This is an admission estimate for these inputs, not a dense-input guarantee or a cap
inside the solver. Skip estimates above the smallest of 6 GiB, 60% device memory and free
device memory minus 2 GiB. Retain
warnings, failures, partial output and deferred runs. These diagnostics do not establish
large-scene physical quality or attainment of the real-time target.

Collect separate Nsight CUDA/memory traces at 8,000 particles for four and 480 steps and at
110,592 for four steps, where the pilot completes. Preserve original profiles privately and
share sanitised exports with analytical rows unchanged. Reconcile counted/fill launches,
transfers, synchronisation and allocated-byte peaks against the changed implementation.
Use matched 480-step traces to compare hot operations and gaps; do not add overlapping host
and GPU times or call profiler timings primary samples. Driver/context memory remains outside
the tracked-allocation peak unless separately measured.

## Decision

Retain this change only with independent correctness evidence and a measured runtime benefit
or a justified measured capacity benefit with its runtime trade-off. Reprofile before choosing
another optimisation. No arithmetic tuning, barrier removal, golden replacement, new dependency,
Git checkpoint or final evaluation is authorised by this experiment.

## References used

<a name="ref-s053"></a> **S053** — NVIDIA, *CUDA Driver API* v13.3, API and stream synchronisation behaviour.
[Source record](/docs/research/sources/053-nvidia-cuda-driver-api.md).
