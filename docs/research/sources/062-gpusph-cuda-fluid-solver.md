# S062 — GPUSPH developers (n.d.)

## Full reference:

GPUSPH developers (n.d.) *GPUSPH*. Upstream README, revision
`08ffd94ddc4a076361f0e5f6e2bfde7874ba087f`. Accessed 22 October 2026.

#### https://github.com/GPUSPH/gpusph/tree/08ffd94ddc4a076361f0e5f6e2bfde7874ba087f

## Relevance:

An established open-source CUDA fluid code to inspect for architectural alternatives beyond PBF.

## Reliability:

Primary, pinned project documentation. The README establishes method and implementation platform,
not a comparable PBF timing. Its old toolkit guidance should not be treated as current installation advice.

## Tags

`cuda`, `sph`, `performance`, `open-source`

## Reading notes

- Read the pinned [README](https://github.com/GPUSPH/gpusph/blob/08ffd94ddc4a076361f0e5f6e2bfde7874ba087f/README.rst).
- Identifies a CUDA implementation of weakly compressible SPH, not position-based fluids.
- Device-state ownership and neighbour-list construction/traversal are planned inspection topics;
  no kernel-level finding or GPUSPH benchmark was established by this reading.
- Further inspection on 22 October read pinned `docs/dev-guide/src/dox/neibs.dox` and
  `src/cuda/neibs_iteration.cuh`. They describe neighbour-index construction after hash/sort/reorder
  and implement strided list offsets. The iterator declares GPL-3.0-or-later; no code was copied.

#### Date added

22/10/26
