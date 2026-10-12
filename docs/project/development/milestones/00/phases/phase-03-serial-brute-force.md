# Phase 3 implementation and verification record

## Starting point

The annotated `milestone-00/phase-03/start` checkpoints identify EPQ
[`1ec05bd693df1260d67d259429715309a1466b50`](https://github.com/Mahkrab/EPQ/tree/1ec05bd693df1260d67d259429715309a1466b50)
and Maelstrom
[`4f4e71882fd72578f648491f2524b960baeaa5f8`](https://github.com/Mahkrab/Maelstrom/tree/4f4e71882fd72578f648491f2524b960baeaa5f8).
These supplied the configuration, scene and numerical foundations, but not a complete serial timestep.

## Scope and outcome

The library now runs serial brute-force simulations from resolved scenes, composing the
existing foundations under the
[timestep contract](/docs/project/development/milestones/00/phases/phase-00-design-contract.md#timestep-contract).
It supports individual steps, multi-step requests, and cancellation.

## Decisions and implementation

The [simulation boundary](https://github.com/Mahkrab/Maelstrom/blob/19d2c64203b8048333b882eecfb0bb84cc1412e3/src/simulation/mod.rs) takes independent ownership of inputs after
revalidating configuration and planes, because callers can modify resolved records. Sorting particles once
by stable identity makes slice order suitable for every subsequent serial reduction. Keeping validated
configuration and calculated parameters immutable avoids repeated setup without changing arithmetic.

[Brute-force discovery](https://github.com/Mahkrab/Maelstrom/blob/19d2c64203b8048333b882eecfb0bb84cc1412e3/src/neighbours.rs) reads the complete prediction snapshot and produces
ordered, duplicate-free interaction rows, excluding self and pairs exactly at the support radius. Membership
stays fixed throughout the timestep. The [existing fluid calculations](https://github.com/Mahkrab/Maelstrom/blob/19d2c64203b8048333b882eecfb0bb84cc1412e3/src/fluid.rs) recompute
distances from each iteration's positions: leaving neighbours *:(* stop contributing, while newly close
particles wait until the next timestep. Density includes iself exactly once. These distinctions preserve the
selected approximation rather than silently changing which particles influence an iteration.

Each of four Jacobi iterations finishes all multipliers before calculating corrections from the same
immutable positions. Corrections remain separate until every candidate exists; planes then project candidates
in configuration order. This prevents serial execution from accidentally using another particle's updated
position. Final velocities come from the complete corrected and projected displacement.

Accepted particles and the completed-step counter change together only after all checks succeed. Numerical
errors, residual plane penetration and cancellation discard the proposal. Cancellation is cooperative between
stages, so an ongoing search or Jacobi calculation finishes before the next poll. Multi-step failures retain
earlier accepted steps and their outcomes, including CFL warnings; warnings do not adapt the timestep or
reject otherwise valid state.

[Read-only snapshots](https://github.com/Mahkrab/Maelstrom/blob/19d2c64203b8048333b882eecfb0bb84cc1412e3/src/simulation/state.rs) let callers retain requested checkpoints between
steps. Observation, future audits and formatting remain outside the step call, which supplies the logical
timing boundary. No clocks or density-error audit are implemented here.

## Verification

Coverage in the [serial integration tests](https://github.com/Mahkrab/Maelstrom/blob/19d2c64203b8048333b882eecfb0bb84cc1412e3/tests/serial_simulation.rs) includes support edges,
empty and coincident inputs, plane ordering, warning semantics and invalid inputs. An
[independent binary64 oracle](https://github.com/Mahkrab/Maelstrom/blob/19d2c64203b8048333b882eecfb0bb84cc1412e3/tests/support/serial_oracle.rs) evaluates small systems with separate
position and velocity tolerances. Deliberately incorrect variants distinguish stale distances, neighbour
rebuilding within a step, in-place updates, wrong iteration counts and final-only projection.

The repeatability test runs the 64-particle `falling-block-04` scene for 12 steps, comparing complete accepted
state bits and outcomes across repeated runs and reversed input order. Rollback tests compare state bits
after numerical and plane failures, cancellation at every poll, and retries against uninterrupted execution.
Together with the immutable-observation doctest, these demonstrate repeatability and atomic acceptance
without requiring a display.

Checks were rerun locally on 12 October 2026, using Ubuntu 24.04.5 LTS, Rust/Cargo 1.98.1 and
`x86_64-unknown-linux-gnu`. Build output used Maelstrom's ignored `target/` directory, with display
variables unset. Cargo build/test commands used `--locked --offline`. These results assess Maelstrom
[`19d2c64203b8048333b882eecfb0bb84cc1412e3`](https://github.com/Mahkrab/Maelstrom/tree/19d2c64203b8048333b882eecfb0bb84cc1412e3).

| Local check | Observed result |
| --- | --- |
| `cargo check --all-targets --all-features`; Clippy with the same target/features and `-D warnings` | Passed |
| `RUSTDOCFLAGS='-D warnings' cargo doc --no-deps --all-features` | Passed |
| `cargo test --all-targets --all-features`, debug and `--release` | Each passed 83 integration tests, including 20 serial tests, and one unit test |
| `cargo test --doc --all-features` | Passed one compile-fail snapshot test |
| `cargo fmt --all -- --check` | Passed after formatting; the malformed Rustdoc closing tag was also corrected |

EPQ's three Markdown utility tests and milestone asset check passed locally. The source permalinks were
checked against the committed Git objects, not fetched from GitHub.

## Limitations and Gate G03

**Gate G03 is satisfied by the inspected implementation and local evidence.** The complete timestep follows
the frozen mathematical and ordering contract; repeated runs produce identical accepted state in the tested
environment; failures and cancellation preserve atomic acceptance; and read-only snapshots provide the
observation boundary without a display dependency.

Diagnostics beyond CFL, result formats, the CLI, benchmark selection, baselines and optimisation remain
outside this record. Hosted CI, browser rendering, benchmarks and cross-environment repeatability were not
checked.

The annotated `milestone-00/phase-03/complete` checkpoint identifies the assessed Maelstrom commit. EPQ pins
that same commit through its gitlink; its matching completion tag identifies this record and the parent tree.
These completion checkpoints are local and await publication. The updated milestone plan is Git-ignored and
remains local.
