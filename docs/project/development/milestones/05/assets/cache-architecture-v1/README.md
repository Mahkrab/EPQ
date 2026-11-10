# Simulation cache review evidence

The [architecture review](/docs/project/development/simulation-cache-review.md) recommends a staged
particle cache and independent renderer, while rejecting adoption of this serial prototype as
production. It preserves first-export regressions, repeated-render benefits and negative results.
No application source or numerical method was replaced.

## Identity and experiment boundary

The primary PC experiment uses clean Maelstrom
[`6bf2682325b7665e48f8a8647ce087d48ff13f0b`](https://github.com/Mahkrab/Maelstrom/tree/6bf2682325b7665e48f8a8647ce087d48ff13f0b)
plus an isolated measurement overlay. [Source identity](source-identity.json) records every tracked
exported source file and the two added diagnostic files. Only `src/export/mod.rs` and
`src/workflow/record.rs` differ from the clean base: one adds the experimental module, the other
adds a checked snapshot constructor. All native, numerical, render/shader, dependency and lock
files match that clean base. The local dirty CUDA candidate was not benchmarked.

The two measured release binaries are:

- Application: `e8459c6a14138c5c71f45a6076468b423bb17ecb3511da8d5d02dbeea1f37467`.
- Probe: `33206d148b628e1ac3fa26c9742be84a61d25e40e21da230abf665ab237e6a19`.
- Both contain the same freshly built **218,499-byte** PTX,
  `2bb95233ef4e5aa5d7f328a3e93715855f8d7dea026c053acc1be8ba666d6203`.

[Environment](environment.json) records the Ryzen 9 7900X, RTX 4070, WSL2 kernel, CUDA/Rust tools,
driver and hardware OpenGL/D3D12 device. The [prospective protocol](protocol.json) fixes one warm-up,
three alternating A/B pairs, experimental numerics, CUDA 0/block 128, 1,200 accepted steps,
stride 4, 301 images and 640×480/1280×720 resolutions. Measurement ran without overlapping builds,
tests or other experiment commands in this session. Unobserved activity outside this session
cannot be excluded. Whole-device GPU samples are not exclusive process counters.

Each A process is ordinary `compile`, including scene resolution, output catalogue and teardown.
B measures two independent processes: a serial binary cache bake and rendering using the unchanged
private offscreen/encoding path. B starts from a frozen resolved-input document and emits experimental
records rather than an application-supported bundle. It intentionally recalculates canonical hashes
during rendering; no provenance shortcut, production receipt journal or asynchronous cache writer is
implemented. The benchmark does not claim a drop-in production speedup.

## Retained observations

- [Complete summary](summary.json) retains all warm-ups and measured process clocks, stage profiles,
  RSS/CPU accounting, commands and paired first-export sums. Warm-ups are not pooled with measurements.
- [Resource summary](resource-summary.json) retains per-invocation GPU samples' aggregates, independent
  process high-water RSS, CPU equivalents, effective packing/write/sync and warm-read rates. These
  are not SSD-only rates; no cold-cache experiment was performed.
- [Verification](verification.json) records exact frame/provenance checks, published-file readback,
  old bundle validation, additional fixed-camera new-resolution controls and changed camera/colour
  renders with CUDA devices hidden from those processes. The original campaign's refitted-camera
  controls remain in the raw evidence and are not used as exact-image comparisons.
- Fault checks reject a byte flip, a truncated frame, an incomplete cache and an existing destination.
  An injected stop after seven writes preserves seven byte-exact observations and no completion
  index. This is process-failure/prefix evidence, not power-loss durability or solver continuation.
- Primary-PC exporter tests passed four ordinary tests and three explicitly enabled software-Vulkan
  cancellation/failure tests. Test logs are inside the raw archive. Four focused parent tests passed
  locally; the retained local receipt names their scope. No full fresh solver suite or physical
  qualification is claimed for the unchanged numerical source.

[The raw archive](raw.tar.gz) and [member manifest](raw-manifest.json) retain exact timed collector,
probe and supplementary check code, requests, compressed original manifests, per-process output and
resource/GPU logs, fault outcomes, test/build logs, source identities and seal code. The archive
excludes complete source trees, binaries, build products, duplicate PNGs and binary particle caches.
Every archive member and the archive SHA-256 were verified on the primary PC and locally.

The durable primary root on `ssh pc` is
`/home/oliver/.local/share/maelstrom-experiments/cache-architecture-v1`; it retains full caches,
images, executables and build/source exports. The recorded commands used the temporary alias
`/tmp/maelstrom-cache-review-20261110`. These are source-identified experimental files, not a Git
checkpoint or hosted verification.

## Reproduction and limitations

`compile`, probe `simulate` and probe `bake` start new simulations. Probe `render`, `render-alt`
and `validate` consume immutable cached observations and run no fluid timesteps. They do not resume
a solver. Current application `play` consumes PNGs.

1. Export the named base into a fresh non-Git `ROOT/source` with `git archive`; do not alter the
   working repository. Copy the retained `cache_review.py` and `cache_review_probe.rs` together
   outside it, then run `python3 cache_review.py prepare ROOT/source`. Check the four overlay
   paths and full source hashes against `source-identity.json`.
2. Build in that export with `CUDA_HOME=/usr/local/cuda CARGO_TARGET_DIR=ROOT/target cargo build
   --release --locked --all-features --bins`. Check native/PTX identities independently. Recreated
   build paths/environment may change executable bytes; record new identities rather than assuming
   binary equality.
3. Run `python3 cache_review.py measure ROOT` on the primary PC with new output destinations and
   no competing experiment. It retains all processes and runs exact-output assessment. A later
   evidence-reader revision adds finite-clock/resource rejection and preflight refusal of Git
   checkouts; the exact timed version is preserved in the archive.
4. Supplementary `tools/performance/cache_review_checks.py` runs as a module from an EPQ-style
   module root containing these two parent tools. It verifies frames/files, creates fixed-camera
   new-resolution controls, changes view/colour without CUDA and injects faults into fresh copies.
   It never modifies a measured cache. Run the focused parent tests from EPQ with
   `python3 -m unittest tests.performance.test_cache_review`.

The prototype requires its resolved-input request alongside the frame files. The proposed production
cache instead owns immutable inputs and receipts. No compression, direct video, multi-GPU/hybrid
worker, persistent GPU readback ring, cold-disk, disk-full, power-loss, render-resume or solver-restart
implementation was measured. No first-export improvement is established: the serial prototype is
materially slower at both particle counts. The architecture recommendation concerns reusable
simulation and independent presentation, with remaining optimisation claims explicitly modelled.
