# Phase 5 implementation and verification record

## Starting point

Maelstrom started from the completed headless-workflow commit
[`a126ac215ca51384f330b3c4f3357b5c148b89ce`](https://github.com/Mahkrab/Maelstrom/tree/a126ac215ca51384f330b3c4f3357b5c148b89ce).
The library already supported headless runs and replayable results, but the binary
printed a greeting. The [headless-workflow record](/docs/project/development/milestones/00/phases/phase-04-diagnostics-results.md)
therefore left Gate G04 open pending the public CLI.

Both repositories now use `phase/00-05-cli`. The annotated `milestone-00/phase-05/start`
tags were created retrospectively on 15 October 2026 at the committed starting points:
Maelstrom's commit above and EPQ `40b1703e5f3f8c99ae67174a8040c8fa2734ce35`.
Work had already begun on the milestone branches. These local tags capture only the
baseline, not the staged or unstaged implementation, repairs or documentation.

## Scope and outcome

The local implementation exposes `maelstrom scenes`, `validate`, `inspect`, `run`
and `replay`. It supports bundled and external scenes, explicit configuration
selection and overrides, step or simulated-duration limits, correctness checkpoints,
text or JSON results, standalone snapshots and cooperative Ctrl-C cancellation.

The assessed source is the **uncommitted Maelstrom working tree** on top of the
starting commit, with EPQ based on `40b1703e5f3f8c99ae67174a8040c8fa2734ce35`.
Links to the [CLI](/Maelstrom/src/cli/mod.rs),
[subprocess tests](/Maelstrom/tests/cli_workflow.rs) and
[user guide](/Maelstrom/README.md) below identify live working files, not an immutable
completion revision. No implementation commits, completion tags, pushes or gitlink
updates have been made; only the local phase branches and retrospective start tags exist.

## Decisions and implementation

Every run names its scene and limit. `validate` and `inspect` also work on configuration
alone. Bundled scenes embed the existing TOML files and defaults, allowing the installed
command to work outside the checkout; external inputs retain the ordinary scene-relative
configuration loader. `--config` deliberately replaces the scene's base selection while
preserving its overlays. `--set` accepts strict primary-field TOML literals. Resolution
keeps the existing default, configuration-file, scene and command-line precedence and
field provenance. Duration rounds up to whole steps using the effective fixed timestep.

Clap supplies structured parsing, help, version discovery and argument errors. Its
features are limited to parsing and help requirements, without environment-selected
inputs or colour. Ctrlc supplies the interrupt handler; it sets an atomic flag checked
by the existing transactional solver. Neither dependency changes numerical work.
The binary delegates to the library, with parsing before stepping and presentation after it.

Stdout carries requested data; stderr carries warnings, verbose context and errors.
Quiet mode retains data and errors. Plain presentation has no terminal-dependent colour,
animated progress or prompts. Distinct exit codes identify usage, input, execution,
publication and cancellation failures. Help and the user guide document precedence,
defaults, examples, channels and compatibility boundaries.

Results reuse existing versioned records and safe publication. A small library addition
publishes standalone snapshots through the same non-replacing writer and retains any
failure in the result. Preflight checks reject existing files, symlinks, shared destinations
and missing directories; publication itself still refuses replacement if a destination
appears afterwards. Scene-selected configuration errors now identify the dependency path.

### Boundary correction discovered through the CLI

The supplied `falling-block-20 --duration 10` run exposed a projection defect on
its third step. Binary32 subtraction projected `x = 4.0276384` to `1.4000001`
against a wall at `1.4`, and the strict acceptance check correctly rejected it.
An independent scalar reproduction also showed that a distant candidate could
project to zero rather than contact, demonstrating a general cancellation defect.

The user authorised a [numerical contract correction](/docs/project/development/milestones/00/phases/phase-00-design-contract.md).
Exact axis normals now obtain the constrained coordinate directly from the signed
offset. Oblique arithmetic, projection order, strict acceptance and finite checks
remain intact. Backend identity advances to `v2`, preventing silent replay of
earlier numerical evaluations. The regression fails with the previous code;
tests cover all six directions and 240 combinations of offset and separation,
plus strict rejection and a near-axis normal that must retain the general formula.

### Regularisation repair following particle collapse

Longer CLI runs subsequently exposed numerical instability despite successful acceptance.
The [initial repair record](/docs/project/development/milestones/00/numerical-repair-01.md)
documents the independent equation audit, revised `defaults-v2.toml` regularisation,
preserved historical settings and bounded collapse regressions. The
[second repair record](/docs/project/development/milestones/00/numerical-repair-02.md) adds separation,
energy and convergence evidence and selected `defaults-v3.toml`. CLI completion establishes the
workflow contract; it does not certify coherent fluid behaviour or benchmark readiness.
The [third repair](/docs/project/development/milestones/00/numerical-repair-03.md) adds explicit
timestep refinement and configurable fixed solver work. It selects
`defaults-v4.toml` for all falling-block scenes while preserving exact historical replay.

## Verification

Checks ran locally on 14 October 2026 under WSL2 Ubuntu 24.04.5 LTS, Rust/Cargo 1.98.1,
`x86_64-unknown-linux-gnu`. Cargo verification used `--locked --offline`; simulation
tests ran with display variables unset. Initial fixture-schema and compilation mistakes
were corrected, then all final checks passed without weakening numerical assertions.

| Local check | Observed result |
| --- | --- |
| `cargo fmt --all -- --check` | Passed |
| All-target, all-feature `cargo check` and Clippy with `-D warnings` | Passed |
| Strict Rustdoc with `--no-deps --all-features` | Passed |
| All-target, all-feature tests in debug and release | After broader qualification, each passed 148 integration tests, including 23 CLI, 18 workflow and 12 fluid stability tests, plus three unit tests |
| All-feature doctests in debug and release | Each passed two compile-fail snapshot tests |
| Local installation and commands outside the checkout | Passed help, version, discovery, validation, inspection, a 12-step named/external run, snapshots and byte-identical replay |
| `git diff --check` in both repositories | Passed |

Formatting, checking, Clippy, strict Rustdoc and both profiles' full test and doctest
suites were rerun on 15 October 2026 and passed with the same totals. This does not
rerun the installed-command checks or the broader qualification matrix recorded elsewhere.

The CLI tests invoke the public executable with closed stdin and captured output.
They exercise discovery, configuration-only and scene validation, complete effective
inspection, all bundled inputs, selected configurations, external scenes, limits,
checkpoints, output files and replay. One-particle free fall has independently known
exact binary values. An overflowing velocity demonstrates numerical failure with
unchanged accepted state. A real SIGINT demonstrates exit 130, a cancelled record
and state equal to an uninterrupted run of exactly the accepted step count.

| Gate G04 evidence | Direct local evidence |
| --- | --- |
| Every required journey works through the CLI | Subprocess tests cover discovery, validation, inspection, named/external execution, explicit configuration, checkpoints, snapshots and replay |
| Help, errors, channels and statuses support automation | Tests separate stdout/stderr, check documented failure codes, closed-input operation, broken stdout and refusal to replace files |
| Recorded inputs reproduce the same serial run | External scene/configuration execution replays byte-identical JSON after both original input files are deleted |
| Presentation and diagnostics do not alter accepted state | Text, JSON, quiet, verbose and checkpoint choices preserve particle-state bits and accepted-step diagnostics |

The existing workflow suite also rechecks independent density audits, warning retention,
immutable snapshots, replay identities and failure preservation. The new snapshot
publication test verifies unchanged state and retained failure history. These checks
cover the runner evidence required alongside the CLI.

`cargo install --path . --locked --offline --root /home/mahkrab/.local` installed the
tested release binary as `/home/mahkrab/.local/bin/maelstrom`, already on the local PATH.
An installed-command check ran from a temporary directory and reproduced the same
12-step result from the named scene, explicit external files and recorded replay.

## Limitations and Gate G04

**Gate G04 is satisfied locally for the assessed working tree.** This completes the
requested implementation and user-facing evidence; it is not a durable Git checkpoint
or completion of the whole milestone. No `milestone-00/phase-05/complete` annotated tags
were created in either repository.

Hosted and Windows/macOS verification were not performed. Replay across platforms
is not certified. Observations remain in memory, cancellation is polled during stepping,
and publication requires hard-link support. Result and snapshot files are published
individually, with no directory-entry crash-durability guarantee. Benchmark selection,
golden-reference freezing and performance measurement remain later work.
