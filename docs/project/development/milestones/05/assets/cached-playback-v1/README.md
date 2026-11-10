# Cached playback and video evidence

The [qualification assessment](/docs/project/development/milestones/05/performance-cached-playback.md)
owns the interpretation. This receipt identifies original observations and their boundaries; it is
not a solver-performance, physical display FPS, cross-platform or hardware-encoder qualification.

## Source and binary identity

All application exports started from the actual dirty Maelstrom tree based on
`6bf2682325b7665e48f8a8647ce087d48ff13f0b`. The commit alone does not identify these builds.
[Initial source](initial-source.json), initial Git statuses and the tracked/untracked source patches
retain the starting state, including the pre-existing CUDA, cache and video work.
[Binary identities](source-binary-identity.json) independently repeat build.rs's source digest and
check its presence in each executable. Every admitted executable embeds the same PTX:
`cf4a83d08b2db15e1576a975759b41844d853b2b52e69235890cc254dce45b8b`.

| Export | Role | Executable SHA-256 |
| --- | --- | --- |
| control | Starting timing policy plus opt-in tracing | `f8a2ec9df5b175eb84f48c30e010b6e9f2851660dd964599f95af82f812bd52d` |
| candidate | Alternating timing comparison | `cb8c796c63dddbde14154d14e7a5326bfb540c9c4de4d0a8b66426e5bcfad189` |
| delivery | Soak, first camera journeys and main video matrix | `3e69f3cdb20c98fcd9a0fbb032577a93aa80fd22502d696336623289d4783271` |
| gpu-probe | Synchronous GPU timestamp diagnostic only | `f7c4ae406273fd105a12a747b3e386fecff878315f22f78ba161fe56ee54e4d5` |
| final | Final tests, viewer/camera checks and supplementary exports | `3fd6cc67556500d8ec382c543edb7ed3079fbb3856d5541494f177bfa1371e52` |

The initial tracked patch plus `initial-untracked-source.patch` reconstruct the starting sources.
`initial-to-control.patch`, `control-to-candidate.patch`, `candidate-to-delivery.patch`,
`delivery-to-final.patch` and `candidate-to-gpu-probe.patch` retain the exact compilation-input
deltas. `qualification-changes.patch` records the complete local delivery change from the initial
working files, including tests and documentation. Build hashes cover Cargo files, build.rs, source,
native code, build support, scenes and configuration; documentation edits after measurement do not
alter the embedded source identity. No source directories, binaries, caches or image bundles are
copied into this evidence directory.

The final shared-target build initially reused the GPU probe. `stale-artifact-build.log` and
`pc-stale-artifact-tests.log` are rejected evidence. No performance result from that executable is
admitted as final. The package was cleaned in the isolated target directory, rebuilt and checked
against the expected embedded source/PTX before further tests and final measurements. The
[identity checker](/tools/performance/cached_identity.py) now makes this an explicit admission check.

## Measurement and reproduction

[Environment](environment.json) records fresh primary-PC CPU, graphics, compiler, memory and storage
observations. Native WSLg Xwayland selected Mesa D3D12 OpenGL on the RTX 4070. Both window sizes
are actual drawable dimensions in the client traces. FFmpeg came from download-only Ubuntu packages
extracted under the experiment directory. No package installation or system graphics change occurred.

The complete retained experiment remains on the primary PC at
`~/.local/share/maelstrom-experiments/cached-playback-v1`, with source exports, separate copied
executables, generated MP4s/PNGs and the one new 32,000-particle cache. Existing 8,000/110,592 caches
remain under the earlier `cache-pipeline-v1/runs/` experiment. The source, request and result
identities in these receipts identify them independently of those convenience paths.

Reusable collectors live in [tools/performance](/tools/performance/):

- `cached_playback.py` and `cached_campaign.py`: paired windows, raw submissions, source-time progress,
  resources and original timing protocol. Run as Python modules from the tooling root.
- `cached_journey.py`: targeted X11 keys plus server-routed XTest pointer gestures, resize, exact
  inspection, presentation saving and process-owned window closure.
- `delay_cache_reads.c`: opt-in process-local read delay; the source cache stays unchanged.
- `cached_gpu_probe.py`: patches a disposable source export to request timestamps and synchronously
  read them. Drawing expressions remain unchanged; throughput must not be pooled with ordinary runs.
- `cached_video_campaign.py`, `cached_post.py`, `cached_faults.py`, `cached_verify.py`: video/export,
  independent FFmpeg/FFprobe, lifecycle, identity and final qualification work.

The individual `protocol.json` and `process.json` files retain exact command arrays. Release builds
used `cargo build --release --locked --features viewer,cuda`. Use a distinct application target or
clean the isolated package when switching source exports, then check embedded identity. The scripts
do not install FFmpeg, change clocks or publish to Git. New output directories are required.

The new cache has 601 observations at approximately 120 Hz, reflecting the existing 480 Hz scene
configuration and stride 4. Its bake took 9.44 seconds and is setup only. The other caches have
301 observations at approximately 60 Hz. This matters for both timing and CFR video. The main
32,000 video matrix preserves all 601 frames; the separately labelled `video-60hz-*` cases select
`--every 2 --fps 60`. They do not rebake, invent states or change the source cache.

## Receipts

- [Raw evidence archive](raw-evidence.tar.gz): original viewer/read traces, 50 ms process samples,
  200 ms whole-device samples, protocols, process clocks, GNU time records, FFprobe decoded-frame
  metadata, encoder provenance, camera journeys, failure results and test/build logs. It excludes
  source directories, package payloads, caches, raw RGBA and published image/video bytes.
- [Playback summary](playback-final-summary.json): recomputed from those original traces. Two
  alternating pairs per workload/size/speed remain separate. The 120-second soak and final traced/
  untraced runs are separate records inside the archive.
- [Video matrix](video-summary.json) and [301-frame middle-cache selection](video-60hz-32000-summary.json):
  complete-process observations, with frame counts/durations and independent stream checks.
- [GPU diagnostics](gpu-summary.json): scene/overlay GPU intervals and separate 61-frame cached-video
  diagnostic CPU intervals; query readback overhead is not an ordinary viewer result.
- [Output integrity](artifact-integrity.json): MP4 byte hashes and source PNG-manifest hashes/settings,
  separating retained full outputs on the PC from the smaller repository receipt.
- [Independent decode](independent-decode.json): both application paths match a separately invoked
  encoder for all 301 large frames and explicit sparse indices `[17,21,25,29]`.
- [Final camera comparison](final-camera-pixel-comparison.json), [saved camera](camera.toml) and
  [viewer capture](viewer.png): exact indexed agreement for 160,000 scene pixels outside the controls.
- `pc-final-tests.log`, `pc-final-cache-workflow.log`, `pc-final-video.log`, `pc-final-clippy.log`:
  382 ordinary tests, three additional cache graphics opt-ins and one additional real-encoder opt-in;
  386 distinct tests passed. Sixty-seven unrelated specialised opt-ins remain unrun.

The source-memory budget is not process RSS. The large 120-second playback RSS stayed at
228.195 MiB. Supplementary 1080p video sampling distinguishes the approximately 206 MiB application
peak from the approximately 1.2 GiB libx264 process peak. GNU time's family high-water mark must not
be presented as an additive simultaneous memory peak. FFmpeg-only timings include warm raw input,
scaling and muxing, but exclude raw preparation. Video process sampling has up to 50 ms completion
granularity; playback pacing comes from client timestamps, not that polling cadence.

Rejected collector records remain in the archive: `collector-failed-partial-log` and
`journey-core-pointer-rejected`. A reader of a live log must defer its incomplete final line;
malformed completed lines still fail. Winit's XI2 route ignored synthetic core pointer messages,
so XTest supplied server-routed pointer input confined to the launched window. This establishes
scripted input handling, not human subjective feel or physical scan-out.

The final file seal records digests for this receipt's files. Original cache/image/video payloads
remain on the primary PC and can be checked against their request/result/manifest/MP4 identities.
Cold reads, other desktops/operating systems, permanent device/storage failure, indefinite shutdown,
longer encoding soaks and power-loss durability are explicitly outside qualification.
