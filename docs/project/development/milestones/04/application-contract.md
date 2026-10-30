# Application, observation and frame contract

This record owns the application behaviour agreed before graphics integration. The
[numerical contract](/docs/project/development/milestones/00/phases/phase-00-design-contract.md),
[comparison policy](/docs/project/development/milestones/00/reference-verification.md) and
[CUDA ownership handoff](/docs/project/development/milestones/03/cuda-gpu.md#application-integration-handoff)
continue to own the simulation. The controller, optional viewer and render-settings parser are
implemented. The offline exporter, publication and saved-image playback workflows are retained by
the [offline rendering checkpoint](/docs/project/development/milestones/04/phases/phase-02-offline-rendering.md). The
[viewer record](/docs/project/development/milestones/04/phases/phase-01-interactive-viewer.md)
separates assessed interaction, graphics and CUDA evidence.

## Journey and implementation boundary

The focused journey is: select a built-in or external scene, apply the existing configuration
precedence, validate it, explicitly select execution and a finite step count, start paused, then
inspect, single-step or run. Reset repeats the selected initial inputs at step zero. Apply changes
to inputs or backend by starting a new run; there is no live numerical editor. Offline output is a
separate finite operation with an explicit frame schedule and destination.

The viewer must offer scene/configuration selection, validation feedback, brute force, serial grid,
threaded grid with worker count, and optional CUDA with ordinal/block size. Controls are start,
pause/resume, single-step, reset, cancel/close, orbit/pan/zoom and fit camera. A failed input selection
must leave the existing selected run accessible. Resolve and validate draft inputs before submission;
if worker resource acquisition fails, show the new failure alongside the retained old outcome.
Do not present an old generation's particles as the new run's state.

Always show status, accepted/requested steps, simulated seconds, effective backend/resources,
particle count, cumulative CFL warnings and the latest CFL diagnostic. Show construction and
simulation failures explicitly. Density audits are requested observations outside solver work,
not a mandatory calculation on every redraw. Label redraw FPS separately from accepted steps/s;
any elapsed application, copy, audit, graphics or encoding measurements require separate boundaries.
The current controller records no performance measurements.

## Graphics choice and support target

Use winit for the main-thread window/events, wgpu for shared particle drawing to a surface or an
offscreen texture, and the `png` crate for image encoding. Official sources describe winit's event
role, wgpu's native graphics backends and PNG encoding respectively.<sup><a href="#ref-s054">S054</a>, <a href="#ref-s055">S055</a>, <a href="#ref-s056">S056</a></sup>
This is a project choice: sharing drawing between interactive and offscreen targets avoids two
renderers, while keeping window creation out of the exporter. Direct Vulkan would require a larger
resource/synchronisation boundary; an application/game engine would introduce scheduling and scene
ownership beyond this journey. The trade-off is shader compilation and a larger graphics dependency
graph than the headless library.

The initial qualification target is x86_64 Linux/WSL2 with WSLg for interaction and Vulkan for
graphics. A software Vulkan adapter may be selected explicitly for correctness checks and must be
identified as such. CUDA and graphics device selection are independent; CUDA access proves neither
surface nor offscreen rendering. Native Windows, macOS, browsers and other graphics backends are
not initially qualified even where the upstream libraries support them.

Plan separate opt-in Cargo features: `render` for wgpu/WGSL and PNG; `viewer` for `render` plus winit.
Keep default features empty and `cuda` independent. Start with the wgpu 30 and stable winit 0.30
families reviewed here; resolve compatible patch releases and retain their lockfile when implemented.
Enable Vulkan/std/WGSL and the required window-handle/X11/Wayland support deliberately, excluding
web, other graphics backends and optional image formats. Offscreen builds must not pull in winit.
The reviewed wgpu and PNG projects offer MIT/Apache-2.0 licensing; winit uses Apache-2.0. Retain
applicable notices and inspect transitive licences when adding the actual dependencies.<sup><a href="#ref-s054">S054</a>, <a href="#ref-s055">S055</a>, <a href="#ref-s056">S056</a></sup>
The implemented graph retains these feature boundaries; windowless PNG export is included in
`render`. The viewer adds a bitmap diagnostic font and uses winit's safe keyboard
loader to report missing native libraries before window creation. The locked Linux graph and
upstream notices were reviewed with the implementation; see the viewer evidence.

The initial lifecycle assessment on 20 October 2026 established no graphics support and could
not reach the PC. Subsequent viewer checks qualified local WSLg Wayland/X11 interaction and
software Vulkan drawing, then CUDA observations and independent graphics drawing on the PC.
These are separate evidence boundaries: an RTX 4070 CUDA check does not qualify hardware Vulkan
presentation. Current environments and negative results are retained in the
[viewer evidence](/docs/project/development/milestones/04/assets/viewer-v1/README.md).
The [offline output evidence](/docs/project/development/milestones/04/assets/offline-v1/README.md)
records the separate export qualification and its same-environment pixel checks.
The [primary-PC capture](/docs/project/development/milestones/04/assets/pc-export-v1/README.md)
adds a completed 8,000-particle CUDA export with software Vulkan and verified transfer to laptop
playback. It is not a hardware-graphics qualification or a new numerical reference comparison.

## Lifecycle and ownership

`application::Controller` starts an idle worker. Each admitted `RunSpec` owns resolved initial
inputs, discovery, execution, target step count and initial pause selection. Construction revalidates
the scene version and solver inputs on the worker. Its solver, private CPU pool and any CUDA context
are constructed, used and destroyed there. Only owned immutable observations cross the boundary;
no solver, context, stream or scratch buffer is shared or made `Send` through unsafe code.

| Current state | Request or event | Outcome |
| --- | --- | --- |
| Idle controller | Start | New generation queued; no snapshot yet |
| Queued | Worker admits request | Constructing; validation/resource acquisition |
| Constructing | Success | Initial accepted snapshot at zero; paused or running as requested; zero requested steps completes immediately |
| Constructing | Failure | Failed with construction diagnostic, no invented snapshot or effective device |
| Running | Pause | Paused at the next command boundary; an already executing step may finish |
| Paused | Resume | Running with the original fixed request |
| Paused | Single-step | Exactly one attempt; paused after acceptance, completed at target, cancelled or failed otherwise |
| Running | Target accepted | Completed, retaining final state, diagnostics and warnings |
| Any non-terminal run | Latched cancel or shutdown | Cancelled at a cooperative boundary, retaining the last accepted state if available |
| Running or stepping | Numerical/resource failure | Failed with diagnostic and last accepted snapshot; failed work is not published |
| Completed, cancelled or failed | Any numerical control | Explicit invalid-transition acknowledgement; outcome unchanged |
| Any selected run | Admitted restart | New generation from initial inputs; old non-terminal work cancelled and independently retained |

Pause while paused, resume while running and single-step while running are invalid. Controls target
the current handle from the same controller; other or superseded handles are rejected. Queueing is
not acknowledgement: a receipt reports the worker's actual transition. A pause receipt establishes
a stable step boundary; a resume receipt reports admission to running, which may already have
advanced by the time it is read. Single-step receipts report any terminal outcome too.

Generation counters increase only after successful queue admission and cannot wrap. Old handles
have independent observation slots. Restart cancels superseded queued construction and numerical
controls, so queued old commands cannot advance the replacement. A step already at acceptance may
finish before cancellation is observed; its observation remains attached to the old generation.
Changing display settings or retaining a snapshot cannot change any physical input identity.

## Transport, pacing and shutdown

The command queue holds at most eight requests, including queued starts. Full queues reject
immediately without cancelling or replacing the selected run; the caller can retry. Each request has
one independent, capacity-one acknowledgement. Dropping its receipt cannot block the worker.
Cancellation is a latched atomic flag and a best-effort wake; it never requires spare queue capacity.

Each run has one latest observation slot. Publishing replaces its previous observation and may skip
any number of intermediate display states. The observation includes an owned `Arc<Snapshot>`,
status, effective settings, cumulative warnings, latest CFL and a sticky terminal failure. Final
state/failure stay readable after teardown and restart through the old handle. Memory is bounded
per queue and per retained handle, not by particle-independent bytes: large inputs and snapshots
still cost memory, and callers explicitly retaining unlimited handles/snapshots can consume more.
No unbounded internal history, failure queue or display backlog is accumulated.

Running is **unpaced**. It executes all requested fixed timesteps as quickly as available resources
permit. Redraw cadence and clocks do not drive it. There is no wall-time accumulator, catch-up step
cap, timestep enlargement, numerical frame skipping or interpolation. Slow execution makes progress
slower; fast execution may finish ahead of display time. Pause adds no numerical work. Display may
redraw the last accepted state, labelled with its actual step and simulated time `step * fixed_dt`.
This deliberately makes no real-time playback guarantee. Tests use command barriers and controlled
consumer schedules; production pacing has no clock to mock.

Shutdown sets the global stop latch, wakes the worker and rejects further admission. The worker
finishes synchronous stages, cancels active/queued non-terminal work, resolves pending receipts and
drops its solver on the owning thread. The event loop calls `request_shutdown`, continues handling
events while polling `is_finished`, then joins. Blocking `join` and destructor fallback have no
deadline. A wait timeout is an observation timeout, never permission to abandon or duplicate a live
worker. Unexpected unwinding retains failure and accepted observations and causes join to report
worker failure; process abort, allocation abort and forced process termination cannot promise retention.

## Visual interpretation

Use the existing right-handed, positive-Y-up coordinates in metres, with no changes to source
positions. A particle is an opaque blue sphere centred on its accepted position with radius half
the configured particle spacing. Use instanced triangle geometry, depth testing, stable ascending
identity draw order, fixed directional lighting and no blending, random jitter, surface reconstruction,
temporal filtering or adaptive radius. Colour is a display choice, not a density or pressure claim.
Use background sRGB `#101820`, particle base `#2b9fd9` and boundary lines `#9aa8b0`; the renderer
revision fixes tessellation, lighting and shader details. Numerical correctness has independent tests.

The perspective camera uses eye, target and up vectors in world metres, vertical field of view in
degrees, aspect `width/height`, and explicit positive near/far distances. Look towards target with
screen-right `normalise(cross(forward, up))`, screen-up `cross(right, forward)`; map camera forward
distance to graphics depth `[0,1]`. Output origin is top-left, X right and Y down. Validate non-zero
view direction, non-parallel up and finite matrices; do not silently mirror or rotate output.

Default camera: eye `[1.2,1.0,1.2]`, target `[0.3,0.4,0.3]`, up `[0,1,0]`, vertical FOV 45°, near
0.001 m, far 100 m. Fit-camera is explicit, never repeated per frame: take the initial particle
axis-aligned bounds expanded by particle radius; for empty input use `[-0.5,0.5]` m on each axis.
Use their centre as target, bounding-sphere radius `r`, and eye direction `normalise([1,0.7,1])`.
Set distance `1.1*r/sin(min(vertical_half_fov,horizontal_half_fov))`, near `max(r/1000, 1e-6)` and
far `distance+10*r`. Record the resolved vectors/planes; export never depends on prior mouse input.
Reject a fit or projection that cannot be represented finitely rather than changing physical scale.

Depict each infinite constraint `dot(normal, position) >= offset` as the intersection of its plane
with a display box, drawn as an outline. That box is the initial particle bounds (empty fallback
above), expanded in every direction by `max(2*spacing, half its largest side)` and frozen for the run.
Label it as clipped plane depiction, not a physical solid extent or extra collision boundary.
This covers arbitrary planes and empty/single-particle inputs without inventing scene-owned walls.
Camera orbit/pan/zoom, clipping and fit are presentation operations only.

## Render settings and frame schedule

Render schema 1 is a separate strict TOML document. Unknown fields/versions and non-finite or
out-of-domain values fail before output creation. It never becomes part of numerical configuration
or scene identity. Precedence is built-in render defaults, one explicitly selected render file, then
explicit command-line render overrides; no implicit working-directory or home configuration. Physical
configuration continues to use its existing precedence independently.

| Field | Default and domain |
| --- | --- |
| `schema_version` | Required integer `1` |
| `width`, `height` | 1280, 720; integers 1–8192; checked RGBA byte size and actual adapter limits must also pass |
| `format` | `png`; only supported value, opaque RGBA8 sRGB |
| `step_stride` | 1; positive u64, sampling accepted indices only |
| `camera.eye_m`, `camera.target_m`, `camera.up` | Default vectors above; exactly three finite components each |
| `camera.vertical_fov_deg` | 45; strictly between 1 and 179 |
| `camera.near_m`, `camera.far_m` | 0.001, 100; finite, `0 < near < far` |

All fields except the version may be omitted and take their declared defaults. Camera overrides
merge field by field. Appearance, plane-box rule, tessellation, single-sample rendering (no MSAA),
no dithering and no overlays in exported images are fixed by renderer revision, not hidden settings.
Interactive diagnostics are a separate overlay. The graphics adapter/backend is an explicit launch
selection recorded in provenance, never inferred from the simulation execution enum.

For a complete run of `S` steps and stride `K`, the authoritative step list is the ordered unique
sequence `0, K, 2K, ... <= S`, followed by `S` if absent. Thus first frame is always initial state,
last is always the requested final state, and `S=0` produces one frame. Count is
`floor(S/K)+1+u64(S mod K != 0)`, checked for overflow and limited to 1,000,000 frames. Frame index
is zero-based, contiguous and independent of step value; filenames are `frame-00000000.png` through
`frame-00999999.png`. For `S=5, K=2`, indices 0–3 map to steps `[0,2,4,5]`. Image sequences have no
implicit playback FPS; simulated timestamps are `step * fixed_dt`. Fractional-step sampling,
interpolated or duplicated frames and wall-time schedules are rejected in this schema.

### Saved-image playback

`maelstrom play DIRECTORY` (or its `manifest.json`) must open completed rendered images without
resolving physical inputs, acquiring a solver or CUDA device, or drawing particles again. The
optional `viewer` build supplies its window. A copied sequence remains playable independently of
the original execution backend. Raw numerical results and incomplete progress files are not
playback inputs; missing snapshots cannot be invented to turn sparse observations into animation.

Default playback advances through recorded simulated timestamps at 1x, with an explicit finite
speed of 0.01–100 simulated seconds per wall-clock second. Support play/pause, recorded-frame
seeking, endpoints, restart, speed changes and optional repetition. Seeking pauses. The final image
remains visible; repetition holds it for the preceding interval, then restarts. A single image is
static. Late presentation may skip displayed images, never alter the saved sequence or interpolate
new states. Show the selected frame, step, timestamp, speed and play/pause status.

Preserve image aspect ratio on resize. The exported camera is fixed; orbiting requires a new
render, not a numerical rerun when the required observations are available. Validate completion,
schema, schedule, finite ordered timestamps and exact frame filenames before opening. Check PNG
and decoded-pixel hashes and dimensions on image load; missing/corrupt images fail explicitly with
no fallback computation or writes. Bound manifests to 64 MiB, encoded frames to 300 MiB and image
dimensions to 8192 per side. Decode on demand into bounded frame storage and reuse one image texture.

### Lossless export ownership

The controller's coalesced slot is **not** the export source for a rerun. A dedicated driver owns
the solver and graphics, advances every step, and renders each scheduled accepted snapshot.
One CPU encoding/hash job may overlap later solver work and preparation/readback of the next image.
The driver collects and publishes the preceding frame before submitting the next CPU job; the
initial image is published before stepping. Cancellation joins outstanding CPU work and leaves it
unpublished. The [compilation pipeline assessment](/docs/project/development/milestones/05/performance-render-pipeline.md)
records this authorised replacement of the original fully synchronous frame boundary; it changes
no numerical or frame-sampling policy. Export
backpressure may delay completion but never discard a scheduled frame or alter numerical work.
Simulation setup/stepping and graphics/readback/encoding must have separate timing boundaries.

Saved-observation mode validates the result schema, portable inputs and finite, ordered checkpoint
data. Use explicitly stored checkpoints and the final snapshot, de-duplicating equal step indices
only if their complete particle bits agree. Every scheduled index must exist; otherwise reject before
publication and report missing indices. Do not interpolate or silently run missing work. Initial
inputs alone are not a stored accepted checkpoint. Cancellation/failed records remain partial:
rendering their available prefix requires explicitly selecting that prefix's last step as `S`, and
the manifest retains original requested/completed counts, status and failures.

Rerun-recorded-input mode is separately selected. It uses replay's validated initial inputs, full
original request and effective execution, starts at zero and compares every available source
checkpoint with the newly accepted state under the existing comparison policy. It is neither
resumption nor certification of recorded outcomes; mismatches fail the operation and remain evidence.
No automatic mode switching or backend fallback is allowed.

## Paths, publication and reproducibility

Input paths explicitly selected on the command line resolve against the invocation directory;
existing scene-selected configuration paths keep their scene-relative rule. The render file has no
input/output path fields. Output directory is a required launch argument, resolved against invocation
directory and recorded as a portable user-facing label, not an absolute personal path. Frames and
manifest entries use fixed basenames and cannot contain traversal or externally supplied filenames.

Use exclusive creation of a new destination directory; reject an existing destination, file or
symlink without modifying it. Preflight schema, schedule and saved-observation availability first.
Write `progress.json` with `complete=false`, then each PNG to an exclusively created temporary name,
close it and publish the fixed final basename without replacement using the existing safe-output
approach. Update progress only after successful publication. Do not delete user data or automatically
resume partial directories. Cancellation/encoding/readback/disk failure leaves published frames and
an explicit incomplete outcome; retain both earlier and output failures where reporting permits.
A crash may leave stale progress or temporary files, which never establish completion.

Publish `manifest.json` last and without replacement, after every expected image has been closed,
hashed and its frame entry recorded. Its schema version is 1. It contains `complete=true`, source
mode (saved/rerun/direct), application version, source commit when available and dirty/source-content
identity, build/target context, full recorded physical inputs and their existing identities, original
request/status/failures where relevant, effective discovery/execution/CUDA device, accepted count,
frame count, stride and full frame-to-step mapping with simulated seconds and SHA-256 image hashes.
Also retain resolved render schema/settings, camera, boundary display box, renderer/shader identity,
graphics API/adapter/device/driver where available, texture format and encoder version/settings.
Record unavailable provenance as unavailable; do not invent a clean source revision. Personal input
paths are not reproducibility identities.

Simulation reproducibility means preserving the identified physical request and applicable backend
comparison policy; transport must preserve every bit of the accepted observations it does deliver.
Frame reproducibility means identical schedule, endpoints, names and resolved settings from the same
inputs. Image reproducibility initially guarantees **no cross-device or cross-driver pixel equality**.
The exporter must establish repeatable decoded RGBA pixels for the same binary, adapter/driver,
resolved settings and source observations in its qualified environment, retain PNG hashes, and test
that guarantee before claiming export support. Compression metadata/bytes may differ across encoder
versions. Pixel differences elsewhere are graphics evidence to investigate, not permission to loosen
solver acceptance. A useful picture does not prove fluid-model accuracy.

## References used

- <a name="ref-s054"></a> **S054 — gfx-rs developers (n.d.).** *wgpu: repository documentation and feature metadata*. [Source record](/docs/research/sources/054-wgpu-rendering-boundary.md).
- <a name="ref-s055"></a> **S055 — winit contributors (n.d.).** *winit: window creation and management*, v0.30.12. [Source record](/docs/research/sources/055-winit-window-events.md).
- <a name="ref-s056"></a> **S056 — image-rs contributors (n.d.).** *PNG Decoder/Encoder*. [Source record](/docs/research/sources/056-image-rs-png-encoding.md).
