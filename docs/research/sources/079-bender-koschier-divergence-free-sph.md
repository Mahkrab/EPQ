# S079 — Bender and Koschier (2017)

## Full reference:

Bender, J. and Koschier, D. (2017) *Divergence-Free SPH for Incompressible and Viscous Fluids*.
IEEE Transactions on Visualization and Computer Graphics, 23(3), pp. 1193–1206.
DOI: 10.1109/TVCG.2016.2578335.

#### https://dankoschier.github.io/resources/papers/BK17.pdf

## Relevance:

An established velocity-level divergence/density-control alternative. Separates iteration
and timestep improvements from changing the pressure spatial discretisation.

## Reliability:

Primary peer-reviewed research. Read from the author's 14-page manuscript on 29 October 2026:
abstract, introduction and §3 SPH/DFSPH formulation. The UCL institutional record confirms
publication details. No full DFSPH reproduction was run; its efficiency is not local physical
qualification or RTX 4070 evidence.

## Tags

`sph`, `divergence`, `pressure-projection`, `feasibility`

## Reading notes

- Controls divergence and density drift, with an optional implicit viscosity solve.
- Divergence still uses particle/kernel sums. Changing iteration level alone does not
  prove constant-pressure or volume-preserving-shear consistency.
- Excluding it from this bounded implementation shortlist does not reject every DFSPH
  variant or corrected meshless projection.

#### Date added

29/10/26
