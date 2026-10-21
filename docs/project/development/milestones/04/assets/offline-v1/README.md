# Offline output evidence

This inventory retains the initial exporter assessment and source identities. The subsequent
[saved-playback checks](/docs/project/development/milestones/04/assets/playback-v1/README.md)
extend the viewing journey; they do not replace the historical results below.
The final implementation is checkpointed in the linked phase record. The earlier exporter-only
build was not separately committed: its recorded content identity remains the evidence boundary,
while the final commit also includes playback. The separate
[primary-PC capture](/docs/project/development/milestones/04/assets/pc-export-v1/README.md)
records subsequent fresh CUDA execution; the original checks below did not exercise it.

Local evidence collected on 21 October 2026 for the
[offline rendering record](/docs/project/development/milestones/04/phases/phase-02-offline-rendering.md).
The [application contract](/docs/project/development/milestones/04/application-contract.md) owns
acceptance. **G02 is satisfied within the qualification below.** These files assess an uncommitted
Maelstrom worktree based on `52d7bffe3923e8d16477a7227c28245777fc4a34`; no completion commit/tag,
remote result or new parent gitlink is implied.

The [requirement audit](/docs/project/development/milestones/04/assets/offline-v1/completion-audit.json)
maps all seven planned work items to current evidence and verifies retained manifests against source.

## Environment and source

[Environment](/docs/project/development/milestones/04/assets/offline-v1/environment.json) records
WSL2 x86_64 Ubuntu, Rust/Cargo and both starting commits. Device checks used Vulkan with llvmpipe,
Mesa 25.2.8 and LLVM 20.1.2. DISPLAY and WAYLAND_DISPLAY were removed; CUDA_HOME and CXX pointed
to unavailable locations for the recorded Cargo checks. No window, toolkit or CUDA device was
required. This qualifies software Vulkan export separately from the headless solver.

The [source inventory](/docs/project/development/milestones/04/assets/offline-v1/source-manifest.json)
retains individual source/test/document hashes and the compiled production-content identity. Every
retained export's build identity matches that content. Hash construction sorts relative path components,
then hashes path, NUL, little-endian u64 byte length and contents for Cargo.toml, Cargo.lock, build.rs
and every src/native file. The independent audit initially used flat string ordering; correcting it
to Rust's component ordering resolved that verifier disagreement without a source change.

The [licence inventory](/docs/project/development/milestones/04/assets/offline-v1/dependency-licences.json)
and retained upstream notices cover the added PNG graph. Metadata includes optional lockfile packages;
[cargo-tree-render.txt](/docs/project/development/milestones/04/assets/offline-v1/cargo-tree-render.txt)
records activated normal/build dependencies. It contains no winit. The
[headless graph](/docs/project/development/milestones/04/assets/offline-v1/cargo-tree-headless.txt)
contains no wgpu, winit, pollster or PNG. PNG 0.18.1 is pinned; default features remain empty.

## Commands and checks

[checks.json](/docs/project/development/milestones/04/assets/offline-v1/checks.json) retains exact
Cargo arguments, working-directory labels and exits. Each label has a corresponding `.log` here.

| Check | Observed result and boundary |
| --- | --- |
| `headless` | Full CPU-only suite: 223 passed, including doctests |
| `viewer-regression` | Full viewer suite: 246 passed, six device checks explicitly ignored at collection; graphics cases were run separately |
| `final-export` | 25 passed: library boundaries, saved/schedule/CLI contracts and all four export-device journeys; no ignored tests in this invocation |
| `publication-regression` | 20 headless workflow tests passed after shared output staging was changed to close files before publication |
| `readback`, `geometry` | Explicit software Vulkan readback/device destruction and independent orientation, depth, empty-image and immutable-input checks passed |
| `device-final` | All four export journeys passed, including inspection of retained comparison-disagreement evidence |
| `clippy-clean`, `format`, `rustdoc`, `render-build` | Strict Clippy for all viewer targets, formatting, warning-free Rustdoc and windowless render build passed |

The full regressions preceded final publication/failure-boundary refinements; the final targeted
checks cover those changes. Later test-only edits applied Clippy's array-chunk idiom and asserted
the disagreement report contents. Logs labelled `clippy` and `clippy-final` retain failed strict
lint attempts; the final code factors the encoder function type and uses the required array-chunk
idiom. An early CLI help invocation also exposed Clap's prohibition on required global arguments;
output presence is now validated as an ordinary usage error, and the CLI test exercises it.

Known geometry passes through the exporter and an independent PNG decoder: asymmetric points test
orientation, projected sphere radius tests metre scale, a nearer sphere occludes a later far sphere,
and empty input produces only opaque background. Width 127 exercises padded GPU rows. Direct,
saved and rerun modes produce identical decoded pixels for the same observations/settings across
independently constructed graphics contexts. Every sampled snapshot hash matches direct headless
execution, including the existing refined 480-step falling block and a two-worker request.

Failure checks retain earlier closed images with no completion manifest: cancellation, an existing
next-frame file, progress staging failure, existing manifest, checkpoint disagreement, resource
destruction and invalid PNG input after the first frame. The latter two run through the same sequence
recovery path as real frame stages. A forced process kill after initial publication leaves an
explicitly incomplete directory. A second failure to record progress is reported with the first;
stale progress after interruption never establishes completion. Existing files and symlinks survive.

## Retained sequences and reconstruction

[examples.json](/docs/project/development/milestones/04/assets/offline-v1/examples.json) records
successful CLI invocations. Its temporary input/output placeholders are labelled explicitly.

| Directory | Source and accepted steps |
| --- | --- |
| `small-direct` | Fresh 27-particle lattice, steps 0, 2, 4, 5 |
| `small-saved` | Stored lattice golden, steps 0, 12; no new simulation |
| `falling-rerun` | Fresh rerun of the existing 64-particle, 480-step refined golden; steps 0, 120, 240, 360, 480, checking stored step 1 too |
| `cuda-saved` | Historical PC CUDA observations, steps 0, 240, 480; CPU-only exporter, no new CUDA execution |
| `falling-wide` | The same falling-block rerun with an explicit wider camera, covering the whole fall |

Every directory retains its PNGs, incomplete progress file and final completion manifest. The
[artifact audit](/docs/project/development/milestones/04/assets/offline-v1/artifact-audit.json)
checks 19 PNGs using independent standard-library PNG chunk CRC, DEFLATE and filter reconstruction,
then verifies dimensions, opacity and decoded-pixel/encoded-image hashes. Schedule endpoints,
ordering and fixed names are checked alongside the manifests. Historical CUDA snapshots and pixels
match the fresh serial rerun exactly at the selected shared steps. The
[CUDA source identity](/docs/project/development/milestones/04/assets/offline-v1/cuda-saved-source.json)
links the unchanged compressed result and records compressed/decompressed hashes.

The [round trip](/docs/project/development/milestones/04/assets/offline-v1/round-trip.json) starts a
new numerical replay from `small-direct/manifest.json`, retains its ordinary result in
`small-reconstructed-result.json`, then renders that result as saved observations into a temporary
new directory. All four frame entries, observation hashes, PNG bytes and decoded-pixel hashes agree.
The source-content, input and graphics identities agree too. This exercises reconstruction rather
than merely inspecting metadata keys.

Visual inspection found that fitting only the initial block leaves the late falling motion mostly
outside the view in `falling-rerun`. That sequence is retained as a camera limitation. The explicit
[wide-camera settings](/docs/project/development/milestones/04/assets/offline-v1/wide-camera.toml)
resolve the display choice without changing the physical request or following particles each frame.

![Final accepted falling-block state with the explicit wider fixed camera](/docs/project/development/milestones/04/assets/offline-v1/falling-wide/frame-00000004.png)

## Limits

These are local correctness and reproducibility checks, with no performance or hosted-verification
claim. Same-environment decoded pixel repeatability is established; cross-device/driver equality is
not promised. Fresh CUDA execution/export and hardware Vulkan export were not exercised. Native
Windows, macOS, browsers and other graphics APIs remain unqualified. Deliberate device destruction
checks error handling, not a physical GPU fault or a hung driver. Synchronous work has no cancellation
deadline. Hard-link publication is non-clobbering, without a filesystem crash-durability guarantee.
