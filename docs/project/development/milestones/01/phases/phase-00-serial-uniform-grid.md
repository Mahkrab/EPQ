# Phase 0 serial uniform-grid implementation and verification

## Starting point

Work began from EPQ `7fc932586a572f281dfe982e2fdaa2785df562a1` and assessed Maelstrom base
[`2d05b4b9c35e7679156bf29fd34535ca35e9dd26`](https://github.com/Mahkrab/Maelstrom/tree/2d05b4b9c35e7679156bf29fd34535ca35e9dd26),
the matching `milestone-01/phase-00/start` checkpoints; both worktrees were clean. The
[inherited numerical contract](/docs/project/development/milestones/00/phases/phase-00-design-contract.md),
[exact comparison policy](/docs/project/development/milestones/00/reference-verification.md) and
[measurement boundary](/docs/project/development/milestones/00/measurement-protocol.md) remain the basis.
The implementation assessed here is Maelstrom
[`b179e6e42b4efd6e269d6eb35fbee50dba4fcfa1`](https://github.com/Mahkrab/Maelstrom/tree/b179e6e42b4efd6e269d6eb35fbee50dba4fcfa1).
All 80 source-file hashes in the retained working-tree report match that committed implementation.

## Scope and outcome

The application selects `--backend brute-force` or `--backend uniform-grid`. Brute force
remains the default, including existing library constructors and workflow calls. Both methods feed
one serial timestep implementation. Binary32 physics, configured Jacobi work, projection, diagnostics
and atomic acceptance are unchanged. No new dependency, numerical input, schema or golden was needed.

Backend and run identities distinguish discovery; physical input/configuration identities agree.
CLI replay restores the recorded method and rejects unsupported contracts. The existing
`replay_inputs` helper still accepts historical brute-force records; the new `replay_execution`
also returns discovery selection, preventing grid records from silently becoming brute-force runs.
The [usage guide](https://github.com/Mahkrab/Maelstrom/blob/b179e6e42b4efd6e269d6eb35fbee50dba4fcfa1/docs/usage.md) documents both selections and replay.

## Decisions and implementation

### Coverage, ordering and storage

The [grid implementation](https://github.com/Mahkrab/Maelstrom/blob/b179e6e42b4efd6e269d6eb35fbee50dba4fcfa1/src/neighbours/grid.rs) uses a
sorted sparse vector of occupied-cell entries. It avoids allocation proportional to spatial volume
and does not depend on hash iteration. Each particle appears once; each query visits the containing
cell and its 26 neighbours. Candidate rows exclude self, apply the original checked binary32
distance and strict comparison, then sort by slice index. The solver sorts by stable
identity before stepping, preserving reduction order.

The uniform width is the smallest power of two at least `max(h, 2^-72, M * 2^-50)`, where `h` is
support radius and `M` is the largest absolute input coordinate. Mapping uses
`floor(binary64(position) / width)`, including negative coordinates and signed zero. Power-of-two
scaling is exact; indices are bounded by `2^50`, checked before conversion, and adjacent offsets
use checked addition. Extreme coordinates enlarge cells instead of saturating indices or losing particles.

This width also gives a coverage argument for the actual arithmetic. If an exact axis separation
reaches a finite power-of-two width, monotone rounding cannot reduce subtraction below that width.
Its square is exact and nonzero at the selected minimum width, or overflows. Non-negative sums and
square root therefore cannot return a finite distance below the width. Every admitted neighbour
differs by less than one cell width on each axis. The minimum matters because tiny squared distances
can underflow to zero and admit pairs farther apart than `h` in real geometry. Binary64 is used only
for indexing; it never replaces the binary32 membership calculation.

### Validation and timestep ownership

Brute force also rejects overflowing distances between distant particles. Skipping their cells must
not hide those failures. A finite binary32 bounding-box diagonal proves all pair distances finite
by monotonicity. If that check cannot prove safety, an actual-pair validation pass runs in reference
order. An unoccupied box corner cannot create a spurious rejection, and the first numerical error
remains the reference's error. This resolves an implementation issue without revising the inherited contract.

Entries, rows and interaction growth use fallible reservations; capacity failure and invalid indexing
return typed errors. Neither search returns partial membership. Search state belongs to its call,
and grid/reference solvers own separate accepted snapshots. Membership is built once from complete
prediction, retained throughout Jacobi, and rebuilt next timestep. Fresh density audits still use
brute force independently. Construction, validation, enumeration, sorting and search-storage destruction
remain within the existing measured step/search boundary.

## Verification

Verification ran locally on 17 October 2026 with Rust/Cargo 1.98.1, x86_64 WSL2 Ubuntu 24.04.5.
Locked/offline debug and release suites each passed **178 integration tests, 5 unit tests and
2 doctests**. Formatting, strict all-target/all-feature Clippy and warning-free Rustdoc also passed.

[Independent geometry tests](https://github.com/Mahkrab/Maelstrom/blob/b179e6e42b4efd6e269d6eb35fbee50dba4fcfa1/tests/uniform_grid.rs) cover all adjacent directions,
negative and exact boundaries, strict support, ordering, coincident/dense/sparse inputs, invalid
arguments, repeated construction, distance overflow and underflow. Generated comparisons cover
translated/scaled clouds, arbitrary finite bits and power-of-two boundaries throughout the finite
exponent range. Unit checks force index and reservation-capacity errors.

Complete grid outputs match both frozen goldens, including signed zero, every checkpoint/audit,
CFL diagnostic and status, in ordinary, total-measured and stage-profiled execution. Every frozen
family size through 8,000 particles also passes a one-step comparison. Stage-by-stage cancellation,
retry, membership retention/rebuilding, numerical/plane rollback, late failure, empty runs, warnings,
CLI selection, replay and output refusal have explicit regressions. A new rebuilding fixture initially
failed because projection reconstructed a separating velocity; an approaching-particle control now
exposes stale membership. An existing replay-error test also caught missing supported-version context,
which was restored without weakening the assertion.

The [retained comparison](/docs/project/development/milestones/01/assets/verification-v1/README.md)
contains full release CLI grid results, hashes, commands, source/build context and per-checkpoint error
reports. Both complete outputs and their CLI replays agree exactly. Only declared backend/run identity,
build context and optional timing fields are excluded from cross-backend numerical acceptance.

## Limitations and Gate G00

**G00 is satisfied locally.** Dense occupancy, enlarged cells in extreme domains, row ordering and
the exceptional full-pair validation pass can reduce the benefit of partitioning. Interaction storage
can remain quadratic; checked reservations are not a process memory budget. Actual allocator exhaustion
was not induced. Full 480-step equivalence is established for the 64-particle golden, not every family size.
No PC speedup, memory measurement, hosted verification or cross-platform bitwise claim follows.

The parent gitlink records the assessed Maelstrom commit. Annotated
`milestone-01/phase-00/complete` tags identify the completion checkpoints in both histories.
The original working-tree report and results are retained unchanged; publication and hosted
verification are separate from this local checkpoint.
