# Evolved neighbour-search trial

This trial follows the [host-acceptance investigation](/docs/project/development/performance-host-acceptance.md)
and the next priority in the [performance plan](/docs/project/development/performance-plan.md).
The retained candidate trace measured count/fill-and-sort at 0.824/2.038 ms per step
over steps 1–120 and 2.390/4.581 ms over steps 241–480 at 110,592 particles.
These instrumented kernel costs motivate the trial; they are not new primary timings.

## Hypothesis and unchanged work

Sorted cells are ordered by x, y, z and identity. For one x/y column, its three
adjacent z-cells form a contiguous interval. One lower-bound search followed by
that interval can replace three separate cell searches. Nine lower bounds per row
should therefore replace 27, in both count and fill, without visiting extra particles.

Only discovery traversal changes. Preserve candidate visitation order, checked
binary32 distances, strict support, prediction-time membership, exact offsets,
identity-sorted rows, dense occupancy, error precedence and retry. Keep heapsort,
cell sorting, allocation, launches, transfers and all solver equations unchanged.
The existing uncommitted graphics repair is present in both source exports; measure
headless CUDA builds, without rendering. Do not change the installed PC executable.

## Verification and collection

Freeze separate control/candidate source and executable hashes. Share new tests,
with only `native/neighbours.cuh` differing between variants. Test discontinuous
columns, empty cells, negative coordinates, upper/lower z limits, identity order,
dense rows, block tails, all supported block sizes and existing invalid-offset,
numerical-failure, cancellation and retry cases against independent CPU discovery.
Run the appropriate CPU/CUDA tests, strict Clippy, formatting and native bridge
sanitisers. Reproduce and disclose existing failures rather than weakening checks.

Use the primary PC, device 0 and 128 lanes. Keep the seven bundled 64–8,000-particle
fixtures, 480 steps, timestep refinement 4 and eight Jacobi iterations, with the
existing 0/1/120/240/480 observation schedule. The separately named 48³ workload
uses the same configuration and 480 steps without checkpoint audits. Compare all
physical results, ordered diagnostics and warning schedules exactly with retained
controls; larger-scene CFL warnings remain a fluid-quality limitation.

For each of 8,000 and 110,592 particles, collect one warm-up per variant and five
alternating matched sample pairs. Retain every sample, command, exit and environment;
take device/Linux state readings outside timed work. Preserve complete solver-step
and invocation boundaries separately. Give each invocation 120 s plus 30 s graceful
cancellation. Capacity checks at 8,000/32,768/110,592/262,144/512,000 retain the
existing memory admission and four-step pilot before the bounded 480-step request.

After ordinary sampling, collect separate full 110,592-particle Nsight Systems traces
for both variants. Partition steps 1–120, 121–240 and 241–480; compare count, fill/sort
and total costs, unchanged launch/transfer counts and tracked memory. Profiling is
diagnostic and never substitutes for the ordinary samples. Counter permissions stay
unchanged; unavailable counters are not passes.

## Assessment

Apply the [engineering assessment policy](/docs/project/development/performance-assessment.md).
Report whole-solver and component effects, all pairs, variability, regressions and
implementation cost. Decide retain, do not retain or needs more evidence in prose;
no range-overlap or percentage cutoff decides automatically. A small, reliable gain
may justify this narrow traversal change. Never trade correctness for speed or
claim that an initial lattice or warning-producing trajectory qualifies fluid quality.
