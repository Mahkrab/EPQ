# Saved-image playback evidence

Local verification on 21 October 2026 extends the
[offline rendering record](/docs/project/development/milestones/04/phases/phase-02-offline-rendering.md).
It was collected from an uncommitted Maelstrom worktree based on
`52d7bffe3923e8d16477a7227c28245777fc4a34`. The final source is now committed as
[`9336ee42104badb1b5e439edc1df5e8488c32987`](https://github.com/Mahkrab/Maelstrom/tree/9336ee42104badb1b5e439edc1df5e8488c32987),
with matching inventory and production-content hashes. Collection-time provenance is unchanged;
the [checkpoint verification](/docs/project/development/milestones/04/assets/playback-v1/checkpoint-verification.json)
records checks on that clean committed tree. The earlier
[export evidence](/docs/project/development/milestones/04/assets/offline-v1/README.md)
retains its original source identity and results; it predates this player.

## Contract and environment

`play` loads completed PNG exports without physical-input resolution, numerical
execution or particle drawing. Tests use independently specified RGBA pixels and
timestamps, including an irregular final interval. A synthetic manifest deliberately
contains unusable physical inputs and an unavailable CUDA ordinal; its pixels still
load with a CPU-only build. Malformed schedules, unsafe names, symlinks, unsupported
versions, incomplete exports and missing/altered images fail without regeneration.

Graphics checks use local x86_64 Ubuntu 24.04.5 on WSL2, Rust/Cargo 1.98.1 and
explicit software Vulkan: llvmpipe LLVM 20.1.2, Mesa 25.2.8. The pixel test uploads
four independent colours, draws through the playback shader and reads back exact
top-left RGBA bytes, checking orientation and sRGB round-trip colour.

The native window harness uses WSLg Xwayland and sends events only to its own
process window. Ubuntu `libxcb-xkb1` 1.15-1ubuntu2 and `libxkbcommon-x11-0`
1.6.0-1build1 were downloaded and extracted into a temporary runtime, not installed
globally. Their package hashes match the
[existing native-library inventory](/docs/project/development/milestones/04/assets/viewer-v1/x11-native-context.json).
Inputs are the existing five-frame falling-block export and three-frame, 64-particle
saved CUDA export. Neither window journey is a new numerical run.

## Checks

[Commands and results](/docs/project/development/milestones/04/assets/playback-v1/checks.json)
record the 257 passing Rust tests (eight opt-in device checks skipped), the separately
run saved-pixel device test, 59 render-only tests, 32 headless CLI tests and 16 Python
tests. Formatting, warning-denying Clippy and the headless build check passed. The
[full viewer-suite log](/docs/project/development/milestones/04/assets/playback-v1/cargo-viewer.log)
and [source inventory](/docs/project/development/milestones/04/assets/playback-v1/source-manifest.json)
identify the assessed content. The inventory follows the exporter's component-sorted
source-content hash, covering the manifest/lock/build files and all Rust/native sources.

The [falling-block journey](/docs/project/development/milestones/04/assets/playback-v1/display/result.json)
and [saved-CUDA journey](/docs/project/development/milestones/04/assets/playback-v1/cuda-display-verified/result.json)
passed pause/resume, frame seeking, endpoints, restart, speed, resizing, final-frame
hold and close, with every input file unchanged. Screenshots are retained with each
result. The image's fixed camera and aspect-preserving resize are visible below.

![Saved falling-block image letterboxed in a square playback window](/docs/project/development/milestones/04/assets/playback-v1/display/resized.png)

Local checks do not establish hosted CI, hardware Vulkan, native Windows or macOS support.
These playback checks performed no benchmark or fresh CUDA execution. The separate
[primary-PC capture](/docs/project/development/milestones/04/assets/pc-export-v1/README.md)
records the subsequent CUDA export and laptop playback. Playback decodes on demand and
may skip displayed images when presentation falls behind; this is not a real-time
or fixed-FPS guarantee. Sparse stored observations remain sparse, not a reconstructed
smooth animation. Camera orbiting and video encoding are outside this workflow.

The first native attempt timed out waiting for its first Right-key seek: the title
remained on frame 1. Its Escape cleanup closed normally. The cause was not established;
it is retained as a failed attempt, not a pass. The next diagnostic run and subsequent
uninstrumented journey passed. No diagnostic key logging remains in the implementation.
An additional launch used the shared debug binary after a render-only build, which
correctly lacked `play`; its [stderr](/docs/project/development/milestones/04/assets/playback-v1/cuda-display/player.log)
is retained. Rebuilding with `viewer` restored the command before the successful
saved-CUDA journey. The final checkout binary includes playback; the installed
headless command was not replaced.
