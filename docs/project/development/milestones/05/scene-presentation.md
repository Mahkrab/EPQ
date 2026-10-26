# Persistent camera and particle colours

## Scope and starting point

This records the presentation work in Phase 02, following the
[scene-usability plan](/docs/project/development/milestones/05/scene-usability-plan.md) and
[settings contract](/docs/project/development/milestones/05/scene-settings-contract.md).
It extends the uncommitted settings and scene-authoring work on `phase/05-02-scene-usability`.
The committed Maelstrom baseline remains
[`4a9675b5f9e3b7aa90335f5a77bdb3e82093a1b5`](https://github.com/Mahkrab/Maelstrom/tree/4a9675b5f9e3b7aa90335f5a77bdb3e82093a1b5),
with EPQ at `812dea60d8527b8ed977c6bd5d865199397aa374`. These commits do not contain this implementation;
the working files and their tests are the review evidence until a separate checkpoint is authorised.

## Camera behaviour

Viewing and compilation now fit a finite plane-bounded domain before considering particle bounds.
This keeps the whole container visible when the fluid initially occupies only one corner.
The presentation calculation intersects the inward half-spaces in f64 and checks for unbounded
directions. Empty or unbounded geometry falls back to particle bounds, then the built-in fixed camera.
Plane outlines use the same finite domain. Physical planes and particle coordinates are unchanged.

F refits the displayed accepted state, using the current window aspect ratio; the finite domain still
takes precedence. Home restores the loaded or fitted pose, or the last successfully saved pose for
that generation. Resizing changes projection without repositioning the camera. Reset restarts the
selected simulation while keeping the current view. Explicit fit/no-fit flags retain their precedence.

S saves the current camera to the displayed editable scene's `render.toml`, independently of unapplied
draft edits. It writes fixed mode and the complete camera, preserving other values and comments.
`--camera-output FILE` selects another destination; `--render-config` remains input selection only.
Bundled scenes require an editable copy. Moving the camera and temporary launch flags never save it.

The saver captures an absolute destination for the selected generation and runs on a separate worker.
It validates the document, writes and flushes a staged file beside the target, checks for detected
concurrent edits, then publishes atomically. Symlinks and read-only targets fail; absent targets use
no-clobber publication. Existing permissions are retained. This is an optimistic edit check, not a
filesystem compare-and-swap or a guarantee against arbitrary concurrent writers or power loss.

Lossless editing uses optional, viewer-only `toml_edit` with parse/display features. Its exact version
was already in the lockfile; no package version changed. This avoids rebuilding the whole document
and losing unrelated comments. Independent preservation tests caught and corrected key-comment loss.

## Colours and compatibility

Render schema 2 supports custom fixed sRGB colours and a blue-to-red kinetic-energy gradient.
Energy is `½m|v|²` in joules, from accepted velocity and resolved physical particle mass. Calculation
uses f64 before uploading one clamped fraction per particle. Saved finite bounds remain fixed across
frames: blue at or below the minimum, red at or above the maximum, with linear-RGB interpolation
before lighting and sRGB encoding. This represents motion, not temperature or a material property.

The shared drawing pass serves both live viewing and offline compilation. Default fixed `#2b9fd9`
retains the original rounded linear colour constants. Normalised manifest render settings use schema 2
for custom or energy colours; default-colour records retain schema 1. The enclosing image-bundle
format remains schema 1. Existing image-only compilations remain playable without recomputing physics.
Changing their camera or colours still requires new rendering from particle observations.

Implementation responsibilities are split between `src/presentation/`, the shared render pass,
the viewer's selected-generation model and the export frame writer. Presentation resolution is
repeated on apply without sending visual settings into the solver. Headless execution ignores them.
The native journey also found a stale controller guard that rejected scene schema 2 before step zero;
it now accepts both supported versions and still rejects unknown versions. No numerical stage changed.

## Verification

Checks ran locally on x86-64 WSL2 with Rust 1.98.1. Software graphics used Vulkan llvmpipe,
Mesa 25.2.8, LLVM 20.1.2. The following checks concern functionality, not performance measurements. The full viewer-enabled
suite passed 309 tests across 33 targets, with 14 explicitly ignored device checks. After the
controller correction, the library and CLI unit suites passed 48 tests, with three device checks ignored.
Eighteen selected headless tests also passed. Strict Clippy passed with and without viewer features;
render-only compilation and strict Rustdoc generation passed. The ten lifecycle integration checks
also passed after the controller correction. Three parent Markdown tests, 51 local link destinations
and the final formatting/whitespace review passed; no hosted Markdown rendering was checked.

| Check | Observed result |
| --- | --- |
| Independent colour cases | Exact energy endpoints, midpoint, clamping, mass scaling, extreme accepted f32 values, custom sRGB conversion and invalid inputs passed |
| Camera geometry | Known box and tetrahedron bounds, unbounded/empty/infeasible domains, portrait/landscape projection and failed-fit preservation passed |
| Camera publication | Legacy upgrade, new files, inline/dotted tables, comments, permissions, symlinks, invalid data, injected failure and concurrent-edit rejection passed |
| Viewer model and CLI | Save target selection, unapplied drafts, camera restore/reset, rejected settings and unchanged accepted particles passed |
| Controller regression | Both supported scene versions constructed and stepped; unsupported versions failed explicitly |
| Software drawing and compilation | Blue/red/midpoint/custom-colour pixel probes passed; palette changes preserved observation hashes; both compiled palettes validated |
| Existing offline checks | Four export integration checks passed, including orientation, depth, cancellation and retained failure evidence |
| Native X11 journey | Editable two-block scene opened paused; orbit/save/Home/refit/close and reuse of saved camera/palette by compilation passed |

The first native attempt reported missing `libxkbcommon-x11-0` and `libxcb-xkb1`. The successful
test used Ubuntu packages 1.6.0-1build1 and 1.15-1ubuntu2 extracted temporarily for the existing
X11 harness; no system installation changed. The intermediate schema rejection remains a recorded
failure, followed by the controller regression and successful repeat. The final screenshot showed
both blocks and the complete box. Native hardware graphics, Wayland, CUDA and the primary PC were
not requalified here, and no new performance claim is made.

Local command logs use `/tmp/maelstrom-presentation-*.log`, including retained failed attempts.
They are transient verification output, not immutable historical endpoints or hosted checks.

## Outcome and limits

Camera persistence and colour rendering are implemented locally. The maintained viewer, input and
compilation guides explain their controls and version behaviour. Saved particle-frame archives,
fluid-effect implementation and final end-to-end qualification remain separate work. No commit,
tag, push, branch change or EPQ gitlink update is included.
