# Hierarchical CUDA spatial sorting

This replaces the global bitonic network with shared-memory tile sorting and parallel
merging. The [evidence](/docs/project/development/milestones/05/assets/spatial-merge-sort-v1/README.md)
retains the prospective protocol, source delta, complete observations and independent audit.

## Choice and correctness

The existing key is three signed 64-bit cell coordinates followed by the particle index.
The replacement compares that complete tuple directly. It introduces no coordinate packing,
Morton order, hashing, range restriction or precision change. I considered CUB but chose a
comparator-based merge implementation that fits the existing Driver API, isolated context and
embedded PTX module without adding library host dispatch or CUDA Runtime linkage. This is an
integration decision, not a measured claim against CUB.

Each block first sorts its tile in shared memory using a local bitonic network. Later launches
merge adjacent runs. Each output tile finds its two merge-path partitions, loads the resulting
left/right slices into shared memory, then assigns each input a distinct output rank. Lower-bound
and upper-bound tie rules take the left run first even for identical padding sentinels. The
particle-index tie-breaker and all signed coordinates retain the original ordering.

Two cell buffers share one context-owned allocation. The initial output half depends on merge
parity, so the last merge lands at the existing public cell-array address without a copy-back.
A separate sorting entry point confines shared-memory storage to sorting. Cell generation,
neighbour search, membership rows, arithmetic, diagnostics and cancellation polls are unchanged.
Stream dependencies and completion/poisoning rules remain those of the preceding
[synchronisation change](/docs/project/development/milestones/05/performance-stream-synchronisation.md).
Every immediate submission failure stops and drains the batch; partial scratch cannot become
accepted state. No extra per-step allocation, host transfer or synchronisation is introduced.

At block size 128, sorting uses one tile launch plus six merges at 8,000 particles, and one
plus ten at 110,592. This replaces 91 and 153 global bitonic passes. The implementation retains
full 32-byte records and performs binary partition searches; it does not claim optimal work
complexity or the performance of a specialised radix representation. The extra buffer costs
32 bytes per padded entry: 256 KiB and 4 MiB at the measured sizes. Memory exhaustion follows
the existing retry policy; no maximum-size or peak-memory qualification follows.

## Measurement and verification

The 182-file control exactly matches the preceding synchronisation candidate. The 184-file
candidate changes nine files, including two additions. Both are uncommitted exports based on
Maelstrom `87145510a9e5d812066138c35f1fac82e4f593b0` plus retained patches. Separate targets,
source/binary hashes and freshly compiled embedded PTX checks identify all ordinary and
diagnostic builds. Diagnostic PTX matches its ordinary counterpart; the two algorithms have
different PTX as expected.

Measurements ran on the primary PC: Ryzen 9 7900X, RTX 4070, WSL2, driver 610.88,
CUDA 13.3.73, G++ 13.3.0 and Rust 1.96.0. Locked offline release builds used compute_89.
Requests started new simulations: device zero, block 128, refinement 4, eight iterations,
480 unpaced steps and no graphics. Each comparison used one warm-up per variant and five
alternating pairs, candidate first in the first measured pair. No samples were replaced.
Only the 8,000-particle runs retained checkpoints 0/1/120/240/480; large runs kept final state
and diagnostics. Enabled effects used XSPH 0.01 and confinement 0.1 m/s.

Ordinary totals sum completed solver steps, including validation, transfers, submission,
completion and acceptance. Construction, teardown, audits and output remain separate.

| Workload | Control solver (s) | Candidate solver (s) | Speedup | Time reduction |
| --- | ---: | ---: | ---: | ---: |
| 8,000, effects disabled | 1.600256 | 1.495986 | 1.070× | 6.52% |
| 110,592, effects disabled | 8.818004 | 8.215197 | 1.073× | 6.84% |
| 110,592, both effects enabled | 9.018209 | 8.548743 | 1.055× | 5.21% |

Every measured pair improved. Control/candidate ranges were 1.5870–1.7406 / 1.4817–1.5032 s,
8.6260–8.8476 / 8.2056–8.2624 s and 8.9908–9.1572 / 8.4483–8.6387 s. Paired reductions
ranged from 5.74–14.11%, 4.40–7.15% and 4.15–7.53%. The slower small control remains
in the evidence; no cause is assigned. Five pairs on one PC do not establish a universal
speedup or statistical significance.

Separate diagnostic exports placed CUDA events immediately around sorting on the same stream.
Elapsed time was read after the existing checked-count completion, without a new wait. These
GPU intervals exclude cell generation and counting, but include sorting launch gaps. Values
below are medians of summed event durations over 480 steps, separate from ordinary totals.

| Particles | Control sort (s) | Candidate sort (s) | Sort speedup | Sort launches per step |
| ---: | ---: | ---: | ---: | ---: |
| 8,000 | 0.120436 | 0.021241 | 5.67× | 91 → 7 |
| 110,592 | 0.619705 | 0.105661 | 5.87× | 153 → 11 |

Sorting ranges were 0.11981–0.12163 / 0.021199–0.021287 s and 0.61764–0.62110 /
0.105481–0.105769 s. Median CPU submission times fell from 0.072619 to 0.005719 s
(12.70×) and 0.127929 to 0.008900 s (14.37×). Submission overlaps the GPU interval;
these durations must not be added. Diagnostic whole-solver medians differed from ordinary
ones by +0.55%/+0.90% at 8,000 and −0.81%/+0.33% at 110,592 (control/candidate).
Later collection and variation prevent treating those differences as isolated instrumentation
costs. Raw collector `wall_s` also includes output compression; it is not invocation-only time
and supplies no reported performance comparison.

Eight-step traces independently confirmed 1,168 → 496 total launches at 8,000 and
1,664 → 528 at 110,592. Sorting accounts for the entire difference: 728 → 56 and
1,224 → 88 launches, reductions of 92.3% and 92.8%. Both traces retain 440 non-sort
launches, 168 stream waits and 219 transfers. Driver-loaded numerical-kernel resources
remain 45 registers, zero local and zero shared bytes. The sorting entry uses 28 registers,
zero local and 8,208 shared bytes. These are resource attributes, not achieved occupancy.

Verification passed 292 ordinary PC release tests, 24 explicitly selected CUDA library checks,
nine boundary/integration checks, strict Clippy, formatting and control/candidate native
ASan/UBSan tests. Fourteen local CPU-library tests passed with invalid CUDA/compiler paths,
checking the disabled feature's build isolation. New tests compare raw signed tuples with an
independent CPU oracle, retain the old individual-pass reference, cover padding and tile
boundaries, exercise reused storage and inject failure at each sort submission. Existing tests
retain cancellation, retry, diagnostic priority and accepted-state checks.

Seven regression pairs, 36 ordinary workload records and 24 diagnostic records agreed exactly.
An independent reader reconstructed all 74 physical records, both timing boundaries and
trace counts. Compute Sanitizer exited 97 with eight WDDM debugger/device-support errors;
the test itself completed, but no device-memory diagnostic pass follows. Racecheck was not
run after that failure. Actual device-loss recovery remains unqualified.

## Assessment

**Retain.** Exact tested ordering and physical/diagnostic agreement, roughly 5.8× faster sorting
and consistent 5–7% whole-solver savings justify the focused merge implementation and extra
linear scratch storage. Its costs are a second cell buffer, shared-memory tile/partition logic
and one additional module entry point. Full records and comparison searches remain; CUB,
alternative encodings, other block-size performance and other GPUs were not benchmarked.
No numerical variant, dependency or broader neighbour-search redesign was introduced. Both
repositories remain uncommitted, with branches, tags and gitlink unchanged.
