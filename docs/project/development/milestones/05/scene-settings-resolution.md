# Saved settings resolution

## Scope and implementation state

This records the settings-resolution work for Phase 02, following the
[settings contract](/docs/project/development/milestones/05/scene-settings-contract.md).
Implementation starts from Maelstrom
[`4a9675b5f9e3b7aa90335f5a77bdb3e82093a1b5`](https://github.com/Mahkrab/Maelstrom/tree/4a9675b5f9e3b7aa90335f5a77bdb3e82093a1b5),
with EPQ at `812dea60d8527b8ed977c6bd5d865199397aa374`.
The changes described here are uncommitted on `phase/05-02-scene-usability` in each repository;
the baseline commits do not contain this implementation or establish a completion checkpoint.

## What changed and why

Schema 2 now resolves primary numerical values before selecting and applying one refinement factor.
Later layers replace earlier selections, including a factor of one to reset saved refinement.
Invalid supplied values cannot hide behind overrides, and all derived assertions check the final
derived values. Schema 1 retains its original per-layer calculation so old inputs keep their meaning.
Scene and configuration versions must match. The numerical equations and backend implementations
were not changed.

A schema-2 lattice can inherit spacing from its numerical configuration. Explicit spacing still
acts as an exact assertion. Optional scene `[run]` settings supply a finite step count or simulated
duration; an explicit CLI limit replaces that selection. Inspection, headless execution, live-view
launch and compilation share resolution. Recorded runs retain effective inputs, so rerunning does
not reread scene files or apply a refinement recipe again.

Inspection now includes saved limits, presentation settings, field origins and portable source labels
with hashes of the exact input bytes. It also shows the unrefined timestep and correction scale,
selected refinement and effective values. Numerical comparison identities remain based on resolved
physics rather than filenames or presentation. Errors retain useful dependency filenames without
printing personal absolute directories.

Presentation parsing and camera validation live independently of graphics initialisation. A selected
scene discovers its neighbouring `render.toml`; `--render-config` replaces it, and explicit dimension,
stride and fit options take precedence. Only an absent optional file uses defaults. Headless running
does not read render settings; inspection and package validation can check them without graphics.
Fresh visual launches default to fitting initial particles unless a fixed camera is selected.

## Scene creation and migration

`scenes create` now writes a new schema-2 package with numerical, scene and render documents.
It validates the source under its original rules, writes effective numerical values without a
refinement recipe, clears overlays and removes validated duplicate lattice spacing. A source's saved
limit is retained; otherwise the new scene visibly saves a one-second duration.

Only explicitly supplied derived assertions are retained. They are written against final effective
values, with any replacement reported alongside its original layer and value. Adding every possible
assertion would have made ordinary edits fail against stale derived values, defeating the single
editable spacing decision. Existing source packages and existing destination directories are preserved.
Legacy render documents migrate with their selected fixed camera intact.

## Verification

Local verification on 25 October 2026 used WSL2 Linux 6.6.87.2 and Rust 1.98.1. The viewer-enabled library and integration
suite passed 285 tests across 30 targets. Twelve device checks were initially ignored; all ten
software-Vulkan checks were then explicitly run and passed using llvmpipe (LLVM 20.1.2). The two
hardware-adapter checks remain unrun. These checks include a compilation that discovers saved limits,
dimensions and stride, publishes the expected images and validates the resulting bundle.

The suite found a missing default provenance entry and a loss of useful dependency labels; both were
fixed. Numerical and golden regressions passed. Final review also added a recorded-input version
consistency guard; the affected library, CLI and replay targets were rerun with 104 tests passing.
New checks use exact binary fractions for refinement, independently known lattice positions and
single-particle free fall, and cover shadowed invalid values, final assertions, relocation, migration,
temporary overrides, saved edits, malformed inputs and preservation of previously accepted inputs.

The contract's three example files were also exercised through the executable: validation and
inspection accepted 64 particles, refinement four and the saved 480-step limit. Energy-colour drawing
was rejected before output, as intended. Strict Clippy passed for viewer-enabled and headless builds;
the headless resolution suites passed 12 tests. Rustdoc passed with broken internal links denied.
The three parent Markdown tests, repository-link checks and final whitespace review also passed.
No primary-PC benchmark, CUDA hardware qualification, native-window check or hosted verification
is claimed by this record.

## Remaining work

Render schema 2 validates fixed and kinetic-energy colour selections, but drawing still supports
only the existing fixed colour. Unsupported requests fail before starting graphics or publishing
output. Energy-gradient drawing, custom colours, fitting the full domain and saving the interactive
camera remain the planned presentation work. Multiple particle groups and container-box authoring
also remain outside this change. This record does not mark the whole phase or final evaluation complete.

The subsequent [scene-authoring record](/docs/project/development/milestones/05/scene-authoring.md)
covers the implemented initial groups and container boxes separately.

The subsequent [presentation record](/docs/project/development/milestones/05/scene-presentation.md)
covers the implemented camera persistence, domain fitting and particle colours.
