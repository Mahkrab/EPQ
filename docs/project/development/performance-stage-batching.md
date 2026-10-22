# Batching dependent CUDA solver passes

The [diagnostic-readback result](/docs/project/development/performance-diagnostic-readback.md)
reduced transfer volume, but each numerical pass still returned separately to the host.
This experiment groups the four passes of each Jacobi calculation and the two passes
of candidate construction/projection. They already share cancellation boundaries.
The [protocol](/docs/project/development/performance-stage-protocol.md) fixes the comparison;
the wider [performance plan](/docs/project/development/performance-plan.md) remains open.

## Dependencies and failures

The same kernels run in the same order on the same private stream. Stream order supplies
the dependency between complete snapshots without requiring the CPU to wait between
launches.<sup><a href="#ref-s012">S012</a></sup> No floating-point expression, neighbour row,
iteration count, timestep, plane order or cancellation poll changes.

Simply sharing one error minimum across a group would be wrong: an earlier particle in
a later stage could replace the actual first failure. Four separate eight-byte slots
retain stage priority before particle/expression priority. Each kernel reads only earlier
completed passes' slots, skips work after failure, and writes only its own slot. This
avoids racing the current pass's atomic error selection. One readback returns the group's
slots, and the host selects the first failed stage. The scratch increase is 24 bytes.

Successful passes leave the all-ones success sentinels untouched. The native owner clears every slot at
the first attempt and after numerical failure; retry still reloads accepted state.
Immediate submission failure stops further launches and drains outstanding work. Uncertain
driver faults poison the resource before any numerical packet is trusted, even if a
previous queued pass had already failed numerically. Batching therefore does not promise
the old intermediate host observation before a subsequent driver fault. Neither case
publishes partial state or permits unsafe reuse.

## Matched PC result

Fresh locked release CUDA builds ran sequentially on the primary RTX 4070/Ryzen 9 7900X
PC. Each variant received an untimed warm-up and five total-only samples, alternating
order. Both used 8,000 particles, 480 refined steps, eight iterations, device zero,
128 lanes and the unchanged observation schedule. No sample was removed.

| Submission boundary | Median solver time | Minimum–maximum |
| --- | --- | --- |
| Individual numerical passes | 2.725 s | 2.656–2.840 s |
| Completed logical groups | 1.928 s | 1.885–1.954 s |

This is **1.413× faster**, or **29.2% less solver time**, for the matched workload.
These are fresh samples, not a ratio assembled from previous campaigns. Required checks,
transfers, resets and completion remain inside solver timing; setup, observation audits,
output and profiling remain separate. The [retained evidence](/docs/project/development/assets/stage-batch-v1/README.md)
identifies the exact dirty source exports and original results. Neither export is a commit.

The separate 8,000-particle traces retain 69,600 kernel launches. Explicit completions
fall from 39,841 to 24,481, and device-to-host copies from 27,840 to 12,480, with the
same 215,247,360 copied bytes. Each invocation has one initial reset. The tracked
allocation peak increases by 24 bytes to 3,069,912 bytes. Gaps fall from 1.872 to
1.168 s in the respective traced windows, but they are not all removable overhead
or primary timings. The trace does not measure complete driver/context memory.

## Verification and remaining limits

Hardware cases exercise all four Jacobi failure positions, candidate and plane failures,
singleton/warp/block/tail sizes and 32/64/128/256 lanes. An early-stage failure at the last
particle takes precedence over a later-stage failure at particle zero. Untouched density,
correction and position buffers demonstrate that dependent kernels skipped their writes.
Clean retries use the same resource after clearing all result slots. Native fault injection
covers every submission position, combined numerical/driver failures, completion, readback,
context restoration, draining and rejection of poisoned resources.

The complete PC release suite passed 255 checks, including opt-in hardware tests, with
the same three automatic-backend CLI failures reproduced in the control. Strict CUDA
Clippy, formatting and native ASan/UBSan checks passed. The local CPU release suite passed
239 checks; the parent experiment suite passed 25. An initial test-build error and an
incorrect control test-target name were corrected before measurement, with their raw
failures retained. No failing test was suppressed.

All seven regression sizes and five fresh serial/CUDA capacity pilots agreed exactly.
Complete capacity trajectories retained the preceding implementation's observations and
warnings. The single diagnostic times at 32,768, 110,592, 262,144 and 512,000 particles
were 3.96, 12.42, 29.60 and 59.52 s, with 75, 259, 300 and 304 warning steps. These
are not paired large-scene speedups, independent density qualification or real-time attainment.

Keep this implementation for its clear matched gain, without treating it as the end of
the performance investigation. Large-scene arithmetic and coordination costs still need
evidence-led assessment; cheaper host coordination does not resolve CFL warnings or
establish physical quality. Actual device-loss recovery, a passing device-memory sanitiser,
other platforms, hosted checks and final evaluation remain unqualified. User edits, installed
applications, ordinary PC checkouts, branches, commits, tags and the parent gitlink are unchanged.

## Implementation checkpoint

After collection, the implementation was committed as Maelstrom
[`5120acfbcb07e94ebefd5957ad8f9afa47888be7`](https://github.com/Mahkrab/Maelstrom/tree/5120acfbcb07e94ebefd5957ad8f9afa47888be7).
All 149 committed files match the assessed candidate's file hashes. The only exported
file omitted from the commit is the unchanged, untracked custom scene, which no benchmark
selected. It remains local rather than being included in the published bundled catalogue.
This is not a fresh measurement of the committed build. Original source manifests,
measurements and limitations remain unchanged; EPQ's gitlink now pins this implementation.
The commit includes both diagnostic readback and logical-stage batching. The intermediate
diagnostic candidate is retained as measured working-tree evidence, not a separate Git checkpoint.

## References used

<a name="ref-s012"></a> **S012** — NVIDIA, *CUDA C++ Programming Guide*, Release 13.2,
§6.2.8.5 and §6.2.8.5.3.
[Source record](/docs/research/sources/012-nvidia-cuda-programming-guide-release-13-2.md).
