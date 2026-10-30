# Rendering pipeline evidence

The [assessment](/docs/project/development/milestones/05/performance-render-pipeline.md) retains one
bounded CPU encoding/hash worker after complete compilation comparisons. Rendering, PNG encoding,
canonical snapshot JSON and all numerical policies remain unchanged. This is an uncommitted,
source-identified experiment, not a new Git checkpoint.

## Source and executable identities

The base is Maelstrom `250932784790ba26cdc55fc38a877ccefacbf054`. The control includes the existing
fast-mode integration and test relocation present at the start of this request.
[The control patch](control-from-base.patch) reconstructs that working source from the base;
[the candidate patch](candidate.patch) applies only the export worker, timing, tests and guide.
[Source reconstruction](source-reconstruction.json) checked all **192 control and 193 candidate
files** against [the source manifest](source-manifest.json).

Both executables were release builds with all features on the primary PC. Their SHA-256 values are:

- Control: `0bd05fcc9bf512d608edb5ad37b29f88513b3aadf194a616e3b59b9bd8dd8ca0`.
- Candidate: `4d7f228fbf6fa86f4c68c7c3ea031081aae7853988e573d3ea9da20dac9f33a5`.
- Common embedded CUDA PTX: `9b08047ae31b3e7cc57994a3b2b00d2787ec602ecabac3d0408f365992f242a5`,
  221,060 bytes.

[Preservation checks](preservation.json) identify the seven changed files and unchanged simulator,
numerical-mode, dependency and native sources. [Post-collection checks](post-verification.json)
confirm unchanged source/binary identities, timing accounting and complete collection.
[Environment readings](environment.txt) identify the PC and toolchain. No installed executable,
checkout history, gitlink, tags or system settings were changed.

The durable primary root is
`/home/oliver/.local/share/maelstrom-experiments/render-pipeline-v1` on `ssh pc`. It retains source
exports, binaries, build trees and every compiled bundle. The local reconstruction/verification
root is `/home/mahkrab/.local/share/maelstrom-experiments/render-pipeline-v1`.

## Measurements and raw records

- [Complete compilation results](measurement-summary.json): one warm-up and three alternating
  control/candidate pairs at 8,000/110,592 particles in each numerical mode, five seconds, 60 Hz,
  301 frames, 640×480. It exposes every measured wall time, paired speedup, stage median,
  process CPU utilisation and sampled whole-device GPU utilisation.
- [Instrumented stage totals](profile-summary.json): four additional compilations, kept apart
  from ordinary timings. Graphics timestamp queries and an extra queue drain separate GPU drawing
  and texture copy from CPU preparation, upload/submission, map waits and row unpack. Snapshot JSON
  generation and SHA-256 have distinct clocks. These nested CPU/GPU intervals are not additive.
- [Saved-state profiles](probe-summary.json): 21 states per mode/count at quarter-second times,
  four renders each, with the first pass excluded from timing medians. All **336 replay images**
  match the original production PNG and RGBA hashes. The corresponding native observations are
  retained in the earlier [fast-mode seal](/docs/project/development/milestones/05/assets/fast-mode-v1/README.md).
- [Verification logs](local-and-primary-checks.tar.gz) and [local results](local-verification.json):
  398 primary-PC all-feature/opt-in Rust checks, 291 local default checks, software export tests,
  strict Clippy, formatting and four parent evidence-auditor tests. No native sanitizer or exhaustive
  power rerun is claimed for unchanged native code.

The [raw seal](retained/manifest.json) inventories **593 files**, **122,971,275 raw bytes**, in two
archives totalling 49,738,594 bytes. It contains every final/pilot/profile process and timing record,
compressed manifests and CLI output, per-frame digests, validation results, 200 ms GPU samples,
saved-state requests and profiling streams, Nsight reports/statistics, source identities, patches,
build/test logs and exact collector/overlay/retention scripts. Build trees, executables and full
source trees are excluded. The first small control warm-up overlapped CPU-only trace report
generation; no measured sample did. A replay preparation attempt that matched `state-rows.bin`
was corrected to select decimal step filenames before collection.

The final **32 bundles / 9,632 PNGs** passed application validation and individual encoded-file
hash checks. Complete frame, input and accepted-diagnostic identities also matched the corresponding
retained fast-mode control. Fresh PNG bundles remain in the primary root; their identical original
image bytes are already in the fast-mode seal and are not duplicated here. The early pilot and four
instrumented compilations remain distinct from the final campaign. No slow sample was removed.

Both [primary seal verification](seal-verification.json) and
[local member readback](local-seal-verification.json) checked every archive and member hash after transfer.

## Reproduction

Compilation and `run` commands start new simulations. `render-probe` loads immutable saved native
states; it performs no numerical steps. Decoding these archives or playing PNG bundles does not
continue a simulation. Use fresh destinations; collectors deliberately reject existing output.

1. Export the base commit into `ROOT/control`, then apply `control-from-base.patch` there with
   `patch -p1`. Copy that source into `ROOT/candidate` and apply `candidate.patch` with `patch -p1`.
   Check all files against `source-manifest.json` before building. The reconstruction receipt
   demonstrates this exact two-patch route; neither repository needs a branch or history change.
2. Build each isolated source with `CUDA_HOME=/usr/local/cuda`, a separate `CARGO_TARGET_DIR`, and
   `cargo build --release --locked --all-features`. Copy executables to `ROOT/bin/control` and
   `ROOT/bin/candidate`. Run the retained release/opt-in checks, Clippy and formatting before timing.
3. Restore the earlier fast-mode scene/configuration inputs and original compiled manifests in
   `OLD`. From the EPQ root run
   `python3 -m tools.performance.render_pipeline ROOT OLD measure`. It declares the protocol,
   alternates requests, retains failures/telemetry, checks unchanged executables and audits every
   image and numerical identity. `summarise` regenerates the ordinary summary without simulation.
4. For diagnostic attribution, use `tools/performance/render_probe.py` to prepare an isolated
   control export. Its `requests(OLD, OUTPUT)` selects saved states that also have original images.
   Build its additional `render-probe` binary and run it on each request JSON. The retained collector
   copy and per-command process records fix the executed recipes. `assess(ROOT)` rejects changed
   state/image hashes and incomplete timing streams. Do not use instrumented clocks as ordinary
   end-to-end retention samples.
5. `retention-select.py` inside the seal selects metadata, profiling and exact scripts without
   duplicating complete PNG bundles. It uses the existing bounded archive writer. Verify this mirror:

   ```sh
   python3 tools/performance/frontier_retain.py \
     docs/project/development/milestones/05/assets/render-pipeline-v1/retained --verify
   ```

Performance qualification is limited to the measured WSL2/OpenGL hardware path. GPU utilisation is
coarse whole-device telemetry, CPU readings cover Linux process time, and clocking observations
support an inference rather than proving the driver's power-policy mechanism. No hosted verification
or new physical-quality assessment is implied.
