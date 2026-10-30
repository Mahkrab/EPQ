# Snapshot serialisation and provenance hashing

**Retain the fixed-schema streaming hash writer.** With the parallel output pipeline enabled in both binaries, matched 110,592-particle fast-mode compilation improved from 23.615 to 14.482 s, an additional **1.631×** speedup. Reference improved by 2.8%; both 8,000-particle settings improved by about 3%. All twelve measured pairs were faster, with exact snapshot provenance, PNG, pixel-digest and accepted-diagnostic agreement.

This follows the [parallel compilation assessment](/docs/project/development/milestones/05/performance-render-pipeline.md). That campaign remains its historical result; these are fresh control/candidate samples and are not pooled with it. The [evidence receipt](/docs/project/development/milestones/05/assets/snapshot-provenance-v1/README.md) records source identities, executable hashes, inputs, raw observations, tests and reconstruction.

## Diagnosis and implementation choice

The old frame worker called `SnapshotRecord::to_json`, then hashed the returned bytes and discarded the string. Inspection of the locked serde_json 1.0.154 implementation showed direct serialisation into a `Vec` initially reserved to 128 bytes. Pretty indentation, punctuation and escaped field names cause many small writes; decimal particle identities construct temporary strings. The complete document grows to roughly 24–28 MB at 110,592 particles before a separate SHA-256 pass.

There was **no intermediate JSON value tree** in this path. Converting that vector to `String` transfers ownership, and `as_bytes()` borrows it: neither performs a full-document copy. Float formatting was already allocation-free. The retained writer therefore addresses generic schema formatting, temporary identities, document allocation/growth and the separate traversal of a large JSON buffer; it does not claim to remove conversions that were absent. Validation and the snapshot/particle copies remain.

The measured large initial snapshot required **11,833,373 memory-writer operations**, including 10,727,550 writes of at most two bytes. The fixed-schema writer emits the same 23,806,786 bytes in **1,769,479 operations**: 107 versus 16 operations per particle, apart from document framing. These are instrumented in-memory formatter operations, not operating-system writes or a count of non-inlined machine calls. The old path also constructs 33,288,192 temporary particle-identity strings across 301 large frames; the replacement formats quoted decimal identities using the existing stack-based integer formatter. No allocator event trace is claimed.

[The private writer](/Maelstrom/src/workflow/snapshot_json.rs) emits the fixed field names, order and pretty whitespace directly through a 64 KiB `BufWriter` into incremental SHA-256. It uses serde_json’s existing numeric formatter for every integer and finite binary32 value. The full canonical byte stream is still generated and hashed, including all whitespace; a complete JSON document is no longer materialised for frame provenance. `SnapshotRecord::to_json` remains unchanged and supplies an independent derived-serializer oracle. There is no representation, schema, hash algorithm or hash-format change.

The original validation runs before any bytes are written. No public API, dependency or unsafe code was added. The worker’s job/result boundary, initial-frame barrier, ordered exclusive publication, cancellation/join path and numerical rollback are unchanged. Both numerical modes, native sources, rendering and all ten CUDA optimisations agree with the control; both executables contain identical CUDA PTX. The implementation changes four Rust files plus the exporter guide, with no scheduling rewrite.

## Independent saved-state benchmark

The primary Ryzen 9 7900X PC replayed 21 immutable native observations at quarter-second times from each numerical mode and particle count. Loading, byte/hash checks and write-operation attribution ran outside timers. Before timing, all **84 snapshots** matched the original production snapshot SHA-256 and the complete standalone pretty JSON byte sequence. Six algorithms received one warm-up and five measured rounds, with rotated order. Timed results were consumed with `black_box`; every operation regenerated its output.

Values are median milliseconds per snapshot. The exact-capacity vector is a favourable allocation-only diagnostic using a known length; the SHA-only diagnostic uses precomputed bytes. Neither shortcut is used in production.

| Particles / mode | Original JSON + SHA | Exact-capacity Vec + SHA | Generic buffered stream | Fixed-schema stream | Original / fixed |
| --- | ---: | ---: | ---: | ---: | ---: |
| 8,000 / reference | 3.060 | 3.015 | 3.061 | 1.515 | 2.020× |
| 8,000 / fast | 3.062 | 3.022 | 3.058 | 1.520 | 2.014× |
| 110,592 / reference | 57.784 | 42.911 | 42.608 | 20.503 | 2.818× |
| 110,592 / fast | 57.641 | 42.944 | 42.604 | 20.578 | 2.801× |

At the large count, generic streaming/preallocation improved only about 1.35×; retaining the fixed schema improved 2.80–2.82×. Original formatting alone cost about 46.5 ms per snapshot, versus about 10.8 ms for SHA-256 over precomputed bytes. Those isolated clocks explain why streaming alone was insufficient. Small generic streaming was essentially unchanged, while fixed-schema streaming improved about 2.02×. These stage results selected the candidate; complete compilation decided retention.

## Complete 60 Hz compilation

Both binaries were locked, optimised all-feature builds on the primary PC: RTX 4070, WSL2/OpenGL through Mesa D3D12, driver 610.88, Rust 1.96.0 and CUDA 13.3.73. Each request simulated five nominal seconds and produced 301 PNGs at 640×480. The existing reference preset used 2,400 steps/stride 8; fast used 1,200 steps/stride 4. Both retained eight solver iterations, CUDA device 0/block 128, the same scene/camera/effects within each mode, and the parallel encoding pipeline.

Each setting received one warm-up and three alternating pairs (AB, BA, AB, BA including warm-up). No measured invocation overlapped builds, tests, microbenchmarks or audits. Process wall time includes startup/resolution, simulation, rendering, all encoding/hashing/publication, final manifest/CLI output and teardown. Validation and report generation followed the invocation.

| Particles / mode | Control median [range], s | Candidate median [range], s | Ratio of medians | Paired speedups |
| --- | ---: | ---: | ---: | --- |
| 8,000 / reference | 7.601 [7.490–7.615] | 7.363 [7.331–7.457] | 1.032× | 1.034×, 1.004×, 1.037× |
| 8,000 / fast | 5.410 [5.383–5.416] | 5.229 [5.114–5.231] | 1.035× | 1.029×, 1.035×, 1.059× |
| 110,592 / reference | 26.145 [26.092–26.189] | 25.440 [25.438–25.747] | 1.028× | 1.017×, 1.028×, 1.026× |
| 110,592 / fast | 23.615 [23.527–25.369] | 14.482 [14.415–15.805] | 1.631× | 1.632×, 1.631×, 1.605× |

The large fast result is **4.723 → 2.896 wall seconds per simulated second**, a 38.7% elapsed-time reduction. The final pair was slower in both variants (25.369/15.805 s); it remains included. A large reference candidate warm-up was also slower than its control (27.234/26.595 s), and is retained separately as planned. These three-pair observations support the large fast improvement; the smaller percentage gains have greater uncertainty and are not a cross-platform or statistical-significance claim.

## What reached the critical path

These are ordinary compilation stage medians for all 301 frames. Worker hashing includes canonical serialisation and PNG/RGBA hashing. Worker intervals overlap caller intervals and must not be added to reconstruct elapsed time; exact per-sample accounting is retained.

| Particles / mode | Worker hashing, before → after | Output wait, before → after | Solver calls, before → after | Graphics/readback, before → after |
| --- | ---: | ---: | ---: | ---: |
| 8,000 / reference | 1.118 → 0.644 | 0.023 → 0.019 | 4.822 → 4.636 | 0.895 → 0.867 |
| 8,000 / fast | 1.122 → 0.641 | 0.026 → 0.019 | 2.498 → 2.415 | 0.934 → 0.920 |
| 110,592 / reference | 18.242 → 6.706 | 0.629 → 0.057 | 19.499 → 19.425 | 2.897 → 2.855 |
| 110,592 / fast | 18.188 → 6.720 | 8.804 → 0.056 | 8.834 → 8.647 | 2.921 → 2.823 |

At 110,592, actual worker hashing improved about 2.71–2.72× and the fast-mode output wait fell from 8.804 to 0.056 s. That workload had exposed CPU output on its critical path. Reference already hid most CPU output behind roughly 19.5 s of solver work, so its much lower CPU cost produces only a modest wall-time gain. The small workloads likewise had little output waiting to remove. No solver-only speedup is claimed.

For the large reference/fast settings, total process CPU time fell from approximately 41.5/30.9 s to 30.2/19.6 s. The code removes the full per-frame JSON allocation and temporary decimal identities, but no process RSS reduction is inferred from the collector’s cumulative child high-water mark. The new hash buffer itself is bounded to 64 KiB; accepted snapshots, image buffers and the existing queue bounds remain.

## Retention, regressions and qualification

**Retain.** The consistent 1.61–1.63× large fast paired gain removes the demonstrated output bottleneck, with identical provenance and a small, safe implementation. All twelve measured complete pairs improved. The maintenance cost is a schema-specific template: changes to snapshot fields or formatting must also update it. Byte comparisons against the unchanged derived serializer guard that obligation.

Small stage regressions remain visible: PNG time rose by about 0.01–0.02 s over 301 frames; large reference frame/progress publication rose by about 0.01/0.02 s. These small changes do not establish a causal regression in those unchanged paths. The large fast candidate ranged from 14.415 to 15.805 s and its control from 23.527 to 25.369 s. No slow sample was removed or given an unobserved cause. The complete gain, rather than the isolated 2.8× hashing result or a fixed percentage threshold, justifies retention.

Primary-PC qualification passed **401 release tests**, all features and opt-in CUDA/graphics checks, with zero failures and zero ignored, plus strict all-target/all-feature Clippy and formatting. Local checks passed the three new canonical-writer tests under default/render builds, seven software export library checks, strict render Clippy and three parent evidence-reader tests. Coverage includes empty records, signed zero, u64 limits, finite binary32 edge/random patterns, records spanning multiple buffers, invalid records before output, typed writer failure, and the retained cancellation/rollback/publication checks.

Every one of **32 compiled bundles / 9,632 PNGs** passed validation and encoded-file hash checks. Ordered frame hashes, pixel digests, snapshot hashes, full inputs and all accepted diagnostics agree with the original control for each mode. The source trees reconstruct exactly from the recorded base and patches; native/PTX, numerical configuration, shaders, pipeline scheduling and dependency identities remain unchanged. This is PC-local evidence, not hosted verification, new physical qualification, native sanitizer coverage or a performance guarantee for other backends. Neither repository history nor gitlink, installed executable or system setting was changed.
