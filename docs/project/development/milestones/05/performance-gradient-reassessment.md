# Ordered gradient reuse reassessment

## Starting point and outcome

This resumes optimisation after scene usability on `phase/05-03-optimisation` in both
repositories. The starting commits are EPQ `3d043355c9744dee9355b5e045217e3c46a9124d` and
Maelstrom [`87145510a9e5d812066138c35f1fac82e4f593b0`](https://github.com/Mahkrab/Maelstrom/tree/87145510a9e5d812066138c35f1fac82e4f593b0).
The [earlier trial](/docs/project/development/milestones/05/performance-gradient-reuse.md)
found useful savings but rejected them under its historical admission rule. That outcome stays
unchanged. This is a fresh comparison against the implementation with both optional fluid effects.

**Decision: retain ordered gradient-prefix reuse.** The larger workloads improved in every pair,
the multiplier profile supports the mechanism, and the change adds no neighbour cache or explicit
device allocation. The [protocol](/docs/project/development/milestones/05/performance-gradient-reassessment-protocol.md)
and [retained evidence](/docs/project/development/milestones/05/assets/gradient-reassessment-v1/README.md)
identify the inputs, source hashes, commands and complete samples.

## What changed

The multiplier previously calculated each neighbour's gradient when building the owner vector,
then calculated it again for the squared-gradient sum. Positions do not change between those loops.
The implementation now accumulates lower-identity squared contributions during the owner traversal,
finishes the owner, inserts self in the original position and revisits only the higher-identity suffix.
It keeps the original additions rather than combining independently summed halves.

Prefix failures are recorded separately until all owner checks finish, preserving failure precedence.
Nothing is reused across position changes. Equations, solver iterations, neighbour membership,
ordering, timestep, cancellation and atomic acceptance remain unchanged. Existing independent
regression cases were retained, with empty input added to the multiplier-ordering case.

## A build mistake caught before retention

The first campaign accidentally shared a Cargo target directory. Its candidate had a new Rust
build identifier but contained the control's compiled CUDA code. A fresh candidate compile was
absent from both measured executables, explaining their almost identical multiplier profiles.
Those results cannot assess this optimisation and are retained as a disqualified build comparison.

The corrected collector uses separate target directories. It independently compiles each source's
CUDA code and checks the complete bytes inside the corresponding executable before qualification.
The two kernels must differ. A regression test now rejects stale CUDA code despite a changed Rust
identifier. The complete qualification and campaign were repeated; no initial samples were pooled
with the corrected results. Source and executable hashes alone had missed this correspondence gap.

## Primary-PC results

The PC used its Ryzen 9 7900X and RTX 4070 under WSL2, driver 610.88, CUDA 13.3.73 and Rust 1.96.0.
Both variants used locked offline release CUDA builds, device zero, 128-thread blocks, eight Jacobi
iterations, timestep refinement 4 and 480 unpaced steps. Each workload had one warm-up per variant
and five alternating measured pairs. Solver totals exclude rendering, output and checkpoint audits.

| Workload | Control median | Candidate median | Less solver time | Faster pairs |
| --- | ---: | ---: | ---: | ---: |
| 8,000 particles, effects disabled | 1.8212 s | 1.7996 s | 1.2% | 4/5 |
| 110,592 particles, effects disabled | 10.8888 s | 10.3664 s | 4.8% | 5/5 |
| 110,592 particles, both effects enabled | 11.2752 s | 10.7769 s | 4.4% | 5/5 |

The enabled case used XSPH coefficient 0.01 and confinement strength 0.1 m/s. It is a separate
workload, not a replacement historical baseline. The small case retained checkpoints 0/1/120/240/480;
the larger cases had none. Complete command durations also improved in median. All samples remain,
including the slower small pair; range overlap did not independently decide retention.

Separate disabled-effect profiles put multiplier device time at 2.030 s for control and 1.532 s
for candidate, about 24.5% less. Early and evolved windows both improved. Each trace retained
99,360 kernels, 24,481 stream completions and identical transfer counts and bytes. Traced allocation
peaks were unchanged at 59,696,464 bytes; this is not total driver memory. Instrumented component
times explain the ordinary results rather than replacing them.

## Verification and limits

Each corrected PC variant passed 292 ordinary release tests, 20 explicitly selected CUDA library
checks and two CUDA application-boundary checks. Strict CUDA Clippy, formatting and native
address/undefined-behaviour sanitiser checks passed. Other opt-in tests remain separately identified
in the raw logs. The seven bundled 64–8,000-particle trajectories and all paired results agreed
exactly, including diagnostics. Hardware checks covered overflow precedence, current support,
changed snapshots, self ordering, empty input and supported block sizes.

The independent reader reconstructed timing totals, medians, pair ratios, physical records and
profile operation windows. Altered timing, physical and profile summaries were rejected. Locally,
the complete headless CPU release suite and 67 parent performance-tooling tests passed. These
are laptop and primary-PC checks, not hosted verification or a passing device-memory sanitiser.

The larger disabled and enabled workloads retained 259 and 181 CFL-warning steps respectively.
Their exact agreement supports this runtime comparison, not physical-quality or real-time claims.
The gain and small implementation cost justify retention under the
[assessment policy](/docs/project/development/milestones/05/performance-assessment.md), without a fixed
percentage rule. Further gradient reuse and cooperative neighbour sorting remain separate work.

The assessed implementation is still uncommitted. Its 179 file hashes and focused patch against
the full starting Maelstrom commit identify the measured source; they are not a Git checkpoint.
Both new branches are local. No commits, tags, pushes, merges or parent gitlink changes were made.
