# Phase 2 offline rendering and output

## Starting point

Work began with clean EPQ `82d0da33869e6056be65c761a98c8ca4ca351761` and Maelstrom
[`52d7bffe3923e8d16477a7227c28245777fc4a34`](https://github.com/Mahkrab/Maelstrom/tree/52d7bffe3923e8d16477a7227c28245777fc4a34).
The viewer already shared its particle/plane pass with offscreen targets. There was no
sequence exporter, saved-observation loader or PNG encoder. The
[application contract](/docs/project/development/milestones/04/application-contract.md)
owns the sampling, appearance, provenance and publication requirements.

## Scope and outcome

The optional `render` build now exports PNG sequences without creating a window. Explicit
sources select saved observations, a full recorded-input rerun, or a fresh scene run. Sampling
uses accepted step indices with initial/final endpoints. Missing saved states fail before
output creation. A failed source needs an explicitly selected prefix, whose original outcome
remains visible in the completion manifest.
The optional viewer build also plays those saved images without repeating numerical work
or drawing the particles again. Exporting alone had left that viewing journey unfinished.

The implementation is committed as Maelstrom
[`9336ee42104badb1b5e439edc1df5e8488c32987`](https://github.com/Mahkrab/Maelstrom/tree/9336ee42104badb1b5e439edc1df5e8488c32987).
EPQ's gitlink pins that implementation. The [export evidence](/docs/project/development/milestones/04/assets/offline-v1/README.md)
retains its original exporter-only collection context; playback and the PC capture match the final
committed production-content hash. Earlier uncommitted build identities have not been rewritten.

## Decisions and implementation

### Preserve every selected observation through a synchronous boundary

The viewer's latest-observation slot deliberately coalesces display updates, so it cannot supply
a lossless sequence. A dedicated driver owns the solver and completes one selected frame's draw,
readback, PNG encoding and publication before advancing. This gives capacity-one backpressure
without adding another worker, queue or CUDA ownership transfer. Every numerical step still runs;
output delay changes elapsed completion time only. Accepted diagnostics and frame metadata remain
in memory, without accumulating particle history. Solver stepping, graphics/readback and encoding
have separate timing fields, which are diagnostics rather than benchmark claims.

Saved loading reuses replay's portable physical-input and backend validation, then checks finite,
ordered snapshots, request/count consistency and exact duplicate-final bits. It never constructs
the recorded CUDA device. Rerun mode retains the complete original request and resources and
compares every stored checkpoint/final snapshot. Serial comparisons include signed zero; parallel
comparisons retain the existing position/velocity budgets. Disagreement retains the expected and
actual observations in a separate failure report. It does not certify the original disposition.

### Treat the manifest as the completion boundary

Exclusive directory creation rejects existing files, directories and symlinks. Shared safe-output
publication now closes each synced temporary file before publishing its hard link. Each frame
records PNG, decoded-pixel and accepted-observation hashes. Progress is always explicitly
incomplete; the final manifest is published without replacement only after all expected images.
Failure retains closed frames, original source failures and the current export failure. A second
failure to write progress is reported alongside the first. Interrupted directories are retained
without automatic cleanup or resume.

The manifest records full portable inputs, numerical identities/resources, schedule/timestamps,
resolved presentation, camera/display box, compiled-source and lock hashes, build context and
independent graphics/encoder provenance. Its numerical fields can be passed to the existing replay
loader to reconstruct the sampled observations. PNG 0.18.1 is pinned and enabled only with `render`;
its graph and upstream notices are retained. Offscreen builds introduce no winit dependency.

### Make the saved output watchable

`maelstrom play` reads a completed sequence rather than a scene or numerical result. It follows
recorded simulated timestamps, with pause, frame seeking, speed changes and optional repetition.
The final image stays visible; resizing preserves aspect ratio. Its camera is already rendered
into the images. PNG and pixel hashes are checked on demand, using bounded frame storage and one
reused texture. Invalid or missing images fail without writes or fallback computation. Sparse
historical checkpoints remain sparse; a complete animation needs those states captured once.

## Verification

The evidence inventory records the completed regression, device, failure and reconstruction checks.
Software Vulkan tests independently decode PNGs, compare their pixels across direct/saved/rerun
exports and compare every observation hash against direct headless execution. They include the
small lattice, the existing refined 480-step falling block, zero-step empty input, a single particle
and a two-worker request. A command-line manifest/replay/export round trip preserves observation
and image hashes. Saved historical CUDA observations also match fresh serial bits at the sampled
steps without constructing CUDA. Known geometry checks orientation, scale, depth and row padding through
the complete exported-image path. Failure checks cover malformed/sparse/partial histories,
non-clobbering output, cancellation, publication/progress errors, device loss, encoding failure,
comparison mismatch and process termination after initial publication.
The separate [playback evidence](/docs/project/development/milestones/04/assets/playback-v1/README.md)
checks timing and input failures independently, reads back known saved colours through the image
shader, and exercises a real window's controls, resize and close. Sequence hashes remain unchanged.
The [primary-PC capture](/docs/project/development/milestones/04/assets/pc-export-v1/README.md) completed
8,000 particles and 480 CUDA steps with zero CFL warnings, producing 481 images. All image hashes
and the completion-manifest hash survived transfer to laptop playback. This was not a benchmark
or a new independent numerical comparison. The final
[committed-tree checks](/docs/project/development/milestones/04/assets/playback-v1/checkpoint-verification.json)
passed all 265 tests, including the eight software-Vulkan checks, with none ignored.

## Limitations and Gate G02

**G02 is satisfied for the implemented workflow within the recorded qualification boundary.**
Final command results and retained sequences are recorded with the evidence inventory. Qualification
is limited to x86_64 WSL2 Linux, WSLg interaction, llvmpipe software Vulkan and the recorded RTX 4070
capture. Hardware Vulkan export remains unqualified. No cross-driver pixel equality, shutdown
deadline, crash durability or automatic recovery is claimed. Application evaluation and the final
research comparison remain subsequent work.

Annotated `milestone-04/phase-02/complete` tags retain the authorised local checkpoints in both
histories. Remote publication and hosted verification remain separate and were not performed.
