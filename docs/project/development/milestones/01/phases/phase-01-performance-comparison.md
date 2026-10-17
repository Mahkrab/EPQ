# Phase 1 paired PC measurement and comparison

## Starting point

EPQ began at `78652854eb22cd7985e8e2e22af7595f977bc011`, pinning the verified Maelstrom
[`b179e6e42b4efd6e269d6eb35fbee50dba4fcfa1`](https://github.com/Mahkrab/Maelstrom/tree/b179e6e42b4efd6e269d6eb35fbee50dba4fcfa1).
Matching `milestone-01/phase-01/start` tags identify these commits. Both worktrees were clean.
The [correctness record](/docs/project/development/milestones/01/phases/phase-00-serial-uniform-grid.md)
qualified grid discovery, but the existing collector selected only brute force and no grid performance
campaign was retained. The user authorised completing this prerequisite before evaluation.

## Scope and outcome

The collector now selects either search explicitly and records its identity. A paired entry point
collects fresh brute-force controls followed by grid execution on the primary PC. The
[measurement policy](/docs/project/development/milestones/00/measurement-protocol.md), seven input sizes,
480-step requests, factor-four refinement, eight iterations, checkpoints, one warm-up, three primary
samples, separate profile and timeout/grace budgets are unchanged. No solver optimisation or numerical
repair is introduced by this work.

The [retained PC campaign](/docs/project/development/milestones/01/assets/performance-comparison-pc-v1/README.md)
contains all 70 benchmark attempts and two replayable correctness results. Every request completed
480 steps without warnings, failures or timeouts. All complete numerical outputs agree exactly across
searches. Grid medians are slightly slower through 1,000 particles, then faster at 1,728 and above,
reaching 1.618× at 8,000. The retained report shows the crossover, spread and bottlenecks.

## Decisions and implementation

The existing collector, compaction, timing checks and summary arithmetic are reused. Backend selection
changes execution identity only. The paired verifier requires identical source, binary, manifest,
policy, collector files and relevant environment fields. Each clean full attempt is compared with
the same-size brute-force warm-up, excluding only backend/run identity, timings and variable build
context. Physical identities, sign-sensitive snapshot/input hashes, every checkpoint audit, accepted
CFL diagnostic and disposition remain in acceptance. Missing or unclean primary sets have no ratio.

The old baseline remains unchanged and its report still regenerates byte for byte. It is context,
not the denominator of the new speedup calculation. Fresh same-build controls reduce ambiguity from
the old source revision and campaign conditions. The older source predates checked search reservations
and the selectable search boundary, despite sharing the numerical inputs and policy. Changes between
those campaigns cannot be attributed solely to the grid. Fixed brute-force-first collection order is retained
explicitly as a possible load/thermal bias; three samples do not remove that limitation.

The PC's existing checkout was older. A separate temporary checkout was created from bundles of the
exact local commits, leaving the original PC checkout intact. Rust 1.98.1 was selected through
`RUSTUP_TOOLCHAIN`; default build flags, affinity, priority and frequency policy were retained.
The full release suite and parent collector tests passed there before measurement. During collection,
no other project checks ran on the PC. Grid bounds validation, cell construction, enumeration, row
sorting and temporary search-storage destruction remain within discovery timing; interaction-row
destruction remains within the total step.

## Verification

On 17 October 2026, local and PC release suites each passed 178 integration tests, five unit tests
and two separately run doctests. Eighteen parent collector tests passed on both devices before
collection; the final 19-test suite passed on both after review. New tests
cover a known median ratio, absent/incomplete primary sets, interruption, duplicate sample identities,
backend/source/environment disagreement, signed zero, intermediate snapshots and CFL changes.
Existing timeout, failed-attempt, profile-separation and non-replacing publication tests remain in use.

Fresh local execution of both retained correctness commands and CLI replays matched every numerical
bit. All 80 source hashes, frozen fixture hashes and comparison-policy hash in the retained grid
verification report were checked before collection. Raw hashes, source/collector provenance, exact
physical outputs, primary statistics, throughput, profiles and ratios were independently checked from
the retained PC files without collector imports. Both backend reports and the comparison regenerated
byte for byte on the PC and locally. The dataset README explains the recorded collector's only later
code difference: a tested two-line interruption guard that prevents launching another series after
cancellation. It does not affect these uninterrupted measurements.

## Limitations and Gate G01

**G01 is satisfied by the retained same-device evidence.** Both searches completed the seven-size
family through 8,000; no larger series was collected or practical maximum established. No fallback
device or numerical optimisation was used. The subsequently authorised
`milestone-01/phase-01/complete` tags retain this evidence and the measured Maelstrom commit
in their respective histories. The records were prepared before checkpointing; these tags capture
the separated work rather than an earlier unrecorded development boundary.
Measurements cover the declared family and machine, not arbitrary clustering, memory use, physical
fluid accuracy, statistical significance or cross-platform reproducibility.
