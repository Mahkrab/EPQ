# Phase 6 implementation and verification record

## Starting point

Phase 6 began from Maelstrom
[`54c5176fe0475b39e53759f11aab355c4c815583`](https://github.com/Mahkrab/Maelstrom/tree/54c5176fe0475b39e53759f11aab355c4c815583)
and EPQ `1f61be503b3dbfb540c0075bfd0d731f4da997df`, on
`phase/00-06-reference-verification` with matching `milestone-00/phase-06/start` tags.
Both worktrees were clean. The public application and numerical repairs already existed; a frozen
comparison family, reviewed golden output and later-backend comparison policy did not.

## Scope and outcome

The [reference contract](/docs/project/development/milestones/00/reference-verification.md) now freezes
the experiment before performance measurement. Maelstrom's
[manifest](/Maelstrom/reference/manifest.json) records exact input and golden SHA-256 hashes, requests
and particle-count order. Two complete golden results and
[seven reference tests](/Maelstrom/tests/reference_verification.rs) accompany the existing verification
layers. No production solver, defaults, dependencies or numerical expressions changed.

## Decisions and implementation

The canonical falling block uses the existing factor-four matched refinement, retaining eight
iterations, spacing and the other recorded numerical settings. Its 480 steps cover approximately one
simulated second, observing steps 0, 1, 120, 240 and 480. This avoids treating the unrefined run's CFL
warnings as an unqualified baseline. The existing 64–8,000-particle family supplies the fixed
scalability sequence; the 64-particle case supplies the primary golden. An unforced 27-particle
lattice supplies a second, short multi-step fixture.

Golden data were captured through the public CLI from the unchanged solver revision above, with
that full revision compiled into the result. Complete inputs, diagnostics, checkpoint states and
audits, final state and completion status are retained. Tests replay both results through the
library and public CLI and compare every numerical bit, including signed zero; only recorded build
context may differ. Mutated intermediate output and signed zero demonstrate that the comparator
can detect those changes. Verification never regenerates goldens.

An initial independently evolved binary64 lattice trajectory exceeded the proposed single-step
bounds: maximum position discrepancy grew from `27.4 nm` at step 1 to `34.7 µm` at step 12, with
final velocity discrepancy `0.00215 m/s`. This exposed accumulated precision sensitivity rather than
a per-transition equation failure. The retained test evaluates each complete transition independently
from the same accepted input, keeping `3e-6 m` and `4e-4 m/s` bounds. Every transition passes; an
in-place negative control is distinguishable. The full binary32 trajectory is checked exactly
against the golden. Binary64 evolution is not claimed to be the same experiment.

## Verification

Local checks ran on 15 October 2026 in x86_64 WSL2 Ubuntu 24.04.5, Rust/Cargo 1.98.1.
Locked/offline debug and release suites each passed **155 integration tests, three unit tests and
two doctests**, with no failures or ignored tests. Formatting, all-target checking, strict Clippy,
strict Rustdoc and whitespace checks passed. Parent Markdown unit tests, asset-policy checks and local
link checks also passed.

| Requirement or layer | Direct evidence |
| --- | --- |
| M00-0/1: complete serial brute-force execution | [Solver tests](/Maelstrom/tests/serial_simulation.rs): asymmetric equation oracle, fixed membership, next-step rebuild, ordered projection and reconstruction; [solver source](https://github.com/Mahkrab/Maelstrom/blob/54c5176fe0475b39e53759f11aab355c4c815583/src/simulation/mod.rs) and [pair search](https://github.com/Mahkrab/Maelstrom/blob/54c5176fe0475b39e53759f11aab355c4c815583/src/neighbours.rs) |
| Primitives, exact boundaries, invalid and non-finite values | [Kernel mathematics](/Maelstrom/tests/kernels_and_math.rs), [fluid equations](/Maelstrom/tests/fluid_foundations.rs), [motion, planes and CFL](/Maelstrom/tests/motion_boundaries_diagnostics.rs), [independent lattice derivation](/Maelstrom/tests/reference_lattice.rs) |
| M00-5: resolved inputs, construction, identity and compatibility | [Configuration](/Maelstrom/tests/configuration_contract.rs), [scenes](/Maelstrom/tests/scene_contract.rs), [external fixtures](/Maelstrom/tests/external_scenes.rs) and frozen-input hash checks |
| M00-2: determinism; empty state, cancellation and atomic failure | Repeated golden/library/CLI results; solver cancellation at every poll, late numerical failure and rejected final planes; [workflow failure and replay tests](/Maelstrom/tests/headless_workflow.rs) |
| M00-3: headless architecture | Inspected library dependency direction and solver source; complete tests and CLI execution require no rendering, threaded solver or CUDA |
| M00-4: correctness oracle | Independent equations, every-step health guards and fresh binary64 density audits qualify the golden; performance evidence remains Phase 7 |
| Diagnostics and public workflows | [CLI suite](/Maelstrom/tests/cli_workflow.rs): human/JSON workflows, statuses, invalid use, interruption, output safety and presentation invariance; [workflow suite](/Maelstrom/tests/headless_workflow.rs): fresh support, unavailable metrics and warning retention |
| Later-backend handoff | Self-contained golden inputs/outputs and the [exact matches, parallel tolerances and disagreement report](/docs/project/development/milestones/00/reference-verification.md#later-backend-comparison-policy) |

The primary falling golden passes the existing separation, compression and fixed energy screen at
every accepted step, reaches the floor and has no CFL warnings. Fresh binary64 audits agree within
`2e-6`; final mean/maximum absolute relative density errors are `0.09173302`/`0.20032573`.
These include free-surface deficiency and are diagnostic, not convergence-to-zero requirements.

A separate [family report](/Maelstrom/reference/family-review-v1.json) retains one public CLI run
of every size: all completed 480 steps with zero warnings or failures. It records hashes and checkpoint
diagnostics, not full trajectories or every-step health qualification for the larger sizes. Some results
lack an embedded build revision after verification rebuilds; their actual metadata is preserved and
production source remained unchanged. The two goldens retain their explicit generating revision.

## Limitations and Gate G05

G05 is satisfied locally for the recorded serial oracle and verification scope. This does not
complete M00-4's performance requirement, G06 or the milestone. Parallel tolerances are explicit
project acceptance budgets, not measured GPU accuracy; no later backend, cross-platform execution,
hosted CI or browser rendering was verified. Static-plane density deficiency, empirical artificial
pressure and sensitivity to precision remain numerical limitations.

The new tests, fixtures and records remain uncommitted. The assessed production solver is the full
commit identified above; the new verification tree has no completion commit yet. Matching
`milestone-00/phase-06/complete` annotated tags are intended at an authorised checkpoint. No tags,
branches, remote state or parent gitlink were changed by this work.
