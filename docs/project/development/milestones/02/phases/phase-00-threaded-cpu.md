# Phase 0 threaded CPU implementation and verification

## Starting point

Work began from clean EPQ `aecae771f9ce9e8b24cfb3d6e8a4509a380db4ef` and Maelstrom
[`2156bdca7f6702cea18030a8b0c603dfa393e036`](https://github.com/Mahkrab/Maelstrom/tree/2156bdca7f6702cea18030a8b0c603dfa393e036),
the matching `milestone-02/phase-00/start` checkpoints. The
[serial-grid handoff](/docs/project/development/milestones/01/serial-uniform-grid.md) identifies Jacobi
work as 82.83% of the largest grid profile. That finding motivated distributing independent particle
calculations. It does not establish a threading speedup.

## Scope and outcome

The CLI and library support threaded grid execution while retaining both serial controls and their
defaults. For example, `run falling-block-04 --backend uniform-grid --execution threaded --threads 3
--steps 12` selects a private three-worker pool. Replay restores the exact execution settings.
The [usage guide](/Maelstrom/docs/usage.md#threaded-cpu-execution) documents selection, validation,
resource ownership and failure behaviour. These implementation links describe the current worktree;
the base commit above does not contain this change.

The [numerical contract](/docs/project/development/milestones/00/phases/phase-00-design-contract.md)
and [comparison policy](/docs/project/development/milestones/00/reference-verification.md) are unchanged.
No floating-point reduction order changes, so this implementation requires exact binary32 agreement,
including signed zero. The parallel tolerance allowances were not needed or used to accept a difference.

## Decisions and implementation

### Work distribution and barriers

The [Jacobi implementation](/Maelstrom/src/fluid.rs) distributes three separate passes: current
interaction filtering, density/constraint/multiplier calculation, and position correction. Indexed
particle ranges are split by Rayon's scheduler; each particle retains its ascending reductions.
Every pass finishes before the next reads its results. Positions and fixed membership remain
immutable throughout the stage, and all multipliers exist before any correction is calculated.
The serial and threaded paths share per-particle equations, with serial orchestration retained.

Discovery stays serial, retaining the independently checked grid's rounded-distance coverage,
strict support and overflow validation without adding another concurrent structure. Prediction,
acceleration/CFL, candidate formation, per-particle ordered projection and acceptance also remain
serial: the measured bottleneck justifies concentrating concurrency on Jacobi first. Membership is
still built once from complete prediction, then filtered using current distances. Fresh brute-force
audits remain independent of that membership.

### Resource ownership and failure order

[`Execution`](/Maelstrom/src/execution.rs) owns a private reusable Rayon pool. Rayon 1.12.0 was selected
to provide scoped, borrowed parallel work and reusable scheduling without a custom unsafe worker
implementation. Default features are disabled; Cargo.lock retains Rayon, rayon-core, either and
three Crossbeam packages. This adds scheduler dependencies and allocation/dispatch overhead; no
performance benefit is claimed before measurement.

Explicit worker counts are 1–256, with oversubscription allowed. The default for threaded mode is
process-visible available parallelism capped at 256. A failed query or pool construction is explicit;
an admitted pool must have exactly the requested count. No global pool or environment-selected Rayon
count is used. Empty stages contain no particle tasks; small non-empty inputs and one-worker mode
still use the pool. Each solver owns its state and resources independently.

Workers return indexed results, all of which are joined before the caller chooses the first error.
This preserves pass/particle error precedence instead of reporting whichever worker finishes first.
Cancellation predicates run only on the caller at the existing polls. A complete Jacobi stage
finishes before its next poll; accepted state changes only after the final validation and poll.
Failed or cancelled buffers are discarded, allowing a clean retry.

Execution mode is separate from `SearchBackend`. The shared `Simulation` retains `SerialSimulation`
as a compatibility name. Threaded records add explicit execution settings and a distinct backend/run
identity; physical hashes and historical serial records are unchanged. `replay_options` retains all
settings; older helpers reject records whose settings their return types cannot represent.

## Verification

Local verification used Rust/Cargo 1.98.1 on x86_64 WSL2 Ubuntu 24.04.5 on 17 October 2026.
Full debug/release suites passed, followed by targeted reruns after extending failure checks: the final
coverage is **194 integration tests, eight unit tests and two doctests** in each profile. Formatting,
strict all-target/all-feature Clippy and warning-free Rustdoc passed. Nineteen existing parent baseline
tests and five new report-verification tests passed.

[Independent tests](/Maelstrom/tests/threaded_execution.rs) check equations, deliberate stale/in-place
controls, concurrent workers, complete barriers, dense/sparse/boundary/extreme inputs, empty and uneven
partitions, fewer particles than workers, repeated errors, every cancellation poll, rollback/retry,
independent simultaneous solvers and pool lifecycle. Workflow tests compare audits, warnings, invalid
inputs, late failures and cancellation with serial results. The report tests deliberately corrupt
components, identities, signed zero, checkpoints, audits, warnings and execution settings.

The [retained evidence](/docs/project/development/milestones/02/assets/verification-v1/README.md)
contains complete CLI results and component reports for both goldens, serial controls and workers
1, 2, 3 and 7, including ordinary, measured, profiled and replayed requests. Larger family members
through 8,000 particles agree exactly for a complete step with initial/final audits. No fixture,
configuration, golden, tolerance or sampling rule was changed.

## Limitations and Gate G00

**G00 is satisfied locally.** Exact repeatability is supported for the tested builds and worker counts;
no cross-platform bitwise guarantee follows. Full-duration qualification covers the two goldens,
not every larger family size. Actual OS exhaustion was not induced; spawn failure was injected.
Dense membership and audit costs, pool overhead, cancellation latency and memory use remain limits.
Dispatch, barriers and repeated allocations are inside solver timing; one-time pool setup/teardown
are outside it. No PC scaling, speedup, memory or hosted-verification claim is made.

The assessed implementation remains uncommitted above the full Maelstrom base identified here;
per-file hashes, a source fingerprint and the release binary hash identify its retained evidence.
Both indices and EPQ's gitlink remain unchanged. Intended `milestone-02/phase-00/complete` annotated
tags in both repositories require separate checkpoint authorisation and have not been created.
