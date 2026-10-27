# Compact CUDA state observations

**Retain.** This change replaces repeated full-array CFL/bounds observations and the host
neighbour-prefix round trip with compact summaries and device-side checked prefixes. Fresh
primary-PC measurements reduced steady-step transfer bytes by about **61.7%** and completed
solver time by **3.56–5.55%**, preserving the tested physical and diagnostic records.
The [evidence](/docs/project/development/milestones/05/assets/state-transfers-v1/README.md)
retains the prospective protocol, source identities, all samples, raw trace rows and audit.

## Lifecycle and correctness

The starting implementation already kept accepted vectors and planes on device. It still
returned acceleration velocities and predictions for host CFL/bounds calculations, downloaded
row counts and uploaded their prefixes, then returned final vectors for snapshot acceptance.
The earlier [coordination study](/docs/project/development/milestones/05/performance-coordination.md)
measured modest standalone arithmetic costs and larger surrounding copy/packing costs. Here,
observations are fused with existing stages rather than adding separate reduction launches.

Acceleration and prediction now emit one 32-byte summary per block into correction scratch.
Per-particle CFL lengths retain the ordered binary32 dot product and round-to-nearest square
root; only finite maxima are reduced. Acceleration errors and CFL errors have separate slots,
so an acceleration failure at a later particle still precedes an earlier CFL overflow. Host
observation faults retain precedence over CFL interpretation. The shared host limit/warning
calculation remains unchanged. Coordinate extrema determine the same power-of-two width and
unsafe-diagonal checks; no ordered floating-point sum is parallelised or approximated.

Neighbour counting queues block scans, a scan of block totals and carry addition on the same
stream. Counts, the initial zero and deterministic first-error selection are checked before
using offsets. The validated dimension/row bounds ensure u64 sums fit; host byte-size and
allocation checks remain. Only the final eight-byte total returns. Offsets stay on device.
The scan reuses correction scratch after the bounds summary has been consumed, and Jacobi
subsequently overwrites that scratch. There is no additional device scratch allocation at the benchmark
sizes; empty/tiny cases reserve at least 32 scratch bytes.

All existing stage cancellation polls and completion boundaries remain. Failed or cancelled
attempts retain accepted device vectors and the host snapshot. Allocation exhaustion remains
retryable; other uncertain driver faults still poison the resource. Simulation still validates the final snapshot and passes its last cancellation poll before
native promotion, which rejects pending or numerically failed attempts. New bounded offset reads
validate the range before forming the device address.

Final position/velocity downloads remain. `snapshot()` borrows an infallible immutable host
snapshot, used by workflows, the worker and presentation. Removing those downloads would need
a broader fallible materialisation/ownership design. This change preserves every host identity,
finiteness and plane check, snapshot freshness and thread-local CUDA ownership. It introduces
no renderer dependency on device scratch and does not claim fully device-owned execution.

## Measurements

The control matches the 184-file
[spatial-sort candidate](/docs/project/development/milestones/05/assets/spatial-merge-sort-v1/README.md).
The measured candidate has 186 files; separate targets, source/binary/input hashes and fresh
embedded-PTX checks identify both uncommitted exports. The final tree additionally clarifies
one header comment; reconstruction and a fresh byte-identical PTX comparison record that change.
No earlier campaign is pooled with this comparison.

The primary PC exposed Ryzen 9 7900X, RTX 4070, WSL2, driver 610.88, CUDA 13.3.73,
G++ 13.3.0 and Rust 1.96.0. Locked offline release builds used compute_89 and precise CUDA
arithmetic. Each request started a new simulation: device zero, block 128, refinement 4,
eight iterations and 480 unpaced steps without graphics. Each workload had one warm-up per
variant and five alternating measured pairs, candidate first in the first measured pair.
The 8,000-particle case retained checkpoints 0/1/120/240/480; larger cases retained final state
and diagnostics. Enabled effects used XSPH 0.01 and confinement 0.1 m/s.

Totals sum internal completed solver-step clocks, including validation, preparation, transfers,
submission, completion and acceptance. Construction, teardown, audits, output and compression
remain separate; profiler durations do not enter these samples.

| Workload | Control median (s) | Candidate median (s) | Speedup | Time reduction |
| --- | ---: | ---: | ---: | ---: |
| 8,000, effects disabled | 1.445243 | 1.393821 | 1.037× | 3.56% |
| 110,592, effects disabled | 7.897792 | 7.487536 | 1.055× | 5.19% |
| 110,592, both effects enabled | 8.319625 | 7.857580 | 1.059× | 5.55% |

Every measured pair improved. Control/candidate ranges were 1.4172–1.5206 / 1.3728–1.3983 s,
7.8274–8.0415 / 7.4033–7.5334 s and 8.2003–8.3318 / 7.6978–7.9277 s. Paired reductions
ranged from 2.31–8.34%, 3.76–7.49% and 3.95–7.47%. Slower control observations were retained
without assigning a cause. Five pairs on one machine do not establish universal performance
or statistical significance.

Separate eight-step traces checked every copy against its host API correlation and expected
stage order. The following values describe one steady, non-empty step, excluding first uploads:

| Particles | Control bytes, both directions | Candidate bytes | Byte reduction | Kernel launches |
| ---: | ---: | ---: | ---: | ---: |
| 8,000 | 512,440 | 196,480 | 61.66% | 62 → 65 |
| 110,592 | 7,078,328 | 2,709,952 | 61.71% | 66 → 69 |

Each step changes from **26 downloads plus one upload to 26 downloads and no upload**.
Explicit stream synchronisations remain **21 per step**. Small diagnostic reads still dominate
call counts. With `N` particles and `B = ceil(N/128)`, bytes change from `64N + 440` to
`24N + 64B + 448`. The two final vector downloads remain `24N` bytes and account for about
98% of remaining traffic. Counts are not a claim that implicit transfer waits disappeared.

Across each eight-step trace, downloads remain 208 and uploads fall from 11 to three;
the three initial uploads are unchanged at 192,096 / 2,654,304 bytes for the two sizes.
Total transferred bytes were 4,291,616 → 1,763,936 and 59,280,928 → 24,333,920.
Each trace retained 168 stream waits and added 24 scan launches. The numerical kernel retains
45 registers and zero local/shared bytes; observation and prefix entries use 8,192 / 2,048
shared bytes with no local storage. Resource attributes do not establish achieved occupancy.

## Verification and assessment limits

Verification passed 292 ordinary PC release tests, 26 explicitly selected CUDA library checks,
nine boundary/integration checks, strict Clippy, formatting and native ASan/UBSan faults.
The CPU-only release suite passed 290 tests with deliberately invalid CUDA/compiler paths.
New GPU tests independently check exact CFL maxima, scalar extremes, extrema, stage priority,
empty/tail cases, malformed row counts, complete u64 prefix arrays through 110,592 rows,
all four supported blocks and reused storage. Native checks cover offset bounds and failures
at each count/scan submission, completion, readback and context restoration.

All seven regression pairs and 36 warm-up/measured records matched physical state, CFL values,
warning schedules and diagnostics exactly. The independent reader reconstructed all 50 records,
medians, paired effects and every transfer count/size. Compute Sanitizer exited 97 with 16
WDDM debugger/device-support errors; its two tests completed but no device-memory diagnostic
pass follows. Racecheck was not run after that failure. Actual device-loss recovery and
worst-case cancellation latency remain unqualified.

The consistent measured savings and substantially smaller observations justify the fused
reductions, scan kernels and narrow FFI changes. Costs include three extra launches per step,
shared-memory reduction/scan logic and more native diagnostic modes. The final host mirror and
21 completion boundaries remain architectural limits. No dependency, numerical variant, lazy
snapshot or broader application redesign was introduced. Other GPUs and block-size performance
were not benchmarked. Both repositories remain uncommitted; branches, tags and gitlink are unchanged.
