# Spatial-sort comparison fixed before timing, 27 October 2026

Control: the complete initial dirty tree after the synchronisation change.
Candidate: shared-memory tile sort and global merge passes over full Cell tuples,
with a second context-owned cell buffer. Preserve source manifests, incremental
patch, binary and embedded PTX identities, inputs, command/exit/monotonic timing
records and all raw outputs. Build isolated locked offline release exports with
CUDA and compute_89 on ssh pc. Ordinary checkouts and installed commands stay put.

Qualify ordinary release tests, explicit CUDA library/boundary/integration tests,
strict Clippy, formatting and native ASan/UBSan fault tests. Check full signed tuple
ordering and index ties independently, including power-of-two/tile edges, padding,
growth/shrink, every supported block size and partial submission failure.

Compare seven existing sizes (64..8000) for 480 steps with checkpoints
0,1,120,240,480. Complete-work timing: 8000 with checkpoints, 110592 without,
110592 with XSPH 0.01 and confinement 0.1 m/s without. Use CUDA device 0, block128,
refinement4, eight iterations, 480 unpaced steps, no graphics. One warm-up per
variant and five measured pairs, alternating order (first measured candidate/control).
Sum completed solver steps; retain setup/teardown separately. Require exact canonical
physical and diagnostic records excluding measurements/build revision. Keep failures,
warnings and slower samples; stop mismatches or incomplete work, without replacement.

Sorting-stage benchmark uses separate diagnostic exports of both trees: CUDA events
record immediately before and after operation13 on the existing private stream;
after the existing checked-count completion, read elapsed time and log it. No new
wait is introduced. Also retain monotonic CPU submission time. Verify diagnostic PTX
matches its ordinary counterpart. Give each variant one warm-up and five alternating
pairs for 8000 and 110592, 480 steps, and require the same physical records as the
ordinary runs. Device-event intervals exclude cell generation and counting but include
sorting launches and gaps on that stream. Instrumented whole-step totals are separate
from primary timings; report instrumentation cost and limits.

After timing, trace eight new steps at both sizes using ordinary binaries. Retain
privacy-limited analytical activity rows and reconstruct sorting/total launch counts,
waits and copies from raw APIs and kernel names/correlations. Do not mix profiler
durations into primary samples. Request ceilings are 120s (600s builds/tests, 180s
profiles), with at least4GiB host and2GiB GPU free before measurement. Retain environment
and resource checks. No full-pipeline, cross-device or statistical significance claim.
Make a written assessment from correctness, measured effects, memory and code costs.
