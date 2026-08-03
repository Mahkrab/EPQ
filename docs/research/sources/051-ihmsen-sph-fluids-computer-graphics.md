# S051 — Ihmsen et al. (2014)

## Full reference:

Ihmsen, M., Orthmann, J., Solenthaler, B., Kolb, A. and Teschner, M. (2014) ‘SPH Fluids in Computer Graphics’, *Eurographics 2014 — State of the Art Reports*, pp. 21–42. Eurographics Association.

#### https://doi.org/10.2312/egst.20141034

## Relevance:

Provides an authoritative comparison of graphics-oriented SPH methods and practical guidance on simulation order, timestep selection, neighbourhood search, density convergence, boundary handling and the cost structure of iterative solvers such as PBF.

## Reliability:

Peer-reviewed Eurographics state-of-the-art report written by researchers with extensive publications in particle-based fluid simulation. It synthesises the established literature and distinguishes alternative methods rather than presenting one implementation as universal.

## Tags

`sph`, `neighbour-search`, `timestep`, `density-error`, `performance`

## Reading notes

- Describes a velocity CFL condition of the form $\Delta t\leq\lambda d/\|v_{\max}\|$, with particle diameter
  $d$ and $\lambda\approx0.4$, while noting that further timestep aspects can also matter.
- Treats neighbourhood search as a distinct expensive stage in Lagrangian particle simulation.
- Supports reporting density deviations and separating correctness concerns from performance cost; Maelstrom's
  fresh all-pairs audit and warning-only fixed-timestep policy are project decisions.

#### Date added

23/07/26
