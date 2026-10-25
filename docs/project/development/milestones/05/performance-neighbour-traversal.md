# Neighbour traversal in evolved motion

This investigation follows the [host-acceptance work](/docs/project/development/milestones/05/performance-host-acceptance.md)
and addresses the next priority in the [performance plan](/docs/project/development/milestones/05/performance-plan.md).
It changes cell lookup work without changing the numerical experiment. The existing
graphics repair is shared by the comparison sources and is absent from headless timings.

## What needed improving

A fresh 110,592-particle control trace confirmed that discovery becomes more expensive
as the fluid moves. Counting rose from 0.814 ms per step over steps 1–120 to 2.385 ms
over steps 241–480. Filling and sorting rose from 2.020 to 4.514 ms. These are device
kernel intervals, separate from completed solver-step and invocation timings.

The cells are sorted by x, y, z and identity. The original search performs a lower
bound for each of the 27 adjacent cells. Three consecutive z-cells share a column,
so it appeared possible to reuse their lookup. Both trials kept checked distances,
strict support, candidate visitation order, identity-sorted rows, allocation and
all Jacobi arithmetic unchanged. The [protocol](/docs/project/development/milestones/05/performance-neighbour-bands-protocol.md)
records the initial trial and the separately declared follow-up.

## Why the first version did not stay

The first candidate merged each column's three z-cells into one continuous scan.
It helped every 8,000-particle pair: the median fell from 1.741 to 1.705 s. At
110,592 particles, however, every candidate pair was slower, with medians of 10.225
and 10.620 s. Both complete datasets remain in the
[evidence collection](/docs/project/development/assets/neighbour-traversal-v1/README.md).

The separate profiles put the extra cost in evolved counting and filling/sorting.
Late count time rose from 2.385 to 2.898 ms per step; fill/sort rose from 4.514 to
5.002 ms. Both builds reported 44 registers per thread and zero local memory, while
the major numerical kernel times stayed close. This did not support register pressure
as the explanation. The exact hardware cause remains unresolved; combining cell runs
changed traversal efficiency despite visiting the same candidates.

That version was not retained. Its small-scene saving did not justify consistently
slowing the large workload this investigation was meant to improve. That judgement
uses the workload and profile evidence, rather than a percentage or range-overlap rule.

## Keeping cell runs separate

The follow-up still visits each z-cell separately. It finds the first cell in a
column once, then advances the same sorted cursor through the following two cells.
This preserves the original cell-run structure while reducing normal lower-bound
searches from 27 to nine in both count and fill. Heapsort, row storage, transfers,
launches and numerical work remain unchanged. No occupancy limit or approximation
was introduced.

The unchanged control source and executable were reused explicitly. Both variants
received fresh warm-ups and five alternating sample pairs at each workload, with
480 steps, timestep refinement 4, eight iterations, CUDA device 0 and 128 lanes.
The 8,000-particle request retained its checkpoint audits; the 110,592-particle
request omitted them. The two campaigns were not pooled.

| Follow-up workload | Control median and range | Candidate median and range |
| --- | --- | --- |
| 8,000 particles | 1.762 s; 1.746–1.773 s | 1.800 s; 1.722–1.874 s |
| 110,592 particles | 10.423 s; 10.373–10.470 s | 10.210 s; 10.184–10.239 s |

Every large pair improved, saving 0.134–0.260 s. The ratio of workload medians
corresponds to about 2.0% less solver time. The smaller result is mixed: two pairs
improved and three slowed, and its candidate median is about 2.2% higher.

Separate follow-up profiles support the intended mechanism. Over steps 241–480,
counting fell from 2.420 to 2.066 ms per step and fill/sort from 4.550 to 4.204 ms.
The traced window fell from 10.587 to 10.315 s, with idle gaps close to 2.2 s in
both runs. Launches, transfers and tracked peak allocation were unchanged. Reported
registers rose from 44 to 46 per thread, with no reported local memory; achieved
occupancy and the exact hardware cause of the traversal difference remain unmeasured.

**Retain the follow-up.** The consistent saving at the targeted larger workload,
supporting component profiles and narrow implementation justify the change. The
smaller workload's mixed result remains a trade-off, not an improvement claim.
This is a modest gain and does not establish competitive real-time fluid performance.

## Verification and limits

The independent reader checks original compressed results and recomputes timings.
New hardware fixtures compare discontinuous columns, missing cells, negative
coordinates, identity order, block tails and reused storage with CPU all-pairs rows.
They run at all four supported CUDA block sizes alongside the existing boundary,
dense-row, invalid-offset, numerical-error, cancellation and retry checks.

Both qualified sources passed 259 CUDA tests with the same three existing CLI
failures: `configured_iteration_work_is_identified_and_replays_exactly`,
`replay_rejects_the_previous_projection_contract_explicitly` and
`threaded_selection_replay_and_environment_independence_are_public`.
The follow-up reused the identical control qualification and reran its own suite.
Strict Clippy, formatting and host bridge ASan/UBSan checks passed. Local verification
passed 239 CPU tests and 55 parent performance tests. Tests were not weakened.

The seven-size regression and all five capacity trajectories through 512,000 particles
matched retained physical results and warning schedules. The larger workloads still
warned on 75/259/300/304 steps at 32,768/110,592/262,144/512,000 particles respectively.
Exact agreement is regression evidence, not independent qualification of fluid quality.

The source exports are based on Maelstrom `8c5fc2d815f6e6c1d17b8eeed17cd7bf22b43fce`;
their exact source and executable identities are retained with each campaign. They
are working snapshots, not new Git checkpoints. The custom scene and graphics work
are preserved. No branches, commits, tags, gitlink or installed PC executable changed.

Counting and fill/sort remain substantial costs. The next useful investigation is
to separate the remaining distance-checking, row-writing and identity-sorting costs
before choosing another implementation change. Fill minus count time alone is not
a pure sorting measurement. No hosted checks, device-memory sanitiser pass or new
independent large-fluid quality qualification follows from this work.
