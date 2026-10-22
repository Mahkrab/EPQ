# Pre-evaluation review: usability and performance

## Why the project needs another pass

Review on 21 October 2026 found a gap between completing the planned features and making Maelstrom
straightforward to use and sufficiently efficient for the final evaluation. The user's assessment
was that its documentation was overcomplicated and difficult to follow, and that its demonstrated
particle counts were disappointing beside older PBF implementations. These concerns change the
order of work; they do not erase the earlier implementation or its measured improvements.

This review inspected EPQ `068c0f5597636f8533a7de1e8ce1574d78080eb2` and Maelstrom
[`a881145a373fe2a4c9a25b0ca10f3b89c2b1db9e`](https://github.com/Mahkrab/Maelstrom/tree/a881145a373fe2a4c9a25b0ca10f3b89c2b1db9e).
Both worktrees were clean. The findings below separate observed interface problems, source-level
scaling costs and unmeasured explanations. This was a source and documentation review, not a fresh
benchmark, user study or independent rerun of the historical qualification.

## Documentation and command-line experience

The [README](https://github.com/Mahkrab/Maelstrom/blob/a881145a373fe2a4c9a25b0ca10f3b89c2b1db9e/README.md)
still introduces a headless reference solver and spends substantial space on backend and measurement
contracts. Viewing, export and playback appear later. The information is useful, but it does not
lead a new user from installation to a visible result. The
[viewer guide](https://github.com/Mahkrab/Maelstrom/blob/a881145a373fe2a4c9a25b0ca10f3b89c2b1db9e/docs/viewer.md)
leads with Cargo development commands, whereas the export guide uses an installed executable.
Its launch examples also omit `--release`, so following them uses the development profile rather
than the optimised build used for performance evidence.
Feature selection, rebuilds and runtime requirements need one clear explanation rather than prior
knowledge. This does not mean every existing statement is wrong; a complete rewrite must retain
accurate technical reference material while changing how readers reach it.

The [CLI declarations](https://github.com/Mahkrab/Maelstrom/blob/a881145a373fe2a4c9a25b0ca10f3b89c2b1db9e/src/cli/arguments.rs)
confirm an inconsistent execution interface. `run` defaults to serial brute force and uses
`--backend`, `--execution` and `--threads`. Viewing and direct export default to serial grid and use
`--mode` and `--workers`; the viewer defaults to four workers, while threaded `run` normally selects
available parallelism. A user has to relearn the same choice for different journeys.

Fresh simulation, numerical replay, rendering saved observations and playing saved images are
different operations. Their names, help and examples must make that distinction immediately clear.
An ordinary run should not accidentally select the slow comparison method, but neither CUDA nor
threading is fastest for every request. The
[PC campaign](/docs/project/development/milestones/03/cuda-gpu.md#measured-benefit-and-remaining-uncertainty)
found CUDA slower than serial grid at 64 and 216 particles. A universal fastest-backend claim or an
automatic threshold copied from one old scene family would therefore be unjustified.

## Performance and capacity concerns

The retained same-binary PC campaign measured 8,000 particles over 480 refined steps with eight
iterations: CUDA took a median 7.611185 seconds, compared with 63.791997 seconds for serial grid and
21.519382 seconds for the twelve-worker control. These establish backend gains, not competitive
absolute performance. Approximately one simulated second took 7.61 seconds of solver work; solver
step rate is not display FPS. The campaign and its qualification limits remain owned by the
[CUDA evaluation](/docs/project/development/milestones/03/cuda-gpu.md).

Source inspection identifies concrete scaling concerns:

- [CUDA storage](https://github.com/Mahkrab/Maelstrom/blob/a881145a373fe2a4c9a25b0ca10f3b89c2b1db9e/src/cuda/solver.rs)
  reserves `4 * N * ceil(N / 32)` bytes for membership, even for sparse local neighbourhoods.
  This calculates to 8 MB at 8,000 particles and 1.25 GB at 100,000, before other storage.
- The [membership iterator](https://github.com/Mahkrab/Maelstrom/blob/a881145a373fe2a4c9a25b0ca10f3b89c2b1db9e/native/solver.cu)
  scans each row's words, including empty words, during repeated numerical passes. Grid discovery
  therefore does not eliminate quadratic membership traversal as particle count grows.
- The [native boundary](https://github.com/Mahkrab/Maelstrom/blob/a881145a373fe2a4c9a25b0ca10f3b89c2b1db9e/native/bridge.cpp)
  synchronises after each solver call. The host solver also downloads per-particle error arrays,
  uploads accepted state each attempt and runs a many-pass bitonic cell sort.

These are implementation facts, not measured allocations of elapsed time to individual causes.
Compact neighbour storage, fewer synchronisation points and less repeated transfer are candidates
for a separate PC profiling investigation, not promised speedups. The largest measured workload is
not a demonstrated capacity limit. Larger-input tests must measure memory, time and correctness.
Published solvers also differ in scene, neighbourhood, timestep, iterations and quality requirements;
their particle counts alone cannot establish a fair slowdown ratio.

## Decision and remaining work

Address documentation, execution defaults and CLI consistency first, following the
[usability plan](/docs/project/development/usability-plan.md). Then decide and carry out a bounded
performance investigation before admitting final evaluation measurements. Completion of the
usability work does not close the performance concerns.

The subsequent [usability revision](/docs/project/development/usability-revision.md) records the
implementation and local checks separately, preserving this review as the before-change assessment.

Retain historical code, inputs, campaigns and checkpoint tags. Changes to numerical or measurement
contracts remain possible with an explicit rationale and renewed qualification of affected
comparisons. A nicer interface or fewer solver iterations must not be counted as a backend speedup.
Cross-campaign comparability, one-device coverage and limited repetitions also remain evaluation
limitations. No new performance target, result or physical-validation claim is established here.
