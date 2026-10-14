# Phase 4 implementation and verification record

## Starting point

The annotated `milestone-00/phase-04/start` tags identify EPQ
[`df43637e985afc40d825f8f536ce7dcca37c4e23`](https://github.com/Mahkrab/EPQ/tree/df43637e985afc40d825f8f536ce7dcca37c4e23)
and Maelstrom
[`19d2c64203b8048333b882eecfb0bb84cc1412e3`](https://github.com/Mahkrab/Maelstrom/tree/19d2c64203b8048333b882eecfb0bb84cc1412e3).

## Scope and outcome

Phase 4 added the headless workflow around the solver, without changing its timestep mathematics.
It accepts a resolved scene and a step/checkpoint request, retains accepted observations, and produces
replayable JSON or a human-readable summary. The assessed implementation is Maelstrom
[`a126ac215ca51384f330b3c4f3357b5c148b89ce`](https://github.com/Mahkrab/Maelstrom/tree/a126ac215ca51384f330b3c4f3357b5c148b89ce),
currently committed locally but not published.

The public CLI, benchmark-scene selection, performance baselines and rendering are outside this work.

## Decisions and implementation

The [workflow](https://github.com/Mahkrab/Maelstrom/blob/a126ac215ca51384f330b3c4f3357b5c148b89ce/src/workflow/mod.rs)
keeps execution and observation separate. Only the solver's step call advances state; checkpoint copying,
density auditing and output happen after it returns. This gives a clear solver timing boundary without
adding measurements or making checkpoint frequency part of the numerical behaviour.

The [density audit](https://github.com/Mahkrab/Maelstrom/blob/a126ac215ca51384f330b3c4f3357b5c148b89ce/src/diagnostics.rs)
follows the [numerical contract](/docs/project/development/milestones/00/phases/phase-00-design-contract.md).
It rebuilds support sets from accepted positions rather than reusing the solver's fixed membership.
Every particle contributes to the evaluation, self contributes once, and the result reports mean and
maximum absolute relative density error. Empty input has zero samples and unavailable metrics, not a
misleading zero error. A large finite error remains diagnostic and cannot change accepted state.

Reproducibility needs the values used, not just the names or paths of their files. The versioned
[records](https://github.com/Mahkrab/Maelstrom/blob/a126ac215ca51384f330b3c4f3357b5c148b89ce/src/workflow/record.rs)
therefore retain resolved configuration, provenance, ordered planes and particles. Schema version 1
preserves binary32 values, while particle identities and step counters use decimal strings so large
integers survive JSON consumers. Replay validates those inputs, their comparison keys and the backend;
it reconstructs the request, not a guarantee that a recorded failure or cancellation will recur.

Configuration and input identities come from the existing comparison keys. The run identity also includes
the backend contract, application version and requested step count. Display labels, provenance and
checkpoint selection do not change physical identity. Build revision is recorded when supplied at
compilation; otherwise its absence is explicit. `serde_json` handles portable records and `sha2` supplies
the stable identity digest, keeping both responsibilities outside the numerical solver.

Both [output formats](https://github.com/Mahkrab/Maelstrom/blob/a126ac215ca51384f330b3c4f3357b5c148b89ce/src/workflow/output.rs)
read the same observations. CFL warnings remain non-fatal and survive later steps. Validation, simulation,
audit, cancellation and publication failures remain distinct, retaining earlier accepted work where it
exists. File publication writes and syncs a temporary file before linking it into place; it does not
overwrite an existing destination or expose a partial write as a completed result.

## Verification

The [workflow tests](https://github.com/Mahkrab/Maelstrom/blob/a126ac215ca51384f330b3c4f3357b5c148b89ce/tests/headless_workflow.rs)
derive density expectations independently in binary64. They cover strict support, coincident particles,
self contribution, empty input and neighbours that appear only after projection. Failure tests check
accepted-state preservation, warning retention, cancellation, malformed replay inputs and publication.

A 64-particle falling-block fixture runs for 12 steps with and without observations, producing identical
accepted-state bits and CFL outcomes. A separate six-step run replays from its JSON with identical output.
These are test fixtures, not a selected benchmark. Snapshot round trips cover signed zero, subnormals and
the largest particle identity; compile-fail tests prevent mutation through snapshot accessors.

| Local check | Observed result |
| --- | --- |
| `cargo fmt --all -- --check` | Passed |
| `cargo check --all-targets --all-features`; equivalent Clippy with `-D warnings` | Passed |
| Strict Rustdoc, without dependency documentation | Passed |
| All-target, all-feature tests in debug and release | Each passed 100 integration tests, including 17 workflow tests, and three unit tests |
| All-feature doctests | Passed two compile-fail snapshot tests |

## Limitations and Gate G04

The local evidence supports the Phase 4 workflow requirements. **Gate G04 remains open:** it also requires
the public CLI and its user-facing checks. Hosted verification, cross-platform replay and benchmarks were
not performed. Diagnostics and requested snapshots remain in memory, so long runs need deliberate
checkpoint selection. Publication requires hard-link support and does not guarantee directory-entry
durability after a crash.

Neither repository has a `milestone-00/phase-04/complete` tag. Those are the intended completion checkpoints;
EPQ's gitlink still names the starting Maelstrom commit. The links here identify the assessed local commit,
but will not resolve on GitHub until it is published. This record does not establish a completion boundary.
