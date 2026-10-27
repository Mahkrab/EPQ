# CUDA numerical iteration performance

**Retain the guarded exponent-four power path.** Fresh primary-PC medians reduced
completed solver time by **11.81% at 8,000 particles and 25.73% at 110,592**, with
unchanged tested physical results and diagnostics. Correction GPU time fell by
50.23% / 64.99%. The [evidence](/docs/project/development/milestones/05/assets/numerical-iterations-v1/README.md)
retains the protocol, unsuccessful alternatives, exhaustive bit comparisons, all
samples, individual iteration profiles and independent readers.

## Profile and implementation decision

The control is the exact 186-file retained
[neighbour-construction candidate](/docs/project/development/milestones/05/performance-neighbour-construction.md).
A fresh full 480-step profile preceded implementation. At 110,592 particles, the
eight active-distance passes totalled 1.025 ms per step, combined density/lambda
2.870 ms, and correction 5.281 ms. Every iteration had similar costs: correction
averaged 0.660 ms per invocation. It remained the largest kernel in both early and
evolved motion. Density and lambda share one kernel; no isolated density-only or
lambda-only time is claimed.

Spatial scheduling, symmetric pressure caching, cooperative correction, coefficient
hoisting, aggregate validation/replay and shared power tables were explored separately.
They produced mixed gains, regressions or insufficient consistent benefit for the larger
workload. The complete coefficient-only campaign, for example, changed medians by
+0.79% / −0.86% / +0.89% improvement at small/large/effects workloads. It is not retained.
All eleven exploratory two-pair cohorts and the earlier complete campaign remain separate
from the final comparison; no sample was replaced or pooled into it.

Artificial pressure uses a host-compatible power approximation with binary64
intermediates. A direct quartic is faster but does **not** always return its binary32
bits: the exhaustive negative control found **354,191 differing inputs** with normal
quartic outputs. The retained implementation therefore keeps that function intact,
apart from renaming it as the reference, and adds a verified special case.

For exponent exactly four, two binary64 multiplications form the quartic. A cast
produces a candidate binary32 result. Its low 29 binary64 fraction bits locate the
binary32 rounding midpoint. Only values farther than `2^21` fraction units
(`1/256` of a binary32 spacing) from that midpoint use the candidate. Inputs near
midpoints, non-positive/non-finite inputs, subnormal/extreme outputs, and all other
exponents call the retained approximation. An earlier floating midpoint calculation
was slower at the larger workload; the integer guard avoids its extra floating work.

The guard margin is qualified exhaustively, rather than justified by an assumed
analytic approximation-error bound. Every one of **2,147,483,648 non-negative binary32
words** was compared bit for bit with the retained function at exponent four, at each
supported block size 32/64/128/256: **zero mismatches**. The guard accepted 529,216,975
words in that enumeration; this is not a measured simulation call-rate fraction.
Tighter unsuccessful floating guards remain failed experiments. Changing the guard,
reference or precise arithmetic flags requires renewed exhaustive qualification.

The PBF equations, binary32 reductions, ordered power results, eight iterations,
fixed neighbour rows, stage barriers, error checks and cancellation polls are unchanged.
All `Checked` calls remain at their original sites and receive identical power bits.
The helper uses only thread-local values and the original immutable fallback tables.
No Rust/CUDA interface, resource ownership or acceptance path changed. Failed/cancelled
attempts still preserve accepted host/device state. The standalone exhaustive CUDA
utility uses the toolkit Runtime API for testing only; the simulator retains its Driver
API implementation and production dependencies.

## Matched measurements

The final 187-file source changes only `native/power.cuh`, `docs/cuda.md` and the new
`native/power_exhaustive.cu`. The manifests and focused patch identify uncommitted
exports based on Maelstrom `87145510a9e5d812066138c35f1fac82e4f593b0`. Fresh PTX
was matched byte for byte inside each corresponding executable, and final live source
hashes match the assessed export.

The primary PC exposed Ryzen 9 7900X, RTX 4070, WSL2, driver 610.88, CUDA 13.3.73,
G++ 13.3.0 and Rust 1.96.0. Locked offline release builds used compute_89 and the
existing precise arithmetic flags. Every request started a new simulation: device
zero, block 128, refinement 4, eight Jacobi iterations, 480 unpaced steps, no graphics,
and the default enabled artificial pressure with exponent four. Each workload had
one warm-up per variant and five alternating measured pairs, candidate first in the
first measured pair. Small runs retained checkpoints 0/1/120/240/480; larger runs
retained final state and ordered diagnostics. Effects used XSPH 0.01 and confinement
0.1 m/s.

Primary totals sum completed-step clocks, including preparation, validation, transfers,
launches, completion, cancellation and acceptance. Construction, teardown, audits and
output remain separate in the raw records. Child wall durations end before collector
compression. Separate ordinary-binary 480-step traces have no checkpoints; their GPU
intervals explain component costs and are not primary timing samples.

| Workload | Control median (s) | Candidate median (s) | Speedup | Time reduction |
| --- | ---: | ---: | ---: | ---: |
| 8,000 | 1.361744 | 1.200884 | 1.134× | 11.81% |
| 110,592 | 6.566285 | 4.877100 | 1.346× | 25.73% |
| 110,592, both effects | 7.014462 | 5.252002 | 1.336× | 25.13% |

Whole-command medians, including startup, teardown, audits and JSON work, were
2.329 → 2.169 s, 7.161 → 5.470 s and 7.579 → 5.832 s, respectively. Construction
medians were 0.213–0.240 s and teardown 0.0406–0.0423 s across these variants;
these remain separate from the completed-step totals.

Every measured pair improved. Paired reductions ranged from 10.83–18.28%,
24.84–26.66% and 24.43–25.23%. Control/candidate ranges were 1.3503–1.4860 /
1.1951–1.2144 s, 6.5642–6.6406 / 4.8685–4.9340 s and 6.9429–7.0194 /
5.2466–5.2696 s. The slower small control sample is retained without assigning a cause.
These descriptive results do not establish statistical significance or other-machine gains.

## Kernels, iterations and memory

The following are mean **GPU milliseconds per simulation step**, summing all eight
invocations of each kernel. They exclude host gaps.

| Stage | 8,000 control | 8,000 candidate | 110,592 control | 110,592 candidate |
| --- | ---: | ---: | ---: | ---: |
| Active-distance validation | 0.094419 | 0.095477 | 1.057335 | 1.057743 |
| Density and lambda | 0.314071 | 0.317306 | 2.961633 | 2.967176 |
| Position correction | 0.609727 | 0.303431 | 5.472228 | 1.915925 |
| Density/mass validation | 0.011166 | 0.011298 | 0.018933 | 0.018862 |
| Candidate positions | 0.010763 | 0.010892 | 0.026659 | 0.026591 |
| Plane projection | 0.015658 | 0.015835 | 0.032069 | 0.031957 |
| **Eight-iteration total** | **1.055805** | **0.754240** | **9.568856** | **6.018255** |

Correction speedups are **2.009× / 2.856×**; total iteration kernel time falls
28.56% / 37.11%. Mean individual iterations span 0.13193–0.13206 →
0.09419–0.09448 ms at 8,000 and 1.19571–1.19655 → 0.75042–0.75489 ms at
110,592. At the larger size, early correction falls 4.324 → 1.561 ms per step;
late correction falls 5.901 → 2.049 ms. Savings persist through evolved motion.
Density/lambda becomes the largest remaining numerical kernel. Small differences
in unchanged stages are visible; a single profile pair does not establish their cause.

Each iteration still launches six kernels: **48 iteration launches per step**.
Complete steps retain **65 / 69 launches**, 21 explicit stream waits, 26 downloads,
no steady uploads and 196,480 / 2,709,952 transfer bytes. Each full trace has
31,200 / 33,120 launches and 10,080 waits. The reader checks kernel order/types
and correlates every copy with its host API and expected size.

No device/host buffers or reservations were added. The original 512 bytes of power
tables remain; there is no extra cache or fixed neighbour capacity. Driver-loaded
solver registers change **44 → 45**, with zero local/shared bytes in both. Other
function resource attributes are unchanged. These are resource requirements, not
achieved occupancy or cache-counter measurements.

## Validation and retention limits

The PC ordinary release suite passed **292 tests**. Separate CUDA runs passed
**27 library, two boundary and seven integration tests**. Strict Clippy, formatting,
control/candidate native ASan/UBSan and local CPU feature isolation (**290 tests**)
passed. Existing independent ordered CPU correction cases cover diverse exponents,
support changes, coincidences and all supported blocks. Diagnostic priority,
numerical failure, cancellation at every poll, predicate panic, rollback and retry
checks remain enabled. All **50** final regression/warm-up/sample physical and
diagnostic records matched exactly; both final profile pairs matched too. Existing
warnings remain and equivalence is not independent fluid-quality qualification.

Compute Sanitizer exited 97 with eight WDDM debugger/device-support errors. Its
selected correction test completed, but **no device-memory diagnostic pass** follows;
racecheck was not run. Other exponents retain the reference but their performance
was not benchmarked. Inputs concentrated in the fallback region can pay guard
overhead. Other GPUs, compiler versions, worst-case cancellation latency and actual
device-loss recovery remain unqualified.

Under the [assessment policy](/docs/project/development/milestones/05/performance-assessment.md),
the complete input-domain equivalence check, unchanged solver lifecycle, consistent
whole-solver savings and small production change justify retention. Earlier negative
outcomes remain negative. No commits, branches, tags, gitlinks, installed PC commands
or unrelated work were changed.
