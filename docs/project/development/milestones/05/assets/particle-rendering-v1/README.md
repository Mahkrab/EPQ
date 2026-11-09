# Particle rendering evidence

The engineering decision is recorded in
[GPU particle rendering](/docs/project/development/milestones/05/performance-particle-rendering.md).
This family preserves a hardware viewer campaign, separate GPU timestamp profiles,
matched visual witnesses, exact accepted-step capacity traces and regression logs.
The earlier `live-viewer-v1` family is unchanged.

**Absolute capacity is machine-state dependent.** The original campaign qualified
38,400, but the later resumed session qualified only 28,800 under the same strict
every-one-second rule. The renderer gain replicated in both sessions. Read the
[post-resume results](/docs/project/development/milestones/05/assets/particle-rendering-v1/post-resume/README.md)
alongside the original tables; do not treat the earlier faster state as a guarantee.

## Provenance and measurement boundaries

Measurements were collected on 9 November 2026 through `ssh pc`: Ryzen 9 7900X,
RTX 4070, WSL2, Windows NVIDIA driver 610.88, Mesa 25.2.8 D3D12/OpenGL, Rust 1.96.0,
CUDA 13.3.73. Viewer logs identify the actual hardware adapter and sRGB surface.
The benign DRI3 warning alone does not establish software rendering; adapter selection
is checked independently. Software Vulkan appears only in an explicit correctness
test and never in performance samples. No driver, clock, power or OS setting changed.

Parent HEAD was `15a8162e9943a1ad3801c76f86dee47fea5b7d9e`, Maelstrom HEAD
`c40fc627549ad34120a39a1103218192a2b4b6b4`; both had existing uncommitted work.
The PC checkout stayed clean at `f170e9c952c815e2a9e87158c4932bb42ddb465b`.
Source was copied into isolated directories, with the ignored PC target cache reused.
No commit, push, branch, tag, gitlink, installed CLI or repository-history change occurred.

`identity.json` and `identities.json` record comparison and diagnostic production-file
digests and executable identities. The ordinary four-mode comparison binary was
`f0ba66175c522b964218c738c63d9f1f4aeba239ef9a5f30dbb3c42ec61d1a28`, with embedded
source identity `f27fac335d5bd44b84b7d4fd7cd852b7cf6e663aa792e48412601208393f5d75`.
`final-accepted-identity.json` identifies the final live-default/acceptance-trace binary:
`967a6b53d1ed055f1d01d5ba36f35047a893064e3a09f312b5e334a3ae3ecacd`, source
`c39ac6562e15f6542f7f7271ba6c82ea88708c7e3968456c081a53b2e952667a`.
Its only production changes after comparison are default/environment validation in
`viewer/mod.rs` and opt-in accepted-step timestamps in `application/worker.rs`.
All native CUDA sources match. The final embedded NUL-terminated PTX is exactly
218,499 bytes, SHA-256 `2bb95233ef4e5aa5d7f328a3e93715855f8d7dea026c053acc1be8ba666d6203`,
matching the earlier indexed implementation. No numerical kernel was changed.

The original temporary PC directory `/tmp/maelstrom-particles-Co3l9z` disappeared
between sessions. All ordinary/profile/capacity traces and processed visuals had
already been copied here. The final executable survived in the target cache with
its exact recorded digest. Final verification restored the source to
`/home/oliver/.cache/maelstrom-particle-final-20261109/source`, preserved that binary
as `retained-final`, and recreated lost regression logs. This recovery did not rerun
the candidate campaign or replace its samples.

`protocol.md` preserves the planned workloads and the later capacity-method detail.
`low-*`, `impostor-*`, `adaptive-*` contain 72 invocations: warm-up pair zero plus
three measured alternating pairs per candidate/count (54 measured invocations).
Each has frame CSV, GPU telemetry, viewer log and command/summary. Every run computes
all 1,200 required steps. `comparison.json` retains all paired effects and ranges.
`results.md` contains the full indexed/impostor tables and candidate comparisons.

Frame metrics use successful client-window presentations during the running portion.
Simulation rate comes independently from accepted indices and the unchanged f32
240 Hz timestep. Startup/terminal frames are excluded from ordinary running statistics;
complete launch/completion wall time is also retained. These CPU clocks establish
neither compositor acknowledgement nor physical scan-out FPS. WSLg desktop visibility,
native keyboard/camera delivery and input latency remain unqualified.

`gpu-*` are twelve separate timestamp-query/readback runs. The final terminal draw
is excluded from their component means; all raw timestamps remain. Synchronisation
changes contention, so their throughput must not enter the ordinary comparison.
`gpu-draw-summary.json` includes sample counts, submitted triangles and mesh levels.
Draw intervals include clear, particles, boundary lines, overlay and possible GPU
preemption. CPU graphics stages and solver waits overlap them; do not add these as
exclusive times. Whole-device telemetry is not process occupancy or an exclusive
particle-memory allocation measurement. No unavailable performance counter is inferred.

## Visual evidence

Open [the local gallery](/docs/project/development/milestones/05/assets/particle-rendering-v1/visuals/index.html)
in a browser for the image divider and three labelled four-way videos. It needs no
server, external assets or network. `visuals/stills` holds 144 PNGs, covering twelve
matched views at each count for all four renderers. `visual-metrics.md` and
`visuals/comparison.json` quantify changed pixels, foreground/full-frame RGB error,
maximum channel error and PSNR. Alternative renderers are not pixel-equivalent.

The CUDA harness advanced one trajectory per count and rendered each immutable state
through all four representations: 300 state/camera groups and 1,200 original rendered
images, with state and raw RGBA digests in `visuals/images.json`. The retained stills
decode to those exact raw RGBA hashes. The three MP4s sample 91 states at 30 Hz,
steps 0–720 at stride eight, with identical orbit/zoom, plus separate stills at step
1,200. Every simulation timestep was computed. Encoded video cadence is a visual
comparison and does not measure interactive wall-time performance. Original PNG
motion frames were transient inputs; the manifest, selected exact PNGs and encoded
videos are retained rather than duplicating that entire derived corpus.

`legacy-indexed-check.json` records eighteen exact indexed-pixel and accepted-state
matches with the prior viewer corpus. The analytic overlap/depth tests use independent
f64 ray intersections, with off-axis silhouette and near/inside-sphere indexed fallback
checks on both hardware GL and explicit software Vulkan. Close stills show fewer
facets for impostors than low meshes; normal-distance matched motion remains readable.
The evidence covers these scenes/cameras, not all possible fine spray, transparency
or fluid surface reconstruction. The renderer is opaque throughout.

## Capacity and regression evidence

`capacity-exact-*` contains three complete 4,800-step runs at 35,200, 38,400 and
40,000. `accepted.csv` records every successful solver completion in monotonic
nanoseconds. The initial zero starts after construction; timestamping happens before
the observation copy, and CSV writing happens after the run. All intermediate
solver/observation time remains in subsequent intervals. `capacity.json` evaluates
every full one-second interval, including intervals between displayed observations.
The step-count function changes only at an acceptance or one second before one;
checking those boundaries and neighbouring nanoseconds covers the continuous interval.
The independent reader rejects missing steps, invalid ordering and incomplete traces.
At least 240 complete steps must occur in every second, and the overall mean must
also pass. `capacity-*` and `capacity-pilot-*` are exploratory frame-based/pilot runs,
retained separately and not used to qualify that strict condition.

`final-checks` contains the recreated primary-PC release suite (356 passed, 63 opt-in
tests ignored), 35 CUDA unit checks, ten CUDA integration checks, ten application
lifecycle checks, twelve viewer model checks, four device/render checks and two
analytic checks. Focused groups overlap the ordinary suite; do not add these counts
as unique tests. Strict all-target Clippy and formatting passed. Device tests exercise
creation, invalid geometry and error latching; model tests cover camera, selection,
surface failure, zero extent and teardown. Lifecycle/CUDA tests cover pause/resume,
exact accepted state, replay boundaries, cancellation and rollback. Actual removal
of the physical GPU/driver recovery was not attempted.

Final default smoke tests cover all three required counts, confirming the impostor
selection without an override. `native-check` records paused and running client-pixel
capture, resize 1280×720 → 1000×680 and cooperative close. Keyboard focus was not
reinvestigated without a new hypothesis. This check does not establish physical
desktop visibility or camera-input latency.

Retained failures are explicit: initial analytic preflights exposed a Rust closure
lifetime error and then a sign error in the independent CPU oracle; both were fixed
before timing. A later strict build exposed CUDA-only test imports in a CPU feature
configuration; they were correctly feature-gated. On recovery, the first full suite
reused a cached test binary with the deleted `/tmp` manifest path and failed a bundled
scene lookup. Touching source/test inputs forced a correct isolated-path rebuild;
the complete rerun passed without changing the test or scene contract. The failed
`final-suite.log` remains next to `final-suite-rebuilt.log`.

## Reproduction

These commands start **fresh simulations**, computing every required step. Use a
hardware graphics environment; keep builds, tests and GPU diagnostics outside ordinary
samples. Always specify experimental because the external fixtures retain reference
values when loaded with scene-only numerical selection.

```sh
cargo build --manifest-path Maelstrom/Cargo.toml --release --locked --features viewer,cuda
python3 -m tools.performance.live_viewer Maelstrom/target/release/maelstrom \
  docs/project/development/milestones/05/assets/particle-rendering-v1/inputs/110592.toml \
  /new/sample --particle-renderer impostor --steps 1200
python3 -m tools.performance.live_viewer Maelstrom/target/release/maelstrom \
  docs/project/development/milestones/05/assets/particle-rendering-v1/inputs/38400.toml \
  /new/capacity --particle-renderer impostor --steps 4800 --acceptance-profile
python3 -m tools.performance.particle_capacity /new/capacity/accepted.csv
python3 -m tools.performance.particle_report \
  docs/project/development/milestones/05/assets/particle-rendering-v1
python3 -m unittest tests.performance.test_live_viewer tests.verification.test_display
```

Run Cargo in Maelstrom or supply its manifest path. The particle reporter validates
stored ordinary summaries, recomputes separate GPU profiles and exact capacity results,
and writes `assessment-data.json`/`results.md`; it makes no retention decision.
The visual harness is the ignored `matched_particle_stills_and_motion` test, using
`MAELSTROM_PARTICLE_INPUTS` and a new `MAELSTROM_PARTICLE_OUTPUT` directory, followed
by `python3 -m tools.performance.particle_visuals SOURCE OUTPUT` with existing ffmpeg.
`SHA256SUMS` covers the evidence files; tool/source receipts identify the current
uncommitted implementation. None of these files is a tagged historical checkpoint.

`renderer.patch` is a cumulative diff against Maelstrom HEAD for the affected graphics,
viewer and worker files plus the new particle module/tests. It includes the preceding
indexed-mesh and timing work, so it is not a clean patch against the four-mode campaign
source. Production-file digests, rather than a claimed clean Git boundary, identify
the measured uncommitted trees. Thirteen parent Python checks passed locally; the
144 retained stills were independently decoded and matched to their raw RGBA hashes.
