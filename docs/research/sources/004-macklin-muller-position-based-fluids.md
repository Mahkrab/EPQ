# S004 — Macklin and Müller (2013)

## Full reference:

Macklin, M. and Müller, M. (2013) ‘Position Based Fluids’, *ACM Transactions on Graphics*, 32(4), Article 104, pp. 104:1–104:12.

#### https://doi.org/10.1145/2461912.2461984

## Relevance:

Core design reference for position-based fluid constraints, density correction, solver iteration count and the trade-off between visual plausibility, stability and speed.

## Reliability:

Published in ACM Transactions on Graphics and accompanied by an author-hosted preprint. It is a primary research source.

## Tags

`core`, `position-based-dynamics`, `solver-iterations`

## Reading notes

- Defines the per-particle density constraint, equal-mass simplification, relaxed multiplier and pairwise PBF
  position correction.
- Uses Poly6 for density and Spiky for constraint directions, and solves particle constraints in Jacobi fashion.
- Recomputes neighbourhoods once per timestep while recalculating distances and constraint values each solver
  iteration.
- Reports a typical fixed iteration count of two to four and the artificial-pressure form with
  $|\Delta q|=0.1h$--$0.3h$, $k=0.1$ and $n=4$ working well in its simulation coordinates.
- Presents XSPH viscosity and vorticity confinement as optional velocity post-processes; Maelstrom disables both
  for the reference.
- Re-read §8 and Table 1 of the [author preprint](https://mmacklin.com/pbf_sig_preprint.pdf) on
  22 October 2026. The CUDA implementation ran on a GTX 680. Armadillo Splash reports 128k
  particles, two steps per frame, three iterations per step and 4.2 ms per step; Dam Break
  reports 100k, four steps per frame, three iterations per step and 4.3 ms per step.
  Table 1 uses a 16 ms simulated frame. These are workload-specific results, not equivalent
  Maelstrom benchmarks or display frame rates.

#### Date added

05/07/26
