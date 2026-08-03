# S052 — Akinci et al. (2012)

## Full reference:

Akinci, N., Ihmsen, M., Akinci, G., Solenthaler, B. and Teschner, M. (2012) ‘Versatile Rigid-Fluid Coupling for Incompressible SPH’, *ACM Transactions on Graphics*, 31(4), Article 62, pp. 62:1–62:8.

#### https://doi.org/10.1145/2185520.2185558

## Relevance:

Explains why fluid-particle density is underestimated near solid boundaries and provides the boundary-particle density correction referenced by the PBF paper. It supports an evidence-based choice between simple collision planes and density-aware solid boundaries.

## Reliability:

Primary peer-reviewed ACM SIGGRAPH paper published in *ACM Transactions on Graphics*. Its authors are established particle-fluid researchers, and the paper evaluates the method with weakly compressible and predictive-corrective incompressible SPH solvers.

## Tags

`sph`, `boundary-particles`, `density-correction`, `rigid-fluid-coupling`

## Reading notes

- Identifies particle deficiency near solid boundaries as a cause of discontinuous or inaccurate SPH quantities.
- Assigns sampled boundary particles a volume-derived density contribution rather than treating them as ordinary
  inertial fluid mass.
- Supports the documented density-aware alternative; Maelstrom deliberately retains simple planes for the
  Milestones 00--03 comparison instead.

#### Date added

23/07/26
