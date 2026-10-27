# Compilation costs and CUDA block sizes

The [code audit](/docs/project/development/milestones/05/performance-cuda-code-audit.md) identified
missing compilation costs and an untested assumption about CUDA block size. This follow-up adds
an honest timing boundary and compares blocks on the same executable. It implements measurement,
not a new solver algorithm or an asynchronous export pipeline.

## What changed

Compiled manifests now have a versioned `timing_profile`. Disjoint monotonic intervals separate
setup, solver calls, snapshot capture, comparisons, frame particle copying, graphics/readback,
PNG encoding, file publication, hashing and progress updates. The remaining pre-manifest work
is explicit. Integer durations allow accounting to reject component totals that exceed elapsed time.

The boundary ends before manifest construction. Whole-command wall time also includes CLI
resolution, final manifest/catalogue publication and teardown. Graphics timing includes CPU
packing and driver waits; hashing includes validation and JSON serialisation of the portable
snapshot. Existing timing fields keep their meanings, and older bundles remain readable.

The [source receipt and evidence](/docs/project/development/milestones/05/assets/compilation-profile-v1/README.md)
identify both exports from base
[`87145510a9e5d812066138c35f1fac82e4f593b0`](https://github.com/Mahkrab/Maelstrom/tree/87145510a9e5d812066138c35f1fac82e4f593b0).
The candidate changes only export timing, its tests and guide. Reconstruction checked all 181
candidate files. Independent native compilation and embedded-code checks found identical CUDA PTX.
No numerical expressions, iteration order, default block size or dependencies changed.

## Primary-PC measurements

The [prospective protocol](/docs/project/development/milestones/05/performance-compilation-profile-protocol.md)
fixes 480 unpaced steps, timestep refinement 4 and eight iterations. The PC used a Ryzen 9 7900X,
RTX 4070, WSL2, driver 610.88, CUDA 13.3.73 and Rust 1.96.0. Each setting received one warm-up and
three measured requests, with rotated order. These diagnostic samples are not pooled with older
campaigns or final evaluation results.

Median completed-solver totals, in seconds, were:

| Particles and effects | Block 32 | Block 64 | Block 128 | Block 256 |
| --- | ---: | ---: | ---: | ---: |
| 8,000, disabled | 1.615 | 1.619 | 1.648 | 1.638 |
| 110,592, disabled | 8.465 | 9.098 | 8.901 | 8.532 |
| 110,592, enabled | 8.922 | 9.405 | 9.255 | 8.786 |

In block order, small-case ranges were 1.603–1.618, 1.592–1.624, 1.638–1.658 and 1.623–1.746 s.
The large disabled-effect ranges were 8.458–8.474, 9.074–9.138, 8.884–8.921 and
8.464–8.642 s respectively. Enabled ranges were 8.806–8.942, 9.397–9.450, 9.190–9.288 and
8.773–8.851 s. The archive retains every small-case range and sample. Block 32 was best for the
small and large disabled-effect requests; 256 was best with effects. Increasing block size is
not a universal improvement. Keep the default 128 unchanged in this measurement step; a default
revision needs broader workload evidence. Roughly one simulated second still costs over eight
solver seconds, so the real-time ambition remains unmet.

Compilation used D3D12 hardware graphics on the RTX 4070 through Mesa's GL backend, without
software fallback. At block 128, the median component costs were:

| Cost, seconds | Stride 1: 481 images | Stride 4: 121 images |
| --- | ---: | ---: |
| Whole command | 92.864 | 22.733 |
| Solver calls | 31.865 | 9.142 |
| Graphics/readback | 15.712 | 1.398 |
| PNG encoding | 10.886 | 2.749 |
| Frame hashes and snapshot JSON | 29.675 | 7.504 |
| Frame publication | 1.409 | 0.370 |
| Progress work | 1.428 | 0.291 |
| Snapshot capture | 0.078 | 0.068 |

Component medians need not sum to the median command total. Setup, particle copying, comparison,
remainder and work outside the export boundary are retained separately. Whole-command ranges
were 92.250–94.673 and 22.724–27.707 s. At block 256, medians were 93.191 and 22.271 s, with
ranges 92.103–93.707 and 22.202–28.618 s. All settings computed the same 480 steps.

The unchanged block-128/stride-1 control took a median 94.218 s, range 92.042–95.004 s. The
instrumented build shows no material slowdown distinguishable from these samples; its slightly
lower median is not an optimisation claim. Surrounding Linux/GPU readings do not establish what
other Windows applications were doing.

A subsequent driver-JIT query reported 45 registers per thread, zero local/static shared memory
and 512 constant bytes. Active-block resource bounds were 24/20/10/5 per multiprocessor for
32/64/128/256 threads. These are limits, not achieved occupancy or cache measurements; they do
not select the fastest block by themselves. The follow-up was declared before capture.

## Decision and verification

Retain the timing implementation. It identifies a sizeable synchronous JSON/hash and PNG path,
while snapshot copies and progress publication are much smaller. Investigate bounded CPU frame
preparation overlap separately from solver throughput. Solver calls and graphics/readback also
became substantially more expensive with every-step images; these measurements expose that
interaction but do not attribute it to GPU clocks, context switching or WSL. A focused compile
trace is needed before assigning that cause.

For the solver, next scope device-resident accepted/working state with larger checked submission
segments, and a separate neighbour-indexing comparison. Continue bounded correction-arithmetic
work alongside them. A faster image pipeline cannot establish real-time fluid simulation.

The PC release suite passed 314 ordinary tests, 22 explicit CUDA library checks, two CUDA
application checks, four software export checks and four library export checks, plus strict
Clippy and formatting. Local verification passed 76 parent tests and the focused Rust timing
test. The independent reader reconstructed raw totals, physical agreement and common-frame
hashes; six deliberately altered timing, physical, workload and frame claims were rejected.
All 20 compiled bundles passed integrity validation. This is local/primary-PC evidence, with
no hosted check or new native-sanitiser qualification. The large disabled/enabled cases retained
259/181 warning-bearing steps; completion is not physical-quality approval. Both Git histories, branches, tags and the gitlink remain
unchanged; the implementation and evidence are uncommitted.
