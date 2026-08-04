# S003 — Müller, Charypar and Gross (2003)

## Full reference:

Müller, M., Charypar, D. and Gross, M. (2003) ‘Particle-Based Fluid Simulation for Interactive Applications’, *Proceedings of the 2003 ACM SIGGRAPH/Eurographics Symposium on Computer Animation*, pp. 154–159.

#### https://doi.org/10.5555/846276.846298

## Relevance:

Supports Maelstrom’s particle representation and explains Smoothed Particle Hydrodynamics-style neighbour interactions.

## Reliability:

Primary peer-reviewed research paper from ACM SIGGRAPH/Eurographics Symposium on Computer Animation.

## Tags

`core`, `particle-methods`, `spatial-hashing`

## Reading notes

- Gives the standard SPH density summation used as the basis for the equal-mass density estimate.
- Defines the three-dimensional Poly6 kernel and the Spiky kernel used for pressure-gradient directions.
- Both sourced kernels vanish at their support boundary; Maelstrom's strict neighbour inequality and explicit
  zero-distance convention are project decisions layered on those definitions.

#### Date added

05/07/26
