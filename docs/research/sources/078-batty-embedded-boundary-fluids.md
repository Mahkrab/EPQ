# S078 — Batty (2010)

## Full reference:

Batty, C. (2010) *Simulating Viscous Incompressible Fluids with Embedded Boundary Finite
Difference Methods*. PhD thesis. University of British Columbia, September 2010.

#### https://www.cs.ubc.ca/~rbridson/docs/batty-phd.pdf

## Relevance:

Variational pressure projection, staggered kinetic-energy weights and physical boundary
geometry. An established route beyond the flat-domain pressure feasibility prototype.

## Reliability:

Primary doctoral research from UBC. Chapter 2 incorporates published solid–fluid coupling
work of Batty, Bertails and Bridson. Read on 29 October 2026: title/abstract, §2.2
(printed pp. 35–39, PDF pp. 64–68), and §3.5 (printed pp. 67–70).
Selective reading; its general geometry and coupled viscous solver were not implemented or timed.

## Tags

`pressure-projection`, `variational`, `staggered-grid`, `boundary-conditions`

## Reading notes

- §2.2 treats pressure as an energy-metric projection onto compatible velocities.
  Boundary motion exchanges work; a stationary wall supplies normal reaction.
- §2.2.1 uses face velocities and occupied staggered-volume masses. Free-surface pressure
  uses the physical interface location rather than a rounded cell boundary.
- §3.5 derives viscosity from strain dissipation with consistently located volume weights.
  A qualified pressure operator alone does not qualify splitting or boundary traction.
- The local fractional planar layer does not validate oblique interfaces or moving geometry.

#### Date added

29/10/26
