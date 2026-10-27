# Retaining accepted CUDA buffers

This is the first bounded residency comparison after the
[compilation and block-size measurements](/docs/project/development/milestones/05/performance-compilation-profile.md).
**Retain the change.** It removes repeated preparation work and gives a modest, consistent
solver improvement without changing the mathematical work or public snapshot behaviour.
It does not complete the broader device-owned execution design.

## Ownership and implementation

Previously, every timestep reserved fixed storage and uploaded accepted positions, velocities
and static planes again. The candidate does this on its first attempt, inside the existing
step timer. Later attempts reuse accepted device vectors and fixed storage. Neighbour storage
still grows when needed, and its offsets are still calculated and uploaded by the host.

Working vectors remain separate from accepted inputs. After downloading final output, Simulation
performs the same particle, plane and final cancellation checks. Only then does a native operation
exchange the accepted/working position and velocity allocations and their capacities, followed
immediately by installation of the host snapshot. The exchange makes no driver calls. It rejects
poisoned or unopened attempts, device-diagnosed failures and repeated acceptance before changing pointers.

Cancellation, numerical failure and predicate panic leave the previous accepted device vectors
available for retry. All existing stage polls, error priorities and synchronisation boundaries
remain. Host snapshots stay current after every accepted step; this does not remove final downloads,
introduce lazy observations or batch work across cancellation boundaries. No dependencies, kernels,
arithmetic, iteration counts or block defaults changed.

The [evidence and source reconstruction](/docs/project/development/milestones/05/assets/resident-state-v1/README.md)
identify both exports from Maelstrom base
[`87145510a9e5d812066138c35f1fac82e4f593b0`](https://github.com/Mahkrab/Maelstrom/tree/87145510a9e5d812066138c35f1fac82e4f593b0).
The control contains the retained prefix, cooperative sorting and export instrumentation.
Reconstruction checks all 182 candidate files. Both binaries contained identical freshly compiled PTX.
These are measured working states, not new Git checkpoints.

## Primary-PC result

The [prospective protocol](/docs/project/development/milestones/05/performance-resident-state-protocol.md)
fixes CUDA device zero, block 128, 480 unpaced steps, refinement 4 and eight iterations. The
PC used a Ryzen 9 7900X and RTX 4070 under WSL2, driver 610.88, CUDA 13.3.73 and Rust 1.96.0.
Each setting received a warm-up and five measured pairs in alternating order. The small case
kept checkpoints 0/1/120/240/480; the large cases kept none. Enabled effects were XSPH 0.01 and
confinement 0.1 m/s. These results are not pooled with earlier campaigns.

| Workload | Control median | Candidate median | Time saved |
| --- | ---: | ---: | ---: |
| 8,000 particles | 1.690 s | 1.650 s | 2.38% |
| 110,592, effects disabled | 9.082 s | 8.880 s | 2.23% |
| 110,592, effects enabled | 9.376 s | 9.233 s | 1.52% |

All 15 candidate runs were faster than their paired controls. Control/candidate ranges were
1.674–1.805 / 1.645–1.665 s, 9.044–9.099 / 8.860–8.919 s, and 9.354–9.432 / 9.171–9.252 s.
One small control was slower than the others; it was retained. The small workload's median paired
speedup was 1.018, compared with 1.024 from dividing the workload medians. Complete invocation
medians also improved, from 2.670/9.644/9.952 to 2.635/9.454/9.798 s. Individual samples and early/evolved
step distributions remain in the raw records; these are descriptive results, not confidence intervals.

Separate disabled-effect traces explain the removed work:

| Observation over 480 steps | Control | Candidate |
| --- | ---: | ---: |
| Kernel launches | 99,840 | 99,840 |
| Stream completions | 24,481 | 14,901 |
| Host-to-device copies | 1,920 | 483 |
| Host-to-device bytes | 1,698,743,040 | 427,331,424 |
| Device-to-host copies | 12,480 | 12,480 |
| Device-to-host bytes | 2,972,920,320 | 2,972,920,320 |
| Tracked peak allocation | 59,696,464 bytes | 59,696,464 bytes |

Twenty fixed-preparation completions disappear from each warm timestep. Three initial uploads
remain, followed by one offset upload per timestep. Diagnostic trace times are not substituted
for primary solver timings, and tracked allocation excludes unobserved driver/context memory.

## Verification and assessment

Both exports passed 292 ordinary release tests, explicit CUDA application checks, seven CUDA
integration checks, strict Clippy, formatting and native injected-fault tests under address and
undefined-behaviour sanitisation. The control/candidate explicit CUDA library runs passed 22/23
tests. The added test checks device inputs before/after promotion, repeated acceptance rejection,
empty/tail counts, all block sizes, cancellation and panic after prediction, then retry against a
serial trajectory. Existing integration tests cover every cancellation poll and numerical rollback.
Local parent verification passed 78 tests.

Seven regression trajectories and all paired records agreed exactly, including warnings. The
large disabled/enabled cases retained 259/181 warning-bearing steps; completion is not physical-quality
approval. Independent readers reconstructed timings and trace counts and rejected six altered claims.
Preflight found a private test-clock constructor and then an unused test outcome; both were corrected
before timing. Their diagnostics are retained. No hosted check or fresh GPU memory-sanitiser run is claimed.

The small, consistent saving, explicit ownership boundary, unchanged allocation peak and absence of
numerical regressions justify retention. The earlier reservation-only trial remains rejected;
this comparison changes preparation and
accepted-state ownership together. It does not establish real-time simulation: about one
simulated second still costs nearly nine solver seconds. Next prioritise a separate cell-run indexing
comparison against repeated neighbour searches. Larger submissions and reduced host observation still
need an explicit snapshot/cancellation design. Changing particle counts or planes would require residency
invalidation; current Simulation inputs are immutable. Compilation's image pipeline was not rebenchmarked.
Both repositories remain uncommitted on their existing branches, with tags and gitlink unchanged.
