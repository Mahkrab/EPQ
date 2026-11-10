# Reusable simulation cache implementation

**Retain the production cache and independent-rendering path; keep direct `compile` as the default.**
Maelstrom can now bake a reusable particle sequence, validate it, render it repeatedly with new
presentation settings and produce selected-frame image bundles without executing fluid timesteps.
The [architecture review](/docs/project/development/simulation-cache-review.md) remains the rationale
and historical prototype result. Its serial prototype was not adopted.

The implementation is in the actual working Maelstrom tree, including the pre-existing uncommitted
CUDA improvements. The [evidence receipt](/docs/project/development/milestones/05/assets/cache-pipeline-v1/README.md)
identifies the exact measured working sources, executables, common freshly compiled PTX, controls,
protocol, verification and raw records. No numerical method, mode, CUDA file, live-viewer renderer,
shader, dependency or lockfile was changed by this implementation. Neither Git history nor gitlink,
installed binary, driver or system setting was changed.

## Application and storage boundary

[The cache module](/Maelstrom/src/cache/mod.rs) owns a compact schedule, a binary format, a bounded
asynchronous producer and a validated reader. `cache bake` observes the existing `Simulation` only
after step acceptance. It captures scheduled snapshots, while all accepted diagnostics stream through
a fixed buffer to JSONL. One owned frame can be outstanding to a CPU writer; solver resources remain
on their owning thread. The producer retains no particle history, diagnostic vector or frame-index
vector proportional to duration. The initial observation commits before stepping, and subsequent
backpressure is tied to cache capacity, never PNG generation.

The worker computes the unchanged canonical snapshot digest, packs exact f32 arrays, computes the
binary checksum and prepares/syncs an immutable frame. The caller collects and publishes the small
receipt in deterministic order. Receipt publication is synchronous by design: it identifies the exact
committed prefix and remains visible in the timing breakdown. Particle hashing and frame-file work
are asynchronous. This differs from the prototype's serial simulation/hash/write loop.

[The format and CLI guide](/Maelstrom/docs/cache.md) owns the version-1 wire specification. Positions
and velocities occupy 24 bytes/particle; stable u64 identities are stored once. Each frame has a
160-byte header, rather than the review's proposed 128 bytes: the additional 32 bytes bind the original
canonical digest inside the checked binary frame. Independent frame receipts and a final completion
marker bind request, content and diagnostics. Raw storage avoids a new dependency and preserves
seeking, failure isolation and exact bits. Compression remains unimplemented.

The reader checks metadata, identities, receipt chain, diagnostic order/checksum and bounds; it then
loads and checks only requested particle frames. It retains a bounded metadata index, at most 32 MB
of pinned receipt digests at the one-million-frame cap. Those pins also reject receipt mutation after
opening. Input validation has a separate observation path that never constructs a simulation, worker
pool or CUDA context. Full validation independently recomputes canonical digests. Integrity checks
are not authentication: externally produced, self-consistently rewritten metadata still requires
full canonical validation. That boundary has an explicit regression test.

## Independent rendering and compatibility

[Cached rendering](/Maelstrom/src/export/cached.rs) shares the existing indexed offscreen renderer,
pixel readback, PNG settings and bounded encoder. An owned `ValidatedFrame` carries its checked
snapshot and bound canonical digest together. The encoder distinguishes that value from ordinary
recorded snapshots, which still require canonical hashing. Binary checksums never replace canonical
snapshot digests. No global digest lookup or untyped caller-supplied hash is used.

`render CACHE` supports new camera/colour documents, resolution overrides, one frame, or inclusive
index ranges with an explicit increment. It reads no mutable scene package and accepts no numerical
override. Standalone rendering uses the built-in presentation unless a render document is supplied;
the simulation cache contains physical inputs, not camera preferences. `compile --cache-output DIR`
provides staged orchestration with ordinary scene-package presentation resolution.

Cache-derived image manifests use schema 2 and an explicit cache selection/timestep mapping. This
preserves schema-1 schedules and their existing meanings, while allowing a first selected frame at
nonzero simulation time. Playback normalises its internal clock to the first selected image and
retains original simulation timestamps in the manifest. Schema dispatch deliberately supports both
versions in playback, inspection, image validation and recorded-input reruns. Images remain playable
and verifiable after deleting the source cache. Reruns still start at zero.

Existing `compile`, `export saved`, `export rerun`, input records, PNG/pixel/canonical hashes and
`play --last` semantics remain intact. The staged option records its completed image output through
the existing catalogue path. A completed cache survives image-rendering failure. Direct compilation
remains the default; it still overlaps CPU encoding and canonical streaming hashing as before.

## Failure and provenance decisions

Exclusive file publication and ordered receipts identify committed cache frames. A complete cache
marker is published only after the requested schedule and diagnostics close. Unix directories are
synced at publication boundaries. Cancellation closes and joins the CPU writer, discards uncommitted
results and leaves a verifiable prefix. Unreceipted prepared files are ignored. Reader flags and CLI
range requirements make incomplete sources explicit; a complete selected image request does not
turn its source cache into a complete simulation. There is no solver continuation API.

Tests cover byte-level layout, signed zero, maximum u64 identities, finite values, version/flag/offset
rejection, frame and metadata corruption, truncation, symlinks, mutation after opening, cancellation,
failed asynchronous writes, existing destinations, empty observations and absent completion markers.
A process-local file-size fault additionally forces a real Rust I/O error after frames commit,
without altering any system-wide limit. The CLI returns failure and the retained prefix passes full
validation; no completion marker is created.

Request provenance includes resolved inputs, exact timestep, sampling, backend/resources, runtime
device and build/compiler/flag identity. Result identity additionally binds ordered receipts and all
accepted diagnostics. Rendering records its own build, adapter identifiers, shader and encoder beside
the source cache identity. A final provenance audit added the compiler-flag digest and graphics
vendor/device IDs before the final measurement build. Earlier production measurements are retained
separately; neither those nor the review's clean-commit prototype are pooled into final statistics.

## Matched primary-PC measurements

The final measurement build was timed on the primary Ryzen 9 7900X / RTX 4070 under WSL2, driver
610.88, CUDA 13.3.73 and Rust 1.96.0. Rendering used hardware OpenGL through Mesa D3D12.
Each scene had one warm-up and three alternating AB/BA pairs, with experimental numerics,
1,200 accepted steps, stride 4 and 301 observations. Those steps represent nominally five seconds
at the existing binary32 240 Hz timestep. A used the frozen **actual starting working tree**;
B used the final implementation. Both contained identical freshly compiled native PTX, including
the previously uncommitted CUDA improvements. The nearest Git commit alone does not identify either
binary. Exact source manifests and reconstructable patches are retained with the evidence. Final
formatting removed one leading blank line from `build.rs`, and headless Clippy found a render-only
`Path` import in an integration test. The separate delivery patch records both corrections. Production
Rust statements and test assertions are unchanged, but build-source provenance identity differs.
Performance was not remeasured for these non-runtime corrections.

The normal request was 640×480 with a common fit-camera configuration and energy colouring. The
alternative used 1280×720, a shifted fixed camera and fixed colour, with exactly matched presentation
between direct and cached controls. Every cached rendering process ran with CUDA devices hidden.
Process clocks include startup, publication, catalogue work where applicable and teardown. The first
staged value is the median of the three **paired bake-plus-render sums**, not an independently timed
single-process orchestration. `compile --cache-output` was separately exercised by integration tests.

| Complete process or workflow | 8,000 particles, seconds | 110,592 particles, seconds |
| --- | ---: | ---: |
| Existing direct compile, normal | 5.697 | 18.909 |
| Bake reusable cache | 4.248 | 13.306 |
| Render existing cache, initial normal request | 5.189 | 6.342 |
| First complete bake + normal render | 9.436 | 19.642 |
| Repeat normal rendering | 5.234 | 6.462 |
| Direct compile, alternative presentation | 7.903 | 18.496 |
| Cached alternative presentation | 7.241 | 7.037 |

**The first staged export was 65.6% slower at 8,000 particles and 3.9% slower at 110,592 particles**
by these medians. Every measured paired first export was slower. Large cache rendering was about
2.98× as fast as a fresh normal direct export; repeating that render was about 2.93× as fast.
Alternative large rendering was 2.63× as fast as its direct control. Small repeated rendering offered
only a modest difference, with overlapping process ranges. The small campaign drifted upwards in
later rounds; all samples remain in the evidence and no unsupported cause is assigned. Three pairs
are useful engineering evidence, not a precise universal performance distribution.

The earlier production campaign, before the final provenance additions, is retained separately.
It had different process ranges and is not pooled into these medians. The review's 35.77-second
serial prototype also used different clean numerical/native source; attributing the difference from
that number solely to asynchronous writing would be invalid. The evidence for removing serial costs
is the current pipeline's overlapping stages, low writer wait and **zero canonical rehashing during
cached rendering**, together with exact canonical validation and image comparisons.

Stage medians below are accumulated intervals inside the process. The writer overlaps simulation;
PNG workers overlap graphics. These rows must not be summed to reconstruct wall time.

| Stage, seconds | 8,000 | 110,592 |
| --- | ---: | ---: |
| Bake solver steps | 2.663 | 11.656 |
| Direct compile solver steps | 2.791 | 11.653 |
| Bake snapshot capture / diagnostic serialisation | 0.004 / 0.002 | 0.060 / 0.003 |
| Asynchronous canonical hashing | 0.507 | 6.762 |
| Packing / binary hashing | 0.004 / 0.024 | 0.087 / 0.323 |
| Synced frame writing | 1.371 | 2.281 |
| Ordered receipt publication | 1.232 | 0.777 |
| Waiting for writer result | 0.014 | 0.333 |
| Cache file read / binary validation / decode | 0.021 / 0.030 / 0.038 | 0.075 / 0.359 / 0.478 |
| Render canonical rehashing / solver steps | 0 / 0 | 0 / 0 |
| Graphics commands and pixel readback | 1.112 | 3.005 |
| PNG encoding / pixel and PNG hashing | 3.035 / 0.158 | 3.223 / 0.162 |
| Image publication / progress publication | 0.705 / 0.796 | 0.604 / 0.605 |

The worker's large canonical hashing interval is substantial, but overlapped solver work rather than
being repeated during rendering. Synchronous durable receipt/progress publication is still a visible
cost, particularly for small scenes. There is no reason to hide it in a throughput claim. Bake setup
was 0.236/0.342 seconds; render setup was 0.325/0.332 seconds. Whole-process clocks include costs
outside these internal boundaries, including completion publication and teardown.

| Median process/resource observation | 8,000 | 110,592 |
| --- | ---: | ---: |
| Peak RSS: direct / bake / render, MiB | 295 / 110 / 197 | 577 / 159 / 496 |
| CPU logical-core equivalents: direct / bake / render | 1.26 / 0.80 / 0.78 | 1.24 / 1.46 / 0.95 |
| Sampled mean GPU use: direct / bake / render | 31.8% / 34.6% / 8.8% | 60.3% / 71.7% / 31.4% |
| Cache frame bytes | 57,840,160 | 798,964,768 |
| Complete cache bytes, including input and diagnostics | 60,304,595 | 830,580,355 |

GPU measurements are whole-device 200 ms samples, including the desktop, not exclusive allocation,
kernel time or occupancy counters. Peak sampled whole-device memory was approximately 1.8–2.0 GiB;
that is not Maelstrom's private GPU memory. No CUDA/graphics concurrency or contention speedup is
claimed: staged phases intentionally use the GPU separately. RSS is a process high-water mark,
including portable input/manifests and graphics/encoder resources, not a duration-growth experiment.
Bounded producer memory follows from its owned one-job channel and streamed diagnostics; a long-run
memory soak remains unmeasured.

For these frames, synced file-writing time implies effective frame rates of approximately 42/350
MB/s, including publication rather than raw SSD bandwidth. Read timings are warm OS-cache results;
no cold-cache or physical storage throughput claim follows. Resolved input JSON and static identities
are paid once per cache. Raw frame sizes are predictable: 160 + 24N bytes per observation, with
8N identity bytes once. Cache size grows with sampled frames, not every accepted timestep.

## Qualification, limits and adoption

The final primary-PC release build passed **427 tests, zero failures**: 368 ordinary tests,
38 explicitly enabled library tests and 21 explicitly enabled integration tests. The ordinary run
initially reported 69 ignored tests; 59 were subsequently run explicitly, leaving 10 unrelated
specialised opt-ins unexecuted. Strict all-feature/all-target release Clippy passed. Graphics fault
and compatibility tests selected software Vulkan explicitly; performance and large-scene comparisons
used the hardware adapter. Local headless checking, targeted cache/CLI tests and viewer tests also
passed; the three focused parent performance-assessor tests passed. Local checks are supplementary,
not replacements for primary-PC timings.

The final campaign validated all **40 image bundles and 12,040 PNGs**, compared every frame's PNG,
pixel and canonical snapshot identities against matched direct exports, and fully validated all
**eight caches / 2,408 canonical states**. All 1,200 accepted diagnostics per bake matched direct
controls bit-for-bit for binary32 quantities; typed JSONL and direct manifests use different decimal
spellings, so the assessor compares declared f32 bits rather than Python f64 spellings. Its regression
test rejects a one-ULP difference. The earlier assessor's false mismatch and original timed collector
are retained in the separate earlier archive; no image or simulation mismatch was concealed.

Integration tests exercise direct compilation, staged orchestration, cache-only rendering, schema-1
and schema-2 validation/playback, sparse and single-frame selection, changed camera/colour/resolution,
recorded-input resolution and cache deletion after image publication. Existing saved-observation and
recorded-input rerun suites pass. An excerpt-clock regression establishes that a selected range starts
playback immediately while retaining original simulation timestamps. Hardware cached-render processes
had CUDA hidden, reported zero solver work and matched fresh direct images; source construction also
excludes `Simulation` and CUDA solver creation from the render path.

Corruption/cancellation tests cover asynchronous error propagation without deadlock, no-overwrite
behaviour, malformed/truncated binary data, metadata changes after opening, missing completion,
orphan files and explicit partial-prefix rendering. A child-only file-size limit forced a real EFBIG
error after 530 accepted steps and 132 committed observations. The CLI returned failure, emitted no
completion marker and retained a prefix that passed independent full canonical validation. This is
process/file-failure evidence, not a power-cut or arbitrary-filesystem durability guarantee.

Retain the raw uncompressed format, one outstanding writer job, sealed validated-frame digest reuse,
existing indexed renderer/encoder and explicit staged orchestration. They establish reusable history
without changing accepted physics or burdening the default one-off path. The deliberate departures
from the review are the 160-byte digest-binding header, independent receipt journal, diagnostic JSONL
and explicit schema-2 sparse image mapping. They are documented storage/compatibility decisions,
not silent changes to existing schema-1 semantics.

Remaining qualification includes cold/storage-constrained devices, longer memory soaks, Windows/macOS
filesystem behaviour and power-loss testing. Compression, automatic in-place repair, direct video,
external particle adapters and solver checkpoints remain future work. A render cache cannot continue
a solver. No new visual feature or numerical retuning is included.

The design makes cached simulation a first-class artefact now. It does not promise that staging
accelerates a one-off export. Retain explicit `cache bake`/`render` and `compile --cache-output`
selection while the default remains direct. A default switch should follow the intended workflow:
repeated views benefit from retaining particle data, while one-off PNG requests should not silently
incur its storage and first-export cost. Cross-platform and crash-durability qualification should
precede any broader default rollout. The measured single-GPU path does not justify concurrent
CUDA/graphics workers, surface reconstruction or unrelated numerical/rendering optimisation.
