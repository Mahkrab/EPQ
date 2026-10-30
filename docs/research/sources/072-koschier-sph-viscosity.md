# S072 — Koschier et al. (2019)

## Full reference:

Koschier, D., Bender, J., Solenthaler, B. and Teschner, M. (2019)
*Smoothed Particle Hydrodynamics Techniques for the Physics Based Simulation of Fluids and Solids*.
Eurographics tutorial. Read the 41-page maintained author PDF on 29 October 2026;
its contents identify the Eurographics 2019 tutorial and mark it as work in progress.

#### https://interactivecomputergraphics.github.io/SPH-Tutorial/pdf/SPH_Tutorial.pdf

## Relevance:

Provides the continuum Newtonian viscosity model and the central pair approximation used in the
isolated calibration/motion study. The dimensional viscosity and independent shear-decay test
replace an arbitrary velocity-smoothing coefficient.

## Reliability:

Primary technical teaching material by the researchers developing these solvers. Equations
97–102, page 22 of the downloaded PDF, were read directly. The maintained PDF can change;
the campaign records its SHA-256. Its continuum discussion does not establish accuracy at
Maelstrom's neighbour count, free surface or discrete time step.

## Tags

`sph`, `viscosity`, `newtonian`, `conservation`

## Reading notes

- Sections 6.1–6.2 give Newtonian stress and the incompressible viscous Laplacian.
- Equation 102 gives a central pair form with factor 2(d+2), zero strain for rigid rotation,
  and linear/angular momentum conservation; these properties are checked independently here.
- The project uses the finite C2 derivative to avoid a small-distance division singularity,
  excludes exact coincidence, uses constant physical particle volume and explicitly checks the
  time step's dissipation bound. It does not copy a nondimensional XSPH smoothing coefficient.
- The source warns that nonzero velocity divergence in strain-based formulations introduces
  additional bulk-viscosity effects. This remains relevant to approximate PBF incompressibility.

#### Date added

29/10/26
