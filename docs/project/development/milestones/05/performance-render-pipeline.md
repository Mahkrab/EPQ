# Complete compilation pipeline assessment

**Retain the bounded CPU encoding pipeline.** On the primary PC, complete five-second, 60 Hz compilations improved by 1.77× at 8,000 particles in either numerical mode, 1.77× at 110,592 in reference mode, and 2.03× at 110,592 in fast mode. All twelve measured pairs were faster. Numerical inputs, every accepted diagnostic, and every encoded PNG, decoded-pixel digest and snapshot digest agreed exactly within each mode.

The [earlier mode assessment](/docs/project/development/milestones/05/performance-fast-mode.md) remains its original result. This is a new compilation campaign, not a revision of those samples or a new numerical/default policy. The [evidence receipt](/docs/project/development/milestones/05/assets/render-pipeline-v1/README.md) identifies the source trees, executable hashes, requests, raw samples, profiling and verification.

## Measurement boundary and complete results

The PC used a Ryzen 9 7900X, RTX 4070, WSL2, driver 610.88, Rust 1.96.0 and CUDA 13.3.73. Rendering used hardware OpenGL through Mesa D3D12. Each of four settings received one warm-up and three alternating control/candidate pairs (AB, BA, AB, BA including warm-up). Each command computed five nominal simulated seconds and produced 301 PNGs at 640×480. Reference used 2,400 steps/stride 8; fast used 1,200 steps/stride 4, with their existing explicit presets, eight solver iterations, CUDA device 0 and block 128. Scenes, cameras, effects and resolved inputs were matched within each mode.

The monotonic process clock includes CLI resolution, construction, simulation, rendering/readback, PNG encoding, hashing, disk publication, final manifest/CLI output and teardown. Validation ran afterwards. No measured sample overlapped builds, tests, traces or audits. The first small control warm-up overlapped CPU-only Nsight report generation; it is retained and excluded from the measured statistics. Instrumented profiles, short traces and the earlier pilot are separate evidence.

Values below are median complete-command seconds, with the full measured range. Speedup is the ratio of command medians; paired ratios are also exposed to avoid hiding order and variability.

| Particles / mode | Control, s [range] | Candidate, s [range] | Median speedup | Paired speedups | Wall s / simulated s, before → after |
| --- | ---: | ---: | ---: | --- | ---: |
| 8,000 / reference | 13.079 [12.936–13.275] | 7.386 [7.383–7.528] | 1.771× | 1.718×, 1.771×, 1.798× | 2.616 → 1.477 |
| 8,000 / fast | 9.253 [9.247–9.406] | 5.201 [5.132–5.205] | 1.779× | 1.833×, 1.777×, 1.779× | 1.851 → 1.040 |
| 110,592 / reference | 46.177 [46.036–46.232] | 26.133 [26.088–26.225] | 1.767× | 1.772×, 1.762×, 1.761× | 9.235 → 5.227 |
| 110,592 / fast | 47.865 [44.748–50.216] | 23.580 [23.571–25.423] | 2.030× | 1.898×, 2.130×, 1.883× | 9.573 → 4.716 |

The large fast control varied from 44.75 to 50.22 s; its candidate varied from 23.57 to 25.42 s. None was discarded. Its median paired speedup was 1.898×, versus the 2.030× ratio of medians. These are descriptive results from three pairs on one device, not a significance test or cross-platform guarantee.

## Where the gains were lost

The synchronous large path spent about 18 s serialising and hashing frame snapshots and 2.5–2.6 s encoding PNGs. This stopped solver submission and rendering after every scheduled image. The separately instrumented controls generated 8.27 GB of pretty snapshot JSON in reference mode and 8.32 GB in fast mode across 301 frames. JSON generation took 13.85/13.84 s and its SHA-256 took 3.22/3.26 s. The same canonical bytes and hashes are still required and produced.

The CPU creates the sphere mesh once at graphics setup. Repeated CPU work transforms accepted centres, prepares colours and packs buffers; it does not reconstruct a fluid surface. The diagnostic stage totals below cover five seconds at 110,592 particles. GPU durations come from supported graphics timestamp queries. CPU submission/wait intervals include driver work; GPU times overlap CPU intervals and must not be added to them. Query resolution and an extra queue drain deliberately perturb these profiles, so they do not decide retention.

| Diagnostic stage, s | Reference control | Fast control |
| --- | ---: | ---: |
| CPU camera/particle preparation | 0.295 | 0.294 |
| CPU buffer creation/upload submission | 0.072 | 0.067 |
| CPU render command submission | 0.479 | 0.516 |
| GPU draw, including clear and outlines | 1.596 | 4.877 |
| CPU target allocation | 0.411 | 0.284 |
| CPU draw completion/query wait | 1.699 | 5.263 |
| GPU texture copy | 0.126 | 0.179 |
| CPU copy submission | 0.169 | 0.170 |
| CPU transfer/map wait | 0.141 | 0.276 |
| CPU row unpack | 0.017 | 0.016 |
| Snapshot JSON generation | 13.846 | 13.842 |
| Snapshot SHA-256 | 3.223 | 3.261 |

Fast mode’s additional graphics cost was not reproduced by its trajectories alone. The saved-state probe rendered 21 states at matching quarter-second times from each mode and particle count, four times each. All 336 PNG and RGBA hashes matched the corresponding production images. Excluding each state’s first pass, median large GPU draw time was 5.913 ms for either trajectory; texture copy was 0.468/0.470 ms and CPU preparation 1.026/1.002 ms for fast/reference. At 8,000 particles, GPU drawing was about 0.431 ms for either trajectory.

In the interleaved diagnostic compilation, GPU drawing instead averaged 5.30 ms/frame in reference and 16.20 ms/frame in fast mode. Median sampled SM clocks were 2,775 versus 930 MHz. The ordinary final large fast controls had median clocks of 915–1,080 MHz per invocation; all three candidates had 2,790 MHz medians. Removing serial CPU gaps coincides with recovered graphics and coordinated solver time. This supports a cadence/frequency interaction, rather than increased rendering complexity from fast trajectories; it is not a controlled proof of the driver’s power-policy cause. No clocks or system settings were forced.

Texture map completion is necessary before a CPU PNG encoder can consume pixels. The unnecessary ordering was waiting for that frame’s entire PNG/JSON/hash path before admitting later solver work or preparing another image. The retained optimisation removes that ordering. It does not remove numerical validation or CUDA synchronisation. One-second fast control/candidate Nsight prefixes both recorded 16,560 launches, 5,040 stream synchronisations and 1,200 device-to-host copies. These short traces are retained separately and are not ordinary throughput samples or a reliable sample of the longer clocking behaviour.

## Retained implementation and stage timings

[The exporter](/Maelstrom/src/export/mod.rs) retains solver and graphics ownership on its calling thread. One [CPU worker](/Maelstrom/src/export/encoding.rs) owns an immutable snapshot copy and RGBA bytes, encodes the PNG and computes the unchanged hashes. While it works, the caller advances the solver, prepares the next image and reads it back. The caller collects and publishes the preceding frame before submitting another CPU job. The initial image is closed before stepping. Channels admit only one outstanding job/result; there is at most one further prepared image.

Exclusive file publication and progress stay on the caller. Failure retains the published prefix; cancellation joins outstanding CPU work without publishing it. No worker owns CUDA or graphics resources. There is no new dependency, unsafe code, numerical expression, mesh/shader change, sampling change or encoding-policy change. Both numerical modes and all ten CUDA optimisations are unchanged; all native production files and embedded PTX agree between executables.

The following are medians from the ordinary compilation samples, in seconds. After optimisation, PNG/hash durations run on the worker and overlap the export thread; they are **not additive elapsed-time components**. Output wait is the remaining caller wait for that worker. Other intervals and exact per-sample accounting are retained in JSON; component medians need not reconstruct the median command.

### 8,000 particles

| Stage, s | Reference before | Reference after | Fast before | Fast after |
| --- | ---: | ---: | ---: | ---: |
| Setup | 0.529 | 0.539 | 0.530 | 0.524 |
| Solver calls | 6.104 | 4.624 | 2.664 | 2.426 |
| Snapshot capture | 0.017 | 0.018 | 0.009 | 0.009 |
| Frame copies | 0.003 | 0.005 | 0.003 | 0.005 |
| Graphics/readback | 1.252 | 0.873 | 1.100 | 0.884 |
| PNG encoding | 2.214 | 2.239 | 2.090 | 2.070 |
| Frame hashing, including snapshot JSON | 1.493 | 1.116 | 1.469 | 1.112 |
| Frame publication | 0.587 | 0.575 | 0.613 | 0.573 |
| Progress publication | 0.605 | 0.560 | 0.567 | 0.558 |
| Remaining CPU output wait | — | 0.022 | — | 0.031 |

### 110,592 particles

| Stage, s | Reference before | Reference after | Fast before | Fast after |
| --- | ---: | ---: | ---: | ---: |
| Setup | 0.625 | 0.625 | 0.645 | 0.641 |
| Solver calls | 19.413 | 19.493 | 16.874 | 8.811 |
| Snapshot capture | 0.265 | 0.305 | 0.137 | 0.180 |
| Frame copies | 0.046 | 0.091 | 0.094 | 0.093 |
| Graphics/readback | 2.984 | 2.897 | 6.540 | 2.906 |
| PNG encoding | 2.637 | 2.649 | 2.536 | 2.535 |
| Frame hashing, including snapshot JSON | 17.844 | 18.209 | 17.956 | 18.130 |
| Frame publication | 0.726 | 0.754 | 0.755 | 0.866 |
| Progress publication | 0.721 | 0.569 | 0.728 | 0.619 |
| Remaining CPU output wait | — | 0.638 | — | 8.739 |

At 110,592, reference solver time is essentially unchanged (19.41 → 19.49 s), while its formerly sequential CPU output is mostly hidden. Fast solver calls fall from 16.87 to 8.81 s and graphics/readback from 6.54 to 2.91 s. Its remaining 8.74 s output wait exposes the next limit: about 20.66 s of worker PNG/hash work still constrains complete compilation. Fast is now about 1.11× faster than reference for this compiled workload, rather than inheriting its 2.27× solver-only ratio.

## Utilisation, regressions and decision

CPU utilisation below is process user+system CPU seconds divided by wall seconds, expressed as logical-core equivalents. GPU utilisation is the median of each invocation’s mean 200 ms whole-device samples; it is not process occupancy. Linux readings do not observe every Windows activity.

| Particles / mode | CPU cores, before → after | GPU utilisation %, before → after |
| --- | ---: | ---: |
| 8,000 / reference | 0.823 → 1.183 | 32.4 → 38.9 |
| 8,000 / fast | 0.781 → 1.237 | 20.5 → 32.6 |
| 110,592 / reference | 0.896 → 1.594 | 38.8 → 68.5 |
| 110,592 / fast | 0.827 → 1.314 | 41.4 → 37.0 |

Lower sampled utilisation in the large fast candidate does not mean less throughput: it finishes the same work sooner at much higher observed clocks. No achieved occupancy, cache or bandwidth-counter claim is made.

No measured complete pair regressed. Costs remain: one CPU thread, bounded additional frame storage and overlap contention. Large reference worker hashing rose from 17.84 to 18.21 s; its in-compilation solver calls rose by about 0.4%. Large fast frame publication rose by about 0.11 s and frame/snapshot copying has small overhead. Those costs are retained alongside the roughly 20–24 s complete-command saving. The last large fast candidate took 25.42 s rather than 23.57–23.58 s; the raw record is retained without assigning an unobserved cause.

**Retain.** The consistent end-to-end benefit, exact output and small bounded concurrency boundary justify the implementation cost. No speculative GPU, mesh or compression optimisation was retained. CLI and export entry points, bundle schema, frame schedules, PNG bytes and numerical provenance remain compatible. The optional timing profile is explicitly versioned to schema 2 so overlapping worker work cannot be presented as disjoint elapsed time; the three existing `timing_seconds` fields keep their meanings and old bundles remain readable. See [the exporter guide](/Maelstrom/docs/export.md#failures-and-costs).

Qualification passed 398 primary-PC release tests with all features and opt-in hardware/software checks, zero failures and zero ignored, plus strict all-target/all-feature Clippy and formatting. Local checks passed 291 default-feature Rust tests, seven export library and four software export integration checks, strict render Clippy, formatting and four parent evidence-auditor tests. Final collection validated all 32 bundles and 9,632 encoded PNG digests, exact repeated frame/state/diagnostic identities and all timing partitions. Both source exports reconstruct exactly from the recorded base plus patches.

These are primary-PC/WSL OpenGL results, not hosted checks, native Windows/Vulkan performance or a fresh physical-quality qualification. Native sanitiser and exhaustive power tests were not rerun because their source and embedded CUDA code were unchanged. Neither repository history, branch, tag, gitlink, installed binary nor system-wide setting was changed.
