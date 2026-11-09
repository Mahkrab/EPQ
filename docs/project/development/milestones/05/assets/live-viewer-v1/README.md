# Live viewer evidence receipt

Collected on the primary PC on 9 November 2026. The [assessment](/docs/project/development/milestones/05/performance-live-viewer.md)
owns the engineering decision; [results](results.md) and [comparison.json](comparison.json)
expose the measurements. This is hardware OpenGL/D3D12 through a native X11 window,
not software Vulkan, offline compilation, compositor acknowledgement or physical scan-out.
Desktop-visible FPS and native keyboard/mouse latency remain unqualified.

## Identity and reconstruction

Starting local Maelstrom HEAD: `c40fc627549ad34120a39a1103218192a2b4b6b4`.
Starting EPQ HEAD: `15a8162e9943a1ad3801c76f86dee47fea5b7d9e`.
Existing user changes selecting the experimental default were included in the control.
Neither repository history nor the parent gitlink changed. The PC checkout was older
and was preserved; all experiment sources and executables are isolated under
`/tmp/maelstrom-live-Yp09cX` on `ssh pc`. The installed CLI was not replaced.
Builds reused the PC's dependency cache; its ignored `target/release/maelstrom`
artifact now contains the assessed final build rather than the older checkout's build.

| Variant | Source SHA-256 | Executable SHA-256 |
| --- | --- | --- |
| Instrumented control | `55b542732557b07dff09a5a50d5b4e82ea1e9a551b4db407933f9c1fc64429e2` | `fefeb9019e400cc516ca30ef1ce8430e6f7f2e9f38621d7c91f90538566b7416` |
| Indexed | `1f633d185ca24eff858b22b5c00b22417e20277dc36709fb5f93ce0f6c239c89` | `ac3a5d7ad18745d9210c78da2c55aa38cf9b419e69b5c91e11cbc5ed53975d6f` |
| Rejected buffer reuse | `d9351216ee581759f2f2a52f1d135c2f2c46b3982c3ec61f46131e11b825e917` | `046718cc905508bf9d72bc0d37fcaadc4df4231667edf4a8a05a092d78019b87` |
| Final, including profile-error precedence and panel wording | `a87fd0b192632023a9520dc6fd3ac4073b12c41081b2c1a20e1b9a2140f64c15` | `dc83eb70744be25f6230b04136c620e2cecafe10c19099f9aaa2501b83b9349c` |

`identities.json` and `final-identity.json` list every hashed production source/input
file. The source hash uses the build script's path-component ordering and includes
path, NUL, little-endian byte length and file bytes. Each digest was found in its
actual executable. Control/indexed and indexed/buffer variants differ only in
`src/render/gpu.rs`. The final follow-up changes the viewer error/reporting boundary.

`control-from-head.patch` reconstructs the control's production sources from the
starting Maelstrom HEAD, including the pre-existing default changes and profiling.
`indexed-from-control.patch`, `rejected-buffer-reuse.patch` and
`final-viewer-follow-up.patch` identify subsequent changes. These patches are source
evidence, not repository checkpoints. Maintained tests and collectors remain in their
owning repositories rather than being copied into this evidence folder.

All thirteen native files agree. `ptx-identities.json` verifies a fresh precise
compute_89 PTX build, including its NUL terminator, in all four executables:
`2bb95233ef4e5aa5d7f328a3e93715855f8d7dea026c053acc1be8ba666d6203`
(218,499 bytes). Query-build identities are separately recorded in `probe-identities.json`.
No executable, PTX build product or repository copy is stored here.

## Campaigns and timer boundaries

- `indexed-<count>-p<0..3>-<variant>/`: indexed versus control, 24 invocations.
  Pair 0 warms each variant; pairs 1–3 are the 18 measured invocations, in BA/AB/BA order.
- `buffers-<count>-p<0..3>-<variant>/`: independent indexed versus persistent-buffer
  comparison, with the same 24-invocation design. It was rejected and is not pooled
  into the indexed result.
- Each invocation contains `frames.csv`, 200 ms `gpu.csv`, `viewer.log` and a
  `summary.json`. All 36 measured invocations reached exactly 1,200 accepted steps.
- `inputs/` fixes particle count, geometry, spacing, container and camera. Required
  counts are exactly 8,000, 32,000 and 110,592. The explicit experimental selector
  overrides the saved reference schedule in the external scene configuration.
- `capacity-final-*` brackets five-second averages. `capacity-extended-*` and
  `capacity-headroom-*` use 4,800 steps, nominally 20 simulated seconds.
  `capacity-summary.json` includes the lowest full one-second window for each run.
  The first `capacity-48000-*` series overlapped a CPU pixel audit and is exploratory.
- `headless/` retains three fresh no-render controls, their complete process timings
  and compressed full result records. Solver totals exclude construction, output and
  teardown. These test the new graphics-contention hypothesis; they do not revise
  historical solver baselines.
- `trace-*/` retains first-240-step Nsight CUDA/GL reports and CUDA API/kernel/copy
  tables. `gpu-timestamps-*` are separate, synchronising GPU draw profiles with
  `gpu-draw-summary.json`. Their FPS and throughput must not enter ordinary comparisons.
- `final-smoke-*` verifies the final error-priority/caption follow-up at all required
  counts. Its results agree with the retained behaviour but are not extra paired samples.

Presentation rate is successful surface presents divided by monotonic running wall
time. Quantiles use nearest rank. Simulated time comes from accepted index times
the unchanged binary32 timestep. Setup/terminal frames are excluded; the first
observed index varies because simulation starts before graphics setup completes.
Whole-device telemetry includes setup and other Windows activity; it is not process
occupancy. CPU core equivalents come from process user+system counters over the
observed running interval. GPU clock or power changes were never forced.
CPU stages, GPU durations and worker work overlap; adding them would double-count time.

To recompute comparisons from this repository, run:

```sh
python3 -m tools.performance.live_report docs/project/development/milestones/05/assets/live-viewer-v1
python3 -m unittest tests.performance.test_live_viewer
```

The collector starts a **fresh simulation**, waits for its fixed accepted-step limit
and closes only its own window with `WM_DELETE_WINDOW`. On the PC, one invocation is:

```sh
python3 /tmp/maelstrom-live-Yp09cX/live_viewer.py \
  /tmp/maelstrom-live-Yp09cX/final \
  /tmp/maelstrom-live-Yp09cX/inputs/32000.toml \
  /tmp/maelstrom-live-Yp09cX/new-observation --steps 1200
```

The output directory must be new. The command is a fresh run, not playback or resumption.

## Equality, regressions and native checks

`pixel-checks/*.json` retains all 27 image/state digest records for each variant:
three particle counts, steps 0/240/1,200 and three cameras. The manifests are exactly
equal. `pixel-comparison.json` records zero changed pixels and maximum channel delta
zero in all 54 indexed/rejected comparisons. Raw RGBA witnesses remain in the PC
experiment's `pixels-*` directories. The maintained hardware harness is
[viewer_pixels.rs](/Maelstrom/tests/viewer_pixels.rs); its logs are retained here.

`native-check/` contains actual client captures before/after resizing, paused and
running, and clean-close receipts. Capturing pixels perturbs presentation; screenshot
FPS labels are not performance samples. Native keyboard/mouse/camera latency, physical
display visibility and physical device loss/reset were not qualified.

PC release verification: 354 normally selected tests passed; 60 opt-in/hardware tests
were initially ignored. Explicit runs passed 35 CUDA library tests, 12 viewer-model
tests, ten application lifecycle tests, ten CUDA boundary/execution integration tests
and four device-rendering tests. The pixel harness also passed in each source variant.
`final-clippy.log` and `final-format.log` establish strict CUDA/viewer checks.
`local-viewer-suite.log` retains 352 passing CPU/viewer tests; focused lifecycle
verification and ten Python measurement/focus checks also passed.
`validation.json` records source/PTX/image/work-count checks. `tool-identities.json`
identifies the final maintained collectors and verification harnesses.

## Failures and limits retained

The first paused pilot could not obtain focus. The next successful small pilot used
reference settings because external scenes default to their saved configuration; it
is excluded. The large paused pilot required a later external focus attempt and its
complete elapsed time includes that idle period. Subsequent paused indexed pilots
never received the key; partial logs/files are retained. No failed pilot is a paired
performance sample. Core focus, XTest and XInput diagnostics were bounded; the session
contained LogonUI and native host frames were off the X root display. No unlock,
driver/security/power change or software-performance substitution was made.

The initial pixel-test compile used unsupported hexadecimal formatting for the current
SHA-256 result type; the retained `buffer-pixels-attempt.log` precedes the correction.
Strict Clippy later caught an ignored `StepOutcome` in that new test; the corrected
explicit discard passed, and `final-clippy-initial.log` retains the failure.
An initially reused timestamp executable was detected by identity checks before any
query samples; touching the copied source forced the correct rebuild. Both query
executables' embedded source identities were then checked. The requested
`opengl_api_sum` report does not exist in this Nsight version; raw OpenGL API events
remain in the report and graphics GPU timing comes from timestamp queries instead.

No hardware counter, cache/bandwidth/occupancy attribution, desktop FPS or universal
particle-capacity claim follows from these observations. The measured sustained
capacity applies to this scene family, device and 20-second horizon. The old
residency investigation, numerical formulations and offline-encoding investigations
were not rerun or changed.
