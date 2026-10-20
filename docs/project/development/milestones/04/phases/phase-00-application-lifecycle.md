# Phase 0 application contracts and lifecycle

## Starting point

Work began from clean EPQ `162ad8b0070c65103f912bb56970216166a96e5e` and Maelstrom
[`afb8ffbf6482d7d70fe01d03d6c32ce2277ad96b`](https://github.com/Mahkrab/Maelstrom/tree/afb8ffbf6482d7d70fe01d03d6c32ce2277ad96b).
The existing `milestone-04/phase-00/start` annotated checkpoints identify those commits in their
respective histories. The simulator already exposed transactional stepping, accepted snapshots and
explicit CPU/CUDA execution, but had no presentation controller or application/frame contract.

## Scope and outcome

The new non-visual application controller owns a simulation worker and supports construction,
running, pause, single-step, restart, completion, cancellation, failure and teardown. The
[application contract](/docs/project/development/milestones/04/application-contract.md) defines the
focused user journey, graphics/feature choice, pacing, visual interpretation, versioned settings,
offline frame mapping, provenance and publication. A viewer and exporter are not implemented here.

The assessed implementation is now committed as Maelstrom
[`423ac5c6cd0a1939eea9225cad8d7dda2197c0c2`](https://github.com/Mahkrab/Maelstrom/tree/423ac5c6cd0a1939eea9225cad8d7dda2197c0c2).
All 105 hashes in the retained
[source manifest](/docs/project/development/milestones/04/assets/lifecycle-v1/source-manifest.json)
match that commit. Existing numerical code, defaults, goldens, replay schemas and Cargo dependencies
are unchanged. Original evidence retains its working-tree provenance; the parent gitlink now pins
the assessed implementation for the local completion checkpoint.

## Decisions and implementation

### Worker ownership and restart isolation

The CUDA handoff requires constructing, using and destroying the solver on its owning thread.
The controller therefore sends owned initial inputs to a worker rather than moving a constructed
solver across threads. Each run publishes immutable owned snapshots into its own observation slot.
Old handles retain their outcome after restart; stale commands and cancellation cannot overwrite
the replacement's accepted observations. Setup failure has its own outcome while the previous
handle remains readable.

Commands have eight slots and one independent acknowledgement per admitted request. A full queue
rejects admission without replacing the selected run. The display observation coalesces, while final
state, cumulative warnings and failures remain retained. Cancellation uses a separate latched flag
and wake, so it works with a full queue. Final review identified a possible admission after panic
cleanup had drained the queue; admission and worker exit are now synchronised before draining.

These responsibilities live in the [application module](https://github.com/Mahkrab/Maelstrom/tree/423ac5c6cd0a1939eea9225cad8d7dda2197c0c2/src/application); the
[library guide](https://github.com/Mahkrab/Maelstrom/blob/423ac5c6cd0a1939eea9225cad8d7dda2197c0c2/docs/application.md) explains receipts, retained handles and shutdown.
There is no unsafe thread-sharing or new solver scheduling inside numerical stages.

### Pacing and offline observations

Running advances all requested fixed timesteps without wall-time pacing or interpolation. This
keeps display cadence out of numerical work and makes no real-time playback promise. Pause takes
effect at a command boundary; single-step attempts exactly one timestep while paused. The trade-off
is that a fast run may finish before a display consumes its intermediate states.

Consequently, the coalesced display slot cannot feed reproducible offline output. The contract
specifies a separate synchronous, lossless export boundary, accepted-step sampling with explicit
initial/final frames, and rejection of missing saved observations. Saved-state rendering and
rerunning recorded inputs are distinct modes. Render settings and camera state have their own
schema and cannot change physical input identity. The graphics choice and its source appraisal are
recorded in the contract rather than adding unused graphics dependencies now.

## Verification

Local verification uses x86_64 Ubuntu/WSL2 with Rust/Cargo 1.98.1. The
[retained evidence](/docs/project/development/milestones/04/assets/lifecycle-v1/README.md) records
commands, exits, environment, transcripts and assessed source hashes. Verification includes exact
particle-bit comparisons with direct brute-force, serial-grid and threaded-grid execution, a
hand-calculated particle trajectory, controlled consumer schedules, queued stale commands,
full-queue cancellation, failure retention and worker-panic cleanup. No sleep interval establishes
control ordering; acknowledgements and barriers do. With unpaced execution there is no production
pacing clock to mock.

The final release suite passed **223 checks**, including 15 new controller checks. It ran without
display variables and with deliberately unusable CUDA/compiler paths. Formatting, strict Clippy and
warning-free Rustdoc passed. Local Markdown parsing and link/anchor resolution passed; no hosted or
browser-rendered documentation check was performed.

## Limitations and Gate G00

**G00 is satisfied for the non-visual lifecycle and agreed application/frame contracts.** The implemented boundary has no
graphics resources, window or PNG output. Local display socket paths are not graphics qualification.
Two PC SSH probes timed out; the explicit CUDA worker test is supplied but fresh CUDA-enabled
compilation and device execution remain unverified in this environment. Existing CUDA hardware
evidence is historical and does not establish this new worker test passed.

Annotated `milestone-04/phase-00/complete` tags identify the subsequently authorised local completion
checkpoints in both histories, with the exact implementation pinned by EPQ's gitlink. The original
checks and source manifest are unchanged. Remote publication and hosted verification remain separate.
