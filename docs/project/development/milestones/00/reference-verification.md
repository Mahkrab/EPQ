# Frozen serial reference and backend comparison contract

## Ownership and workload

This is the project decision for the comparison workload and tolerance policy assigned to Phase 6 by
the [numerical contract](/docs/project/development/milestones/00/phases/phase-00-design-contract.md).
It supplements that contract without changing the solver. The machine-readable input manifest lives
in [Maelstrom's reference directory](https://github.com/Mahkrab/Maelstrom/blob/48c43e7dec3d18a94ab74cc5efcbb6de13760654/reference/manifest.json); its SHA-256 entries freeze
the exact input bytes. Changes require a new family version and an explicit account of affected results.

The `falling-block-refined-v1` family uses the existing external falling-block scenes and
`config/defaults-v4.toml`, with the existing explicit factor-four timestep refinement. The resolved
timestep is binary32 `0.0020833334 s`, and the complete correction scale is `0.0625`. Gravity,
`0.05 m` spacing, support ratio two, eight Jacobi iterations, relaxation scale 20, artificial pressure,
plane order and every other primary setting retain their recorded values. This is a named numerical
variant of the unrefined reference, shared by every compared backend; it does not replace historical defaults.

The particle-count sequence is **64, 216, 512, 1,000, 1,728, 4,096, 8,000**, corresponding to
axis counts **4, 6, 8, 10, 12, 16, 20**. Only the lattice extent and box dimensions change. Each
request performs **480 fixed timesteps**, approximately one simulated second, with correctness
checkpoints **0, 1, 120, 240, 480**. Step counts are authoritative; duration rounding is avoided.
The 64-particle member is the golden correctness workload. The full size sequence is frozen for
later scalability measurements; freezing a size does not assert that it is practical to time.

The falling block exercises gravity, changing support, free surfaces, fluid corrections, floor contact
and spreading without rendering. Initial, pre-impact, impact and post-impact observations make it more
informative than free fall alone. The existing independent separation, compression and energy tests
remain necessary: a golden result detects change but cannot establish physical correctness by itself.
Factor four is selected before golden generation to avoid the unrefined run's CFL warnings using the
already qualified matched-refinement mechanism. Any warning in a selected run must be retained and
disqualifies it as a warning-free baseline; it must never be suppressed or repaired by adaptive stepping.

An additional unforced 27-particle lattice runs 12 steps at the unrefined numerical settings, observing
steps 0, 1, 4 and 12. Its external scene and golden output are independent fixtures, not another
scalability sequence. It supports short multi-step comparison against the independent binary64 equations.

## Frozen outputs and provenance

Each golden JSON is an ordinary versioned CLI result: complete effective configuration, initial
particles, ordered planes, request, every accepted CFL diagnostic, checkpoint snapshots and density
audits, final snapshot and completion status. It can be replayed without the original files.
The recorded build revision identifies the exact unchanged solver implementation used to generate it.
The manifest, golden files and verification tests are retained in Maelstrom commit
[`48c43e7dec3d18a94ab74cc5efcbb6de13760654`](https://github.com/Mahkrab/Maelstrom/tree/48c43e7dec3d18a94ab74cc5efcbb6de13760654),
identified by `milestone-00/phase-06/complete`. EPQ's matching checkpoint pins that exact commit;
the golden files retain their original generating solver revision.

Repeated serial runs on the supported environment must match every binary32 bit, particle identity,
step, warning and completion outcome, including signed zero. Build context (revision, debug assertions,
OS and architecture) may differ between verification builds; physical input identity, backend contract,
request and numerical output must agree. No cross-platform bitwise guarantee is inferred.

## Later-backend comparison policy

This policy is named `reference-comparison-v1` for comparison reports.

Input/configuration identity, precision, timestep and iteration count, checkpoint sequence, particle
identities and order, support membership, plane order, accepted-step count, completion status, failure
classification, warning flags and availability of audit/CFL values must match **exactly**. The grid
backend must preserve serial reduction order and therefore match all numerical output bits exactly.
Parallel execution may use the following absolute per-component limits, evaluated after converting
both finite binary32 values to binary64; equality at a limit passes:

| Quantity | Absolute limit | Rationale |
| --- | --- | --- |
| Position | `1e-5 m` | 0.02% of the fixed spacing; far below the half-spacing separation guard |
| Velocity and maximum post-acceleration speed | `0.005 m/s` | Approximately one position allowance divided by the refined timestep |
| Mean and maximum absolute relative density error | `1e-4` | 0.01 percentage points; much smaller than the compression guard |
| Finite CFL limit | `1e-6 s` | Less than 0.05% of the refined timestep; warning classification still matches exactly |

These are project acceptance budgets for this frozen workload, not measured GPU error bounds or
permission to alter equations. Every checkpoint and final particle component must pass; averages
cannot hide outliers. Non-finite values always fail. Relative errors may be reported for diagnosis
but do not relax these limits near zero. Passing numerical limits does not excuse membership,
Jacobi, boundary or transactional violations. Later backends must also pass the focused contract suite.
Changes to these budgets require reviewed evidence and a versioned policy, never tuning to a failing backend.

## Required disagreement report

Retain a machine-readable report and a readable explanation identifying both implementation revisions,
backend IDs, compiler/build flags, environment, input/configuration IDs, fixture hashes, request and
policy version. Record structural mismatches before numerical comparisons. For every checkpoint and
final snapshot report particle/component counts, maximum absolute and RMS errors separately for
position and velocity, the worst particle identity and axis, the applied limits and pass/fail.
Record expected/actual audit values, every mismatching CFL step and warning, completion/failure status,
and the first divergent checkpoint (or step when known). Preserve the original candidate result and
reference hashes so discrepancies can be reproduced. Missing checkpoints, unavailable metrics,
non-finite values or a truncated run are failures, never omitted samples. Timing and presentation
metadata are reported as context and do not participate in numerical acceptance.

Performance sampling, warm-up, measurement boundaries and baseline results remain outside this verification contract.
