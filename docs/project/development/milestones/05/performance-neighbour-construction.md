# CUDA neighbour construction in spatial order

**Retain.** Assigning count/fill lanes in existing spatial order reduced neighbour GPU
kernel time by **23.93% at 8,000 particles and 59.42% at 110,592**. Fresh primary-PC
completed-solver medians improved by **3.93% and 13.55%**, respectively. Exact tested
membership, ordering, physical results and diagnostics were preserved. The smaller
workload had two slower pairs; its improvement is less consistent than the larger result.
The [evidence collection](/docs/project/development/milestones/05/assets/neighbour-construction-v1/README.md)
contains the prospective protocol, preliminary investigation, final samples, raw activity,
source identities and independent reader.

## Choosing the change

The control is the exact 186-file final source from the
[state-transfer assessment](/docs/project/development/milestones/05/performance-state-transfers.md),
including spatial merge sorting, device prefixes and cooperative identity row sorting.
Before implementation, separate 480-step control profiles measured cell generation,
spatial sorting, count, each prefix kernel, fill and row sorting. At 110,592 particles,
count/fill averaged 3.118 ms per step, compared with 0.070 ms for row sorting and
0.008 ms for prefixes. Count/fill grew from 1.481 ms in steps 1–120 to 4.160 ms in
steps 241–480. This favoured improving traversal over another ordering or scan rewrite.

Both passes previously assigned lanes by particle identity. After motion, adjacent
identities can visit unrelated cells and traverse different candidate runs. The trial
instead used the already sorted cell array to select each lane's owner. One warm-up
and two exploratory alternating pairs per size produced exact physical records and
improvements in all four pairs. Those observations remain separate from final samples.

The retained change is one owner-index selection in the CUDA dispatcher, with supporting
tests and documentation. Count and fill alone read `cells[lane].index`; particle arrays,
offsets, errors and final rows stay indexed by identity. Sorted valid cells are a
permutation of every owner exactly once, so each output still has one writer. Each
owner retains the same nine column searches, candidate visitation, checked binary32
distances and strict support test. Warp row sorting and its unbounded dense-row heapsort
fallback are unchanged. No neighbour capacity limit or approximate search was added.

Spatial scheduling is intended to improve cell/position reuse and traversal coherence
within warps. Count/fill timings support its usefulness; cache transactions, divergence
counters and achieved occupancy were not measured. Offset/error stores now follow spatial
scheduling and can be less contiguous. Keeping the existing two traversals avoids a new
candidate cache, allocation strategy or error-ordering mechanism. This narrow change
provides a substantial measured large-scene benefit without those costs.

## Measurement boundaries

Both uncommitted exports are based on Maelstrom
`87145510a9e5d812066138c35f1fac82e4f593b0`. The candidate changes three files; the
live tree matches all 186 frozen candidate hashes. Source manifests, the patch, binary
and input hashes, and fresh byte-matched embedded PTX identify the measured builds.
No earlier campaign is pooled with these results.

Measurements ran through `ssh pc` on Ryzen 9 7900X and RTX 4070 under WSL2, driver
610.88, CUDA 13.3.73, G++ 13.3.0 and Rust 1.96.0. Locked offline release builds used
compute_89 and precise CUDA arithmetic. Requests started new simulations with device
zero, block 128, timestep refinement 4, eight Jacobi iterations and 480 unpaced steps,
without graphics. Each workload received one warm-up per variant and five alternating
pairs, candidate first in the first measured pair. The 8,000-particle run retained
checkpoints 0/1/120/240/480; larger runs retained final results and diagnostics. The effects
case enabled XSPH 0.01 and confinement 0.1 m/s.

Primary totals sum internal completed-step clocks, including validation, preparation,
transfers, launches, completion, cancellation polls and acceptance. Construction,
teardown, audits, output and collector compression are separate. Independent ordinary
binary profiles cover all 480 steps without checkpoints; profiler timings are diagnostic
and do not enter the primary sample medians.

## Neighbour pipeline

These are mean **GPU milliseconds per step** from the final separate profile pairs.
Kernel intervals exclude host gaps and do not constitute an uninstrumented pipeline timer.

| Stage | 8,000 control | 8,000 candidate | 110,592 control | 110,592 candidate |
| --- | ---: | ---: | ---: | ---: |
| Cell generation | 0.003073 | 0.003084 | 0.017344 | 0.017651 |
| Spatial sort | 0.040594 | 0.040645 | 0.211216 | 0.215071 |
| Count and cell lookup | 0.184237 | 0.130430 | 1.508674 | 0.508730 |
| Prefix, three kernels | 0.004477 | 0.004487 | 0.007670 | 0.007788 |
| Fill and cell lookup | 0.194354 | 0.144522 | 1.600406 | 0.566697 |
| Identity row sort | 0.006277 | 0.006216 | 0.069508 | 0.069722 |
| Total kernel intervals | **0.433012** | **0.329384** | **3.414820** | **1.385659** |

The pipeline kernel speedups are **1.315× / 2.464×**. The separately defined device
span from cell-generation start to row-sort finish, including intervening gaps, fell
from 0.569732 to 0.488224 ms and 3.558313 to 1.524704 ms. It excludes subsequent host
diagnostic interpretation. At 110,592, count/fill fell from 1.469 to 0.914 ms early and
4.151 to 1.177 ms late. Savings therefore persist through evolved motion. Small changes
in unchanged stages are visible in the table; one trace pair cannot establish their cause.

## Complete solver and costs

| Workload | Control median (s) | Candidate median (s) | Speedup | Time reduction |
| --- | ---: | ---: | ---: | ---: |
| 8,000 | 1.401587 | 1.346481 | 1.041× | 3.93% |
| 110,592 | 7.557370 | 6.533286 | 1.157× | 13.55% |
| 110,592, both effects | 7.873287 | 6.880991 | 1.144× | 12.60% |

Control/candidate ranges were 1.3624–1.4078 / 1.3127–1.4259 s,
7.4188–7.5793 / 6.3779–6.5878 s, and 7.7855–7.8851 / 6.8387–6.9191 s.
All ten large-scene pairs improved by 11.22–15.61%. Three small pairs improved by
3.64–4.36%; two regressed by 1.71% and 0.14%. All samples are retained without
replacement or an inferred explanation for variability. These are descriptive results
on one machine, not statistical significance or universal speedup claims.

Per-step neighbour launches remain **14 / 18**, including cell generation and spatial
sorting; complete launches remain **65 / 69**. Each full trace has 31,200 / 33,120
launches and 10,080 explicit stream waits, exactly as before. Steady steps retain
21 waits, 26 downloads, no uploads and 196,480 / 2,709,952 transfer bytes. Initial
three uploads remain separate. The independent reader joins device activity to host
API correlations and validates every transfer against the source schedule.

There are no new device or host buffers, reservations or transfers. Existing cell
storage is `64 * padded` bytes: 524,288 / 8,388,608 bytes at these sizes. Offsets use
64,008 / 884,744 bytes; indices use `4 * entries`, with unchanged geometric allocation
slack. Prefix work reuses existing correction scratch. Exact counts imply identical
capacity trajectories; no new peak-memory measurement is claimed. Dense membership
can still require quadratic space. The driver-loaded solver reports 45 → 44 registers,
zero local/shared storage; the other kernel resource attributes are unchanged. These
attributes do not establish achieved occupancy.

## Correctness and limits

The PC ordinary release suite passed 292 tests, with 33 explicitly selected hardware
checks ignored there. Separate CUDA runs passed 27 library, two boundary and seven
integration tests. Strict Clippy, formatting and control/candidate native ASan/UBSan
checks passed. Local CPU-only feature isolation passed 290 tests with deliberately
invalid CUDA/compiler environment paths.

New tests permute identity/spatial order across block tails, reuse and all four supported
block sizes, comparing rows with independent CPU brute-force/grid oracles. An extreme
domain verifies lowest-identity diagnostic selection despite reversed spatial scheduling,
failed acceptance and clean retry. Existing tests cover strict support edges, duplicate
positions, dense rows beyond the warp sorter, malformed offsets, numerical error
precedence, every cancellation boundary, predicate panic, rollback and recovery paths.
All 50 regression/warm-up/sample physical records matched exactly, including ordered
diagnostics; both final profile pairs matched too. Existing warnings remain and this
agreement does not independently qualify fluid quality.

Compute Sanitizer exited 97 with eight WDDM debugger/device-support errors. Its selected
test completed, but this is **not a device-memory diagnostic pass**; racecheck was not run.
Actual device loss, worst-case cancellation latency, other GPU architectures and performance
at other block sizes remain unqualified. Under the
[assessment policy](/docs/project/development/milestones/05/performance-assessment.md),
consistent large-workload savings, supporting stage evidence, unchanged storage and a
small implementation justify retention despite the small-workload variability.
Unrelated work, Git histories, branches, tags, gitlinks and installed PC commands were preserved.
