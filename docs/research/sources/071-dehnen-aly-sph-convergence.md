# S071 — Dehnen and Aly (2012)

## Full reference:

Dehnen, W. and Aly, H. (2012) ‘Improving convergence in smoothed particle hydrodynamics
simulations without pairing instability’, *Monthly Notices of the Royal Astronomical Society*,
425(2), pp. 1068–1082. doi:10.1111/j.1365-2966.2012.21439.x.
Read arXiv:1204.2471v2, dated 1 June 2012.

#### https://arxiv.org/abs/1204.2471

## Relevance:

Motivates the separate Wendland-kernel experiment after particle-site density statistics and
geometric tank volume disagreed. It does not establish an accurate Maelstrom PBF configuration.

## Reliability:

Primary peer-reviewed numerical research with stability analysis and tests. Its force-based SPH
results are not a proof about Maelstrom's position projection, free surfaces or static walls.

## Tags

`sph`, `convergence`, `kernels`, `pairing`, `wendland`

## Reading notes

- The abstract and introduction distinguish particle-disorder errors from pairing instability.
- Section 2 distinguishes kernel support radius from smoothing scale. Equal support does not mean
  equal spatial resolution when changing kernels.
- The paper motivates Wendland kernels through pairing stability, rather than attributing all
  instability to a zero derivative at the origin.
- The project experiment uses fixed support, lattice-calibrated equal masses and compression-only
  PBF constraints; these are project choices requiring independent qualification.
- Re-read section 2.5 for the spatial-resolution study. It distinguishes density estimates at
  particle locations from estimates at unoccupied locations and discusses self-contribution bias.
  This supports checking interparticle probes separately; its proposed SPH correction has not
  been adopted into Maelstrom or treated as a qualified PBF free-surface method.
- The 29 October follow-up tests a constant particle-site subtraction in the isolated PBF
  reference. Its coefficient comes from the physical-rest cubic lattice, rather than the
  paper's fitted neighbour-count law. Fixed support leaves the density gradient unchanged;
  PBF work, conservation and free-surface accuracy are still checked independently. Production
  Maelstrom remains unchanged.

#### Date added

28/10/26
