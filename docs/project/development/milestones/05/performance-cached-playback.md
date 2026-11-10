# Cached playback and video hardware qualification

**Retain real-time cached playback as the default, with frame-accurate inspection selectable.**
The workflow is ready for routine use on the qualified Ryzen 9 7900X / RTX 4070 WSL2 system,
subject to the storage, display and encoder-memory limits below. Large cached observations can be
watched at recorded speed, inspected, reframed and exported without constructing a fluid solver.
This is application qualification, not a numerical or live-simulation throughput claim.

The [evidence receipt](/docs/project/development/milestones/05/assets/cached-playback-v1/README.md)
links source identities, individual measurements, original traces and rejected collection attempts.
The [user guide](/Maelstrom/docs/video.md) owns commands and controls; the
[cache implementation record](/docs/project/development/milestones/05/performance-cache-pipeline.md)
owns the existing storage/rendering boundary. No history, gitlink, installed binary, driver, clock,
power setting, dependency, numerical expression, CUDA source or cache format was changed.

## Workloads and measurement boundaries

Release builds with locked dependencies ran on the primary PC through `ssh pc` on 10 November 2026:
Ryzen 9 7900X, RTX 4070, driver 610.88, Rust 1.96.0, CUDA 13.3.73, WSL2 and native WSLg Xwayland.
Graphics selected hardware OpenGL through Mesa D3D12, not software Vulkan. The WSL memory allocation
was approximately 15.2 GiB. CPU encoder tests used FFmpeg 6.1.1/libx264 from Ubuntu packages extracted
inside the experiment directory; wrappers changed only the launched encoder's library search path.

| Cache | Accepted solver timestep | Sampling | Observations | Nominal recorded duration |
| --- | --- | --- | ---: | ---: |
| Existing falling block, 8,000 particles | binary32 1/240 s | stride 4, approximately 60 Hz | 301 | 5 s |
| New block, 32,000 particles | binary32 1/480 s | stride 4, approximately 120 Hz | 601 | 5 s |
| Existing large impact, 110,592 particles | binary32 1/240 s | stride 4, approximately 60 Hz | 301 | 5 s |

The middle cache used the current large-impact package's configuration and a `[40,20,40]` lattice.
Its single bake took **9.44 s**, outside all viewing/export measurements. Its denser observation
schedule is intentional retained evidence, not a matched temporal workload across particle counts.
Compare controls/candidates within each cache; do not attribute cross-row differences solely to N.
Full independent canonical validation passed all **1,203 observations** across the three caches.

Each playback case had two alternating control/candidate pairs, an initial second excluded, then
eight seconds measured, at both 1280×720 and 1920×1080, at 1× and 4×: 48 complete samples.
The control is the actual starting implementation with the same opt-in trace instrumentation.
Reads were repeated with the OS cache warm; no cache flush or cold-storage claim is made.
The trace distinguishes completed validated frame loads, client submissions, displayed source time
and CPU preparation/upload/submission. Load rates include read-ahead which may never be presented.
They are not SSD bandwidth or simulation throughput. Source-time progress includes skipped states
but excludes terminal hold time, so a correct looping 4× run measures slightly below 4.000×.

## Playback results and retained timing correction

Normal-speed candidate results below use the median of the two run rates/CPU samples. Pacing and
RSS show the worse per-run p95/p99/high-water mark, without pooling distributions.

| Particles | Drawable size | Loaded states/s | Client submissions/s | Recorded s/wall s | Interval p95 / p99, ms | CPU core equivalents | Peak RSS, MiB |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 8,000 | 1280×720 | 60.1 | 175.0 | 0.9967 | 6.45 / 7.11 | 0.35 | 190.9 |
| 8,000 | 1920×1080 | 60.1 | 94.0 | 0.9972 | 12.96 / 14.15 | 0.30 | 196.0 |
| 32,000 | 1280×720 | 120.0 | 177.8 | 0.9988 | 6.48 / 6.85 | 0.54 | 201.9 |
| 32,000 | 1920×1080 | 120.0 | 83.6 | 0.9985 | 15.45 / 16.69 | 0.42 | 207.9 |
| 110,592 | 1280×720 | 60.1 | 99.7 | 0.9982 | 10.77 / 11.84 | 0.59 | 223.1 |
| 110,592 | 1920×1080 | 60.1 | 76.5 | 0.9976 | 13.94 / 15.20 | 0.58 | 227.6 |

These are **client submissions**, not compositor acknowledgements or physical display FPS. The
starting overlay's claimed 60 Hz display target was misleading: the event loop/surface can submit
more frequently. The overlay now says presentation follows the surface. One CPU core equivalent
means one logical CPU busy throughout the measurement, not utilisation of the whole 24-thread PC.

| Particles | Size | Control at requested 1× | Control at requested 4× | Candidate at requested 4× |
| ---: | --- | ---: | ---: | ---: |
| 8,000 | 720p | 0.9954× | 2.8791× | 3.9849× |
| 8,000 | 1080p | 0.9947× | 1.5947× | 3.9840× |
| 32,000 | 720p | 0.9976× | 1.2438× | 3.9915× |
| 32,000 | 1080p | 0.6812× | 0.6895× | 3.9891× |
| 110,592 | 720p | 0.9970× | 1.6144× | 3.9856× |
| 110,592 | 1080p | 0.9965× | 1.2549× | 3.9859× |

The old wait-for-every-state policy fails even normal speed for the 120 Hz cache at 1080p. The
correction follows monotonic elapsed time and recorded timestamps, requesting the most recent state
at or before the target. It may skip **presentations**, never cache data. Time continues through
ordinary disk stalls while the last available observation remains interactive. One completed read
is retained even when its target has been superseded; otherwise a moving target could perpetually
discard slower reads. Exact seeks and stepping still require the requested state.

`--cache-playback frame-accurate` or T retains sequential inspection, accepting slower playback;
the 1080p large-cache trace presented every successive index without skipping. Explicit seek/start
waits anchor the clock on arrival. Pause preserves fractional time, speed changes settle the old
multiplier first, and loop/end handling uses the final recorded gap. Unit tests cover these rules,
irregular endpoints, reverse/exact seeks and a same-frame seek which must clear its pending anchor.

The final clean build repeated large 1080p at **0.9970× / 3.9843×**, with 15.12 / 15.41 ms p99
intervals. A separate untraced 4× run measured **3.9889×**, using title observations rather than
submission counts. This supports retention of the timing correction without claiming faster GPU work.

## Rendering, input and memory

An isolated diagnostic build bracketed the unchanged scene/overlay commands with GPU timestamp
queries. Synchronous query readback serialises work; these results are not ordinary viewer rates.
Median indexed GPU draw milliseconds at 720p / 1080p were **0.772 / 0.844** for 8,000,
**1.590 / 1.540** for 32,000, and **4.818 / 4.848** for 110,592. The large 1080p p95 was 5.026 ms.
CPU preparation/upload/submission and presentation backpressure remain separate costs.

Warm per-frame file/receipt read p95 was at most **0.14 / 0.23 / 0.58 ms** across the respective
counts. Complete read/validation/decode/conversion p95 was at most **0.59 / 1.45 / 4.47 ms**.
These intervals include the cache reader's declared work, not raw device latency.

Final hardware X11/XTest journeys exercised keyboard and left-drag orbit, right-drag pan, wheel and
key zoom while paused, running normally and running at 4×, plus alternating scrub targets, exact
reverse/end/beginning transitions, timing-policy changes, resize, arbitrary frame entry and saving.
Handled keyboard events reached a client submission in about 8–11 ms, including during injected
disk delay. The preload fixture delayed each particle-file read call by 100 ms; complete frame reads
took hundreds of milliseconds while camera updates continued. Normal closes took about 0.11 s;
closing during a delayed outstanding read took about 0.42 s. Permanent I/O hangs remain a limit
because shutdown joins the current read.

At matching 640×480 dimensions and source frame 17, the final saved-camera indexed viewer capture
and independent PNG agreed in **all 160,000 compared pixels** in the scene rectangle outside the
controls. This is same-stack indexed evidence. It does not equate impostor/mesh representations,
different aspect ratios, cross-driver pixels or lossy video with PNGs.

The large 1080p, 4×, **120-second soak** loaded 18,509 frames including setup. Sampled process RSS
was flat at **228.195 MiB**; there was no duration-dependent growth in this run. It submitted 76.44/s,
presented 75.64 new states/s and advanced at 3.9868×. P95/p99 intervals were 14.31/15.21 ms, CPU
use 0.90 core equivalents, and validated loads approximately 152.6/s. Whole-device memory samples
plateaued around 1,873 MiB; they include the desktop and cannot establish private GPU allocation.
The configured 128 MiB read-ahead/workspace budget is not an RSS limit. Frozen inputs, graphics,
metadata and encoder buffers remain separate. Repeated seeking and six partial-cache open/close
cycles completed; missing/corrupt frames failed, and incomplete viewing required `--allow-partial`.

## MP4 export

These are complete process wall seconds for **301 selected observations at 60 FPS**, including
startup, validation, rendering or image decode, encoding, publication and teardown. They are single
observations per case. The middle cache explicitly selects `--every 2`; the other caches select all
frames. PNG production is excluded from `video images`, and was measured separately.

| Particles | Size | `video cache`, s (frames/s) | `video images`, s (frames/s) |
| ---: | --- | ---: | ---: |
| 8,000 | 640×480 | 1.667 (180.6) | 0.815 (369.2) |
| 8,000 | 1280×720 | 2.419 (124.4) | 0.967 (311.4) |
| 8,000 | 1920×1080 | 4.176 (72.1) | 1.519 (198.1) |
| 32,000 | 640×480 | 2.274 (132.4) | 0.859 (350.3) |
| 32,000 | 1280×720 | 2.783 (108.2) | 1.115 (269.9) |
| 32,000 | 1920×1080 | 4.307 (69.9) | 1.572 (191.5) |
| 110,592 | 640×480 | 3.973 (75.8) | 0.966 (311.7) |
| 110,592 | 1280×720 | 4.674 (64.4) | 1.267 (237.5) |
| 110,592 | 1920×1080 | 5.835 (51.6) | 1.973 (152.6) |

The original full 601-state middle-cache exports are retained separately: at 1080p they took
7.637/2.724 s and intentionally produce **10.016667 s at 60 FPS**. CFR video uses selection ordinal,
not automatic physical-time resampling. A cache's sampling cadence must inform the explicit FPS
and selection. The normal 301-frame outputs last 5.016667 s; explicit endpoint omission yielded
300 frames/5 s. Inclusive sparse `[17,31]` with increment 4 yielded `[17,21,25,29]`, never an appended
31; omission yielded `[17,21,25]`. Sparse image-bundle ordinals retain original times separately.

FFprobe decoded all representative outputs as H.264/yuv420p with the expected resolution, count,
ordered CFR timestamps and duration. Independently invoked FFmpeg, fed prepared raw frames and
explicit selected PNGs, matched both application's decoded outputs for the full large 301-frame
sequence and four-frame sparse selection. SHA-256 receipts bind published MP4s and source manifests;
sidecars retain source identity, selection, original times, presentation and encoder provenance.

The independent warm raw-input CPU FFmpeg pipeline, including scaling/libx264/muxing, took
0.607/1.011/1.571 s for 301 frames at 480p/720p/1080p: approximately 496/298/192 frames/s. This
excludes raw preparation but includes raw input I/O and uses 50 ms process sampling. It is not pure
codec service time. A separate 61-frame synchronous GPU diagnostic measured median large-cache draws
of 5.021/4.662/4.323 ms and mean complete frame-production intervals of 12.63/14.46/17.12 ms. Those
diagnostic costs overlap encoding and must not be added to the ordinary complete-process table.

At large 1080p, separately sampled application/FFmpeg RSS peaks were **205.8/1,221.0 MiB** for cache
video and **13.6/1,233.4 MiB** for image conversion. These are individual process peaks, not a summed
resident-memory guarantee. The original runs consumed approximately 3.9/13.1 CPU core equivalents
including encoder children. Default libx264 buffering/threading had a substantial separate encoder
resource budget; it was practical in the available WSL allocation. No NVENC/hardware encoding or
video speedup is claimed. Missing FFmpeg/libx264, encoder failure and corruption prevented output;
real encoding cancellation returned 130, reaped its child and removed staging in 0.032 s.

## Verification and disposition

The final primary-PC build passed **382 ordinary tests**, the three normally ignored cache graphics
checks and the real-FFmpeg check: **386 distinct tests**, with 67 unrelated opt-ins unrun. Strict
all-feature/all-target release Clippy passed. Local headless/render-only checks, viewer library/CLI
tests, all cache workflow tests, formatting and focused parent assessor tests also passed. Existing
schema-1/schema-2 bundles, exact cache validation and unchanged native PTX remain compatible.

Retain the timing policy, bounded completed-read fallback, exact seek anchoring, explicit partial
viewer option, option validation, truthful overlay, tests, documentation and opt-in diagnostics.
Retain the existing camera, indexed/impostor distinction, graphics owner, one reader and FFmpeg
pipeline. No evidence justified another reader/GPU worker, particle interpolation, a new buffer
architecture, mesh/shader changes, encoder options or numerical work.

Collection failures are retained: a partial trace line required a collector correction; synthetic
core pointer messages were replaced with XTest for winit's XI2 route. A final shared-target Cargo
build reused the GPU probe executable. Its test receipt was rejected, the application package was
cleaned/rebuilt, and embedded source/PTX identities were checked for **every measured binary**.
The corrected final build received fresh tests, camera journeys and traced/untraced playback checks.

This qualification covers warm local WSL storage and scripted input on the named graphics stack.
Human desktop feel, physical scan-out, cold/concurrent storage pressure, permanent storage/device
failure, indefinite filesystem shutdown, other operating systems, longer encoding soaks and power-loss
durability remain outside the evidence. These limits do not prevent routine cached inspection and
MP4 export on the measured PC; they prevent broader portability or failure-proof claims.
