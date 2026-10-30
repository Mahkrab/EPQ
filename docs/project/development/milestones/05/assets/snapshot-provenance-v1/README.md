# Snapshot provenance evidence

The [assessment](/docs/project/development/milestones/05/performance-snapshot-provenance.md) retains
fixed-schema buffered SHA-256 after byte-exact saved-state checks and a complete-compilation gain.
Both control and candidate retain the parallel encoding pipeline, both numerical modes and all ten
CUDA optimisations. No snapshot contents, canonical representation, hash format or output ordering changed.

## Source boundary

The nearest committed base is Maelstrom `250932784790ba26cdc55fc38a877ccefacbf054`.
[The control patch](control-from-base.patch) reconstructs the **193-file** starting working source,
including the earlier mode integration, test relocation and parallel output pipeline.
[The candidate patch](candidate.patch) adds the fixed-schema writer, its checks and guide, changing
four Rust files plus documentation. [The source manifest](source-manifest.json) and
[reconstruction receipt](source-reconstruction.json) check all **194 candidate files**. This is a
source-identified uncommitted tree, not a newly created historical checkpoint.

The measured primary-PC SHA-256 identities are:

- Control executable: `bdf2312ad3e35f14456155f8662b3440088401a26d6d3a0aa04e0b509f8f0b95`.
- Candidate executable: `d2797727102e103ccb2f5cfc633318035f86d332818ba88792e75c41edf8f111`.
- Common embedded CUDA PTX: `9b08047ae31b3e7cc57994a3b2b00d2787ec602ecabac3d0408f365992f242a5`,
  221,060 bytes.

[Qualification](qualification.json) identifies changed files and 401 passing tests.
[Post-collection checks](post-verification.json) establish unchanged binary/source identities,
matching embedded CUDA code, preserved numerical/configuration/render/dependency files and unchanged
pipeline scheduling. Worker queue/drop code and the export driver remain byte-identical; the worker's
hash call and digest formatting helper are the intended changes. [Environment readings](environment.txt)
record the PC and toolchain.

The durable primary root is
`/home/oliver/.local/share/maelstrom-experiments/snapshot-provenance-v1` on `ssh pc`.
It retains all source exports, binaries, build trees, requests, observations and PNG bundles.
Local reconstruction and verification are under
`/home/mahkrab/.local/share/maelstrom-experiments/snapshot-provenance-v1`.

## Timings and equivalence

[The prospective protocol](protocol.json) separates independent provenance timing from complete
compilation and fixes inputs, warm-ups, rounds and the written retention assessment.

- [Independent measurements](micro-summary.json): 21 saved states at quarter-second intervals per
  numerical mode and particle count, one warm-up and five measured rounds with rotated algorithm order.
  The original serializer, favourable exact-capacity vector, generic buffered hash and fixed-schema
  buffered hash all process the same states. Original-format-only and precomputed-byte SHA-only clocks
  are diagnostic controls, not production shortcuts. Loading, byte checks and write-operation counting
  stay outside timers. Every timed result is consumed through `black_box`.
- **84 exact canonical-byte comparisons** and matches to the original production snapshot SHA-256
  precede timing. The saved native inputs and original image/provenance records come from the existing
  [fast-mode campaign](/docs/project/development/milestones/05/assets/fast-mode-v1/README.md), not a new
  numerical or physical-model experiment. The timed harness and private benchmark accessors are retained
  separately from production source; they add no public production API.
- [Complete compilation measurements](measurement-summary.json): one warm-up and three alternating
  pairs at each count/mode, five nominal simulated seconds, 60 Hz, 301 frames at 640×480. All **twelve
  measured pairs** were faster. Every time and paired ratio is retained, including the last slower
  large fast pair and the slower large reference candidate warm-up. No measured command overlapped
  tests, builds, microbenchmarks or audits.
- Every **32 compiled bundles / 9,632 PNGs** passed application validation and encoded-file hash checks.
  Full resolved inputs, ordered frame/pixel/snapshot hashes and every accepted diagnostic agree exactly
  with their corresponding original production control. The PNG bytes are already in the fast-mode
  seal; fresh identical bundles remain in the durable primary root rather than being duplicated here.

The [raw seal](retained/manifest.json) contains **359 files / 28,946,273 raw bytes** in one
**17,785,148-byte archive**. It retains microbenchmark streams, saved-state requests and hashes,
all measured/warm-up process records and GPU samples, compressed manifests and CLI output,
per-frame output receipts, validation results, protocol, source/probe identities, build/test logs,
patches and exact collector/retention/harness code. Executables, build trees, complete source trees
and duplicate PNG bundles are excluded. The maintained evidence reader was tightened after collection
to reject altered provenance, byte totals, duplicate rounds and inconsistent timing workloads; the
actual timed Rust harness is preserved independently.

Both [primary archive verification](seal-verification.json) and
[local member readback](local-seal-verification.json) verified the archive and every member hash.
[Verification logs](verification-logs.tar.gz) retain the 401-test primary release suite, strict
Clippy/formatting, local canonical/default/render and software export checks, and three parent evidence
reader tests. No native sanitizer or exhaustive CUDA power rerun is claimed for unchanged native code.

## Reproduction

`compile` starts a new simulation. `snapshot-probe` loads immutable native observations and performs
no numerical steps. Analysing these records or playing the PNGs does not continue a simulation.
Use new isolated destinations; collectors deliberately reject existing outputs.

1. Export the base into `ROOT/control`, apply `control-from-base.patch` with `patch -p1`, then copy it
   to `ROOT/candidate` and apply `candidate.patch` there. Check both trees against `source-manifest.json`.
   This exact route was reconstructed locally and checked file by file without changing either Git history.
2. Build both exports with `CUDA_HOME=/usr/local/cuda`, an isolated `CARGO_TARGET_DIR`, and
   `cargo build --release --locked --all-features`. Copy executables to `ROOT/bin/control` and
   `ROOT/bin/candidate`. Complete the release/opt-in regression, strict Clippy and formatting before timing.
3. Restore the earlier fast-mode inputs, native observations and original compiled manifests in `OLD`.
   `tools/performance/snapshot_probe.py` prepares an isolated `probe-source` from the candidate.
   Its `requests(OLD, ROOT / "requests")` creates the four saved-state requests. Build the additional
   `snapshot-probe` binary with the same optimised feature selection and run it on each request JSON,
   retaining output under `ROOT/micro/CASE.jsonl` and stderr alongside it. The seal contains the exact
   timed harness, accessor overlay and requested input hashes. `assess(ROOT)` validates and regenerates
   the independent summary without running a simulation.
4. From EPQ run `python3 -m tools.performance.render_pipeline ROOT OLD measure` for complete compilation.
   Both binaries use the parallel output pipeline. The collector freezes identities, alternates
   requests and validates every bundle/image/input/diagnostic after its process timer.
   `summarise` regenerates the compilation summary without new simulation.
5. `retention-select.py` in the seal selects receipts and uses the existing bounded archive writer.
   Verify this mirror with:

   ```sh
   python3 tools/performance/frontier_retain.py \
     docs/project/development/milestones/05/assets/snapshot-provenance-v1/retained --verify
   ```

These are primary-PC/WSL OpenGL and Linux process measurements. GPU samples are coarse whole-device
readings; cumulative child RSS is not a per-invocation peak-memory comparison. Small workload gains
have only three measured pairs. No hosted validation or performance guarantee for another backend
is implied. No repository history, gitlink, installed executable or system-wide setting changed.
