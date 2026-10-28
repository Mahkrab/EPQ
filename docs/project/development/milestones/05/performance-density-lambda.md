# CUDA density and lambda traversal fusion

**Retain.** Sharing density and owner-gradient traversal reduced the density/lambda
kernel's GPU time by **17.21% at 8,000 particles and 38.35% at 110,592**. Fresh PC
completed-solver medians improved **2.32% and 12.95%**, respectively. The smaller
workload had one slower pair; every large-scene pair improved. Tested intermediate
values, trajectories and diagnostics remain exact. The
[evidence collection](/docs/project/development/milestones/05/assets/density-lambda-v1/README.md)
retains the prospective protocol, attribution overlay, exploratory pairs, qualification,
all final samples, source identities and independent readers.

## What the profile established

Both repositories were clean at the start: EPQ `1f76097a218266822cdf344c38db75ed128628a8`
and Maelstrom `1e0085926d05c42949bb76b55d177d42a1f8f94f`. The control's 187 hashes match
its complete Git archive and the retained
[numerical-iteration candidate](/docs/project/development/milestones/05/performance-numerical-iterations.md).
It includes the guarded power optimisation; earlier timings are not pooled here.

A fresh ordinary 480-step control trace measured 2.984 ms per step in density/lambda
at 110,592 particles. A separate diagnostic export divided that operation into three
stream-ordered kernels, carrying private per-particle values and errors through existing
scratch. Global error selection remained after the last phase, preserving particle
priority. All warm-up/profile physical and diagnostic records agreed exactly.

| Diagnostic phase, eight invocations per step | 8,000 GPU ms/step | 110,592 GPU ms/step |
| --- | ---: | ---: |
| Density and constraint | 0.154104 | 1.456504 |
| Owner gradient, lower prefix and self square | 0.144205 | 1.097798 |
| Higher-identity squared suffix and final lambda | 0.110448 | 0.512159 |

The first two traversals accounted for about 83% of the larger split cost. They visit
the same ordered membership and repeat displacement/length work and position gathers.
The split uses the same 45 solver registers as control, but adds 16 launches per step
and changes scheduling/cache state. Its intervals identify relative work; their sum is
not an additive estimate of the unsplit kernel. DRAM transactions, cache counters and
achieved occupancy were not measured. The evidence supports removing repeated traversal,
without claiming a pure memory-versus-arithmetic attribution.

## Change and equivalence

Density and owner-gradient accumulation now share one membership traversal and one
checked displacement/round-to-nearest length. Each retains its original addition
sequence. Density inserts self at its identity position; owner gradients exclude self.
Lower-identity squared contributions retain their existing ordered prefix, followed by
the completed owner square and unchanged higher-identity suffix. No independently
summed halves are combined or parallel reduction introduced.

The reciprocal value is calculated early, but its check remains after the complete
density and constraint checks. Separate owner and prefix records defer failures until
their original logical positions: density/constraint, reciprocal, owner checks and
scaling, prefix, then remaining squared/final-lambda checks. Sharing active geometry
removes duplicate calculations/checks of values already known finite; it does not remove
a possible failure condition. The ordinary Spiky wrapper still calculates and checks
its length for callers without that existing geometry.

With `E` directed non-self membership entries and symmetric rows, the higher-identity
suffix contains `E/2` entries. Density/lambda therefore visits `2.5E → 1.5E` non-self
entries: **40% fewer logical visits**. Poly6 contributions, gradients, all dependent
additions and the suffix work remain. This is not a claim of 40% fewer DRAM bytes.
There is no geometry cache across position snapshots, extra allocation, capacity limit,
interface change, launch change or cancellation-boundary change. Jacobi barriers and
host/device acceptance, poisoning, rollback and retry paths remain unchanged.

## Qualification and measurement

One warm-up and two alternating exploratory pairs per size improved all four pairs,
with exact physical records. Those results remain separate. The final 188-file export
changes `native/solver.cu`, its CUDA documentation, a test-module declaration and the
new `src/cuda/density_tests.rs`. A patch reconstructs it from the complete retained
commit. All final live hashes match the frozen measured source; independently compiled
PTX bytes were found inside each executable before collection and source hashes were
checked again afterwards.

New hardware fixtures compare density, constraint, lambda and correction **bits** with
independent CPU equations across empty/tail/dense rows, non-spatial identities, inactive
and coincident neighbours, changed snapshots, storage growth/shrinkage, two rest densities
and all four block sizes. Failure cases check deferred owner/reciprocal priority and
clean retry. The same two fixtures pass in an isolated retained-control export with
only the test file and its declaration added. Existing owner/prefix/suffix overflow,
self-ordering and cancellation fixtures remain enabled; tolerances were not changed.

PC qualification passed 292 ordinary release tests, 29 explicitly selected CUDA library
checks, two boundary and seven integration checks, strict Clippy, formatting and native
control/candidate ASan/UBSan. Local CPU feature isolation passed 290 tests with invalid
CUDA/compiler environment paths. All 50 final regression/warm-up/sample physical and
ordered diagnostic records matched exactly, as did both final profile pairs. Warnings
remain; agreement does not independently qualify fluid quality.

Measurements ran through `ssh pc`: Ryzen 9 7900X, RTX 4070, WSL2, driver 610.88,
CUDA 13.3.73, G++ 13.3.0 and Rust 1.96.0. Locked offline release builds used compute_89
and unchanged precise arithmetic flags. Each request started a new simulation with
device zero, block 128, refinement 4, eight Jacobi iterations and 480 unpaced steps,
without graphics. Each workload received one warm-up per variant and five alternating
pairs, candidate first in the first measured pair. Small runs retained checkpoints
0/1/120/240/480; large runs had none. Enabled effects used XSPH 0.01 and confinement
0.1 m/s.

Primary totals sum completed-step clocks, including validation, preparation, transfers,
launches, completion, cancellation and acceptance. Construction/teardown, audits,
output and collector compression remain separate. Ordinary-binary full-motion profiles
without checkpoints are diagnostic measurements, outside the primary sample medians.

| Workload | Control median (s) | Candidate median (s) | Speedup | Time reduction |
| --- | ---: | ---: | ---: | ---: |
| 8,000 | 1.213748 | 1.185555 | 1.024× | 2.32% |
| 110,592 | 4.963287 | 4.320768 | 1.149× | 12.95% |
| 110,592, both effects | 5.307345 | 4.710485 | 1.127× | 11.25% |

Four small pairs improved by 1.01–2.84%; one regressed by **10.12%**. Its timing is
retained without attributing a cause. Every large pair improved, by 11.97–14.01% with
effects disabled and 10.88–12.40% enabled. Control/candidate ranges were 1.2058–1.2212 /
1.1738–1.3277 s, 4.9009–5.0245 / 4.2673–4.3487 s and 5.2844–5.3808 /
4.7092–4.7192 s. These descriptive observations do not establish statistical significance
or universal performance.

## Final kernel costs and trade-offs

These are mean GPU milliseconds per simulation step, summing eight invocations of each
stage and excluding host gaps.

| Stage | 8,000 control | 8,000 candidate | 110,592 control | 110,592 candidate |
| --- | ---: | ---: | ---: | ---: |
| Active-distance validation | 0.094871 | 0.095316 | 1.063311 | 1.028525 |
| Density/lambda | 0.315372 | 0.261107 | 2.985864 | 1.840895 |
| Correction | 0.301379 | 0.304046 | 1.927908 | 1.929903 |
| Density/mass validation | 0.011264 | 0.011354 | 0.019132 | 0.020119 |
| Candidate positions | 0.010878 | 0.010939 | 0.027152 | 0.026472 |
| Plane projection | 0.015628 | 0.015764 | 0.032923 | 0.035882 |
| **Eight-iteration total** | **0.749392** | **0.698525** | **6.056289** | **4.881796** |

Density/lambda speedups are 1.208× / 1.622×; total iteration kernel time falls
6.79% / 19.39%. Early/late larger lambda costs fall 1.759 → 1.093 and
3.587 → 2.215 ms per step. Savings persist through evolved motion. Changes in other
stages, including projection's small absolute increase, are reported rather than
assigned an unmeasured hardware cause.

Iterations still launch six kernels each: 48 per step. Complete launch counts remain
65 / 69; explicit waits remain 21 per step, downloads 26, steady uploads zero and
transfer bytes 196,480 / 2,709,952. Each full trace has 31,200 / 33,120 launches and
10,080 waits. The reader checks every copy size and kernel order/type against source.
No host/device buffers or reservations were added. Driver-loaded solver registers
increase **45 → 51**, with zero local/shared bytes; other function attributes are
unchanged. This additional register demand is a trade-off, not an achieved-occupancy
measurement.

Compute Sanitizer exited 97 with 16 WDDM debugger/device-support errors despite its
two selected tests completing. No device-memory diagnostic pass follows; racecheck
was not run. Other GPU/compiler/block-size performance, actual device loss and
worst-case cancellation latency remain unqualified. Under the
[assessment policy](/docs/project/development/milestones/05/performance-assessment.md),
exact tested behaviour, substantial consistent large-workload savings and a small
allocation-free change justify retention despite the small-workload variability and
higher register requirement. No commits, branches, tags, gitlinks or installed PC
commands were changed.
