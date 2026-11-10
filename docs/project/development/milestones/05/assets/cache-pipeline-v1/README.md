# Production simulation-cache evidence

Retain the versioned cache and independent renderer; keep direct compilation as the default.
The [implementation record](/docs/project/development/milestones/05/performance-cache-pipeline.md)
explains behaviour, costs, compatibility and remaining qualification. The
[application guide](/Maelstrom/docs/cache.md) describes supported commands and wire format.
This evidence measures the production CLI, not the earlier serial review prototype.

## Exact source and executable identity

Both controls were exported from the actual working Maelstrom tree, based on
[`6bf2682325b7665e48f8a8647ce087d48ff13f0b`](https://github.com/Mahkrab/Maelstrom/tree/6bf2682325b7665e48f8a8647ce087d48ff13f0b).
That commit alone is **not** the measured revision. The starting tree included uncommitted CUDA
improvements and their tests. [Starting source](baseline-source.json) lists its 266 source files;
[final source](candidate-source.json) lists all 276 files and the exact implementation delta.
All initially present native/CUDA files, tests, numerical configuration and dependency/lock files
retain their starting bytes. The [delivered source](delivered-source.json) differs from the measured
candidate by removal of one leading blank line in `build.rs` and conditional import of `Path` in render-only
integration tests, found by final formatting/headless Clippy checks.
[The delivery patch](delivery-cleanup.patch) records that exact difference. It changes build-source
provenance identity, without changing production Rust statements or test assertions. Performance
was not remeasured for those corrections.

[Executable and native identity](binary-source-identity.json) establishes:

- Starting working-tree binary: `2a23926ac808fefecdb2173d66bad394af226fa3706b81a67c01dbf7fd41b1d6`.
- Measured implementation binary: `96ae79349b0e802c7cba4dc9da8a3b3f0d7b42757dc04531c90ba8456d514848`.
- Final embedded source identity: `b46486fa569de6cf7345f213bbbf1f913824ae040042dcfc91675a0250f57ecc`.
- Both executables contain the same freshly compiled **317,123-byte** PTX,
  `cf4a83d08b2db15e1576a975759b41844d853b2b52e69235890cc254dce45b8b`.

[Delivery verification](delivery-verification.json) identifies the subsequently formatted executable,
`a7573ebeeab3c530044dcbc3c5384f695e6561131c7ad3f97ac5bb23f9b2542f`, with embedded source
`aa127c63455c9c5a30ef2351d500308c41a59e7a871684f299c8e297cab6d0c0`. Its native PTX is unchanged.
The [delivery logs](delivery-raw.tar.gz) and [seal](delivery-raw-manifest.json) record repeated release
qualification, strict headless and all-feature Clippy, the feature-conditional import correction, and
a fresh large cached-frame replay matching measured direct PNG/RGBA/canonical hashes with zero fluid
steps. The cache CLI tests passed again after the import correction; test assertions did not change.

The collector recomputes source identity using Rust's component-wise path order and verifies that
both source digest and freshly compiled PTX are embedded in the executable. Separate Cargo target
directories prevent cross-export artefact reuse. No installed application, history or gitlink changed.

[The source reconstruction receipt](source-reconstruction.json) verifies three patches in isolated
non-Git exports. Apply [the starting working-tree delta](baseline-working-changes.patch) to a fresh
`git archive` of the base, then [the implementation delta](cache-implementation.patch) to a copy. Apply the delivery patch
last to reproduce the delivered tree.
Every resulting file was compared against its corresponding source manifest. The first patch
preserves user work for reproducibility; it is not a change attributed to this implementation.
It deliberately retains pre-existing whitespace. These patches replace complete source archives
in the repository evidence; they are not commits or checkpoint authority.

## Measurement and qualification

[Environment](environment.json) identifies the primary Ryzen 9 7900X / RTX 4070, WSL2 kernel,
driver, Rust/CUDA toolchains and hardware graphics adapter. [Protocol](production-protocol.json)
fixes one warm-up, three alternating AB/BA pairs, experimental defaults, 1,200 accepted steps,
stride 4 and 301 output frames at 8,000 and 110,592 particles. Initial rendering uses 640×480,
a common fit-camera configuration and energy colouring. Alternative rendering uses 1280×720,
a shifted fixed camera and fixed colouring, matched between direct and cached controls.
Every cached-render process had CUDA devices hidden. Setup, teardown and publication remain in
process clocks. Builds, tests and other experiment commands did not overlap timed samples in this
session; unrelated external activity cannot be excluded. No driver, clock or system setting changed.

- [Final summary](production-summary.json) retains every warm-up, measured process, command,
  stage interval and paired first-export sum. The 9.436/19.642-second first staged medians are
  paired sums of two processes, not a separate orchestration benchmark.
- [Resources](production-resources.json) retain process RSS/CPU, whole-device GPU samples and
  complete cache sizes. Warm reads and synced file-publication rates are not SSD benchmarks;
  GPU samples are not per-process occupancy or kernel execution counters.
- [Verification](production-verification.json) records all 40 validated image bundles,
  12,040 PNG readbacks, eight full caches and 2,408 independent canonical checks. The assessor
  compares exact frame lists, input records and binary32 accepted diagnostics against direct exports.
- [Qualification](qualification.json) records 427 passing final release tests, zero failures,
  strict all-feature/all-target release Clippy, enabled suites and ten remaining specialised opt-ins.
  Opt-in graphics fault tests explicitly use software Vulkan; hardware is used for performance.
- [Resource failure](resource-failure.json) records a child-only 48 KiB file-size limit and EFBIG.
  It preserved 132 committed frames, returned failure, published no completion and passed full
  prefix validation. Cancellation, corruption, missing completion and no-overwrite cases are also
  tested in the production Rust/CLI suites. No power-loss test is claimed.

The final [raw archive](final-raw.tar.gz), [member seal](final-raw-manifest.json) and
[local verification](local-verification.json) retain the exact collector/seal code, requests,
manifests, frame receipts, diagnostic JSONL, per-process output, resource/GPU logs, source identities,
build/test logs and failure metadata. Every member and archive digest was checked on the primary
PC and locally. The stripped records reproduce the published summary and resources exactly. For the resource-size
check, temporary sparse placeholders reconstruct omitted file sizes from receipt lengths and the
8N identity-table contract; these placeholders are never treated as valid particle data.
Particle binaries, PNGs, executables, complete source trees and Cargo products are omitted from
these repository archives; the primary experiment retains them separately.

The [earlier production archive](earlier-raw.tar.gz) and [seal](earlier-raw-manifest.json) retain
another complete campaign before the final provenance additions. Its source identity and ranges
are distinct and are **not pooled** with final results. It includes the originally timed collector,
the assessor's initial false JSON-decimal mismatch, the corrected assessor and successful readback.
Direct manifests expand binary32 diagnostics via a JSON value; typed JSONL uses shortest binary32
decimals. The corrected assessor compares exact declared f32 bits, not loose tolerances; a parent
regression test rejects one-ULP differences. Image, pixel and snapshot hashes already matched.
The clean-commit serial review prototype is a third, historical experiment and is not a matched
performance baseline for this implementation's pre-existing native changes.

## Retained primary files and reproduction

The durable primary roots on `ssh pc` are:

- Final: `/home/oliver/.local/share/maelstrom-experiments/cache-pipeline-v1`.
- Earlier: `/home/oliver/.local/share/maelstrom-experiments/cache-pipeline-initial-v1`.

The original `/tmp/maelstrom-cache-final` and `/tmp/maelstrom-cache-implementation` aliases remain
symlinks, preserving exact command paths and the final campaign's baseline-target link. Full images,
caches, source exports, binaries and target directories remain there. These are local retained
experiments, not hosted or committed verification.

For a fresh campaign, reconstruct `ROOT/baseline` and `ROOT/candidate` as above; copy the two source
manifests and the retained collector to ROOT. Build each with its own `CARGO_TARGET_DIR`,
`CUDA_HOME=/usr/local/cuda cargo build --release --locked --all-features --bins` from its source
export. Run `python3 cache_pipeline.py identities ROOT`, then `measure ROOT`, `resources ROOT`,
`verify ROOT` and `resource-failure ROOT` using a new result root/destination set. The collector
requires `runs` and the fault destination not to exist. New paths/toolchains can change binary
identity; record those identities rather than assuming byte-identical rebuilds.

`compile` and `cache bake` start new simulations. `render`, cache validation and PNG playback
consume existing observations and do not continue a solver. Reassessment of a stripped archive
supports `assess`; `resources` also needs the omitted cache file sizes (or temporary size fixtures).
Image/binary validation requires the separately retained full
primary outputs. Run the parent collector tests from EPQ with
`python3 -m unittest tests.performance.test_cache_pipeline`.

No cold-disk, long-duration memory soak, compression, direct video, external renderer, Windows/macOS,
power-loss or solver-checkpoint qualification is implied. The first staged export remains slower
than direct compilation; the large repeated-render saving supports retention of an explicit staged
workflow, not an unconditional default switch.
