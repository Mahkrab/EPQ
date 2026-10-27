# Cooperative neighbour-row sorting

## Starting point and decision

This continues optimisation on `phase/05-03-optimisation` in both repositories. The control already
contains retained [gradient-prefix reuse](/docs/project/development/milestones/05/performance-gradient-reassessment.md).
It is the uncommitted 179-file tree `a10a3f67d77ebf7d0ac0e8163e2fecd72981cc3f9d6b8851b48491762715d0e1`,
based on Maelstrom [`87145510a9e5d812066138c35f1fac82e4f593b0`](https://github.com/Mahkrab/Maelstrom/tree/87145510a9e5d812066138c35f1fac82e4f593b0).
These results measure the additional sorting change, not an accumulated speedup assembled from
different campaigns. The [protocol](/docs/project/development/milestones/05/performance-cooperative-sort-protocol.md)
and [evidence](/docs/project/development/milestones/05/assets/cooperative-sort-v1/README.md) retain the exact inputs and sources.

**Decision: retain cooperative integer sorting.** Both larger workloads improved in every pair,
the small workload improved in median, and profiling supports removing the measured row-sorting
cost. The extra kernel is included in those comparisons. No neighbour cap or extra device buffer
was introduced, and the previous prefix optimisation stays in place.

## Implementation and trade-off

Previously, each fill thread heapsorted its row in global memory. Filling now retains its existing
geometry and storage checks, then a stream-ordered kernel assigns a complete warp to each row.
A bounded sorting network uses register exchanges for up to 256 identities. Larger rows keep
heapsort, so the threshold selects an implementation rather than limiting the scene.

Padding uses an unused maximum identity and is never written beyond the actual row. Tail rows
exit as complete warps; valid short rows keep all shuffle participants. Sorting owns a separate
native header, while discovery and numerical calculations retain their responsibilities.

Fill and sorting share the existing completion, diagnostic readback and cancellation boundary.
A failed fill prevents sorting invalid rows. Submission failure at either launch drains outstanding
work and invalidates the context through the existing bridge. Sorting changes no floating-point
calculation, fixed membership, reduction order, diagnostic precedence or accepted-state semantics.

## Primary-PC comparison

The PC used its Ryzen 9 7900X and RTX 4070 under WSL2, driver 610.88, CUDA 13.3.73 and Rust 1.96.0.
Separate locked offline release CUDA builds used compute target 89 and precise arithmetic. Each
executable was checked against freshly compiled CUDA code before testing; their kernels differed.

All cases used 480 unpaced steps, refinement 4, eight Jacobi iterations, device zero and block
size 128. Each had one warm-up per variant and five alternating measured pairs. The 8,000-particle
case kept checkpoints 0/1/120/240/480; the larger cases had none. Solver totals exclude output,
rendering and checkpoint audits. The enabled case used XSPH 0.01 and confinement 0.1 m/s.

| Workload | Control median | Candidate median | Less solver time | Faster pairs |
| --- | ---: | ---: | ---: | ---: |
| 8,000 particles, effects disabled | 1.7961 s | 1.7536 s | 2.4% | 4/5 |
| 110,592 particles, effects disabled | 10.4234 s | 9.5052 s | 8.8% | 5/5 |
| 110,592 particles, both effects enabled | 10.7999 s | 9.8033 s | 9.2% | 5/5 |

Whole-command medians also improved. Every sample remains, including the slower small pair.
The enabled larger ranges overlapped despite all five pairs improving; that overlap is variability,
not an independent rejection rule. The disabled and enabled larger cases retained 259 and 181
CFL-warning steps respectively, with exact physical results and diagnostics within each comparison.

Separate disabled-effect profiles put the old combined fill/sort at 1.705 s. Candidate fill took
0.793 s and sorting 0.035 s: together about 51.5% less device time. Early and evolved windows both
improved. The candidate added 480 kernels, giving 99,840, while retaining 24,481 stream completions
and identical transfer counts/bytes. Traced allocation peaks stayed at 59,696,464 bytes.

The driver-loaded shared entry reported 46 registers for control and 45 for candidate, with zero
local/shared allocation in both. These are resource attributes, not achieved occupancy. Other
numerical passes showed no compensating cost increase in these traces. Instrumented timings
support the mechanism; the ordinary pairs own the runtime claim.

## Verification and limits

Both PC release suites passed 292 ordinary tests. Explicit CUDA library runs passed 20 control
and 22 candidate checks, with two application-boundary checks each. Strict Clippy, formatting and
native address/undefined-behaviour sanitiser checks passed. The new hardware cases covered network
boundaries, permuted discovery order, mixed sizes, tail warps, rows beyond 256 entries, invalid
offsets and retry across supported block sizes. Native injected-driver tests covered either launch failing.

Seven bundled trajectories and all paired observations agreed exactly. An independent reader
reconstructed totals, medians, pair ratios, operation windows, correlations and launch dimensions.
Altered timing, physical, sort-duration and launch-dimension inputs were rejected. The updated
reader also passed a read-only audit of the previous prefix campaign. Locally, 68 parent tooling
tests and Rust formatting passed; an initial incorrect trace-offset expectation was corrected
from the explicit launch sequence before collection, with its failure retained separately.

The gains and bounded implementation cost justify retention under the
[assessment policy](/docs/project/development/milestones/05/performance-assessment.md), without a percentage cutoff.
This does not qualify final fluid quality, real-time performance, device-memory sanitisation,
other GPUs or pathological dense-row performance. Correction and host coordination remain costs
to investigate; the optimisation programme is still open.

The measured candidate has 180 file hashes. Reconstructing the control and candidate patches
reproduces both exports. All current runtime/test inputs match; the CUDA guide was clarified after
measurement to describe the separate sort kernel. Changes remain uncommitted, with no tags,
pushes, merges or parent gitlink advancement.
