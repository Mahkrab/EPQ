# S076 — Litvinov, Hu and Adams (2015)

## Full reference:

Litvinov, S., Hu, X.Y. and Adams, N.A. (2015) *Towards consistence and convergence of conservative
SPH approximations*. Journal of Computational Physics, 301, pp. 394–401.
DOI: 10.1016/j.jcp.2015.08.041.

#### https://doi.org/10.1016/j.jcp.2015.08.041

## Relevance:

Provides context for distinguishing kernel smoothing from particle quadrature error and for
checking constant-pressure consistency independently of density residuals.

## Reliability:

Primary peer-reviewed numerical research. Read the abstract and bibliographic record in the
authors' Technical University of Munich institutional repository on 29 October 2026:
https://portal.fis.tum.de/en/publications/towards-consistence-and-convergence-of-conservative-sph-approxima/.
The full article was not obtained. This limited reading supports the stated consistency issue,
not the project's derived shear modulus, chosen thresholds or proposed replacement strategy.

## Tags

`sph`, `consistency`, `pressure`, `quadrature`

## Reading notes

- The abstract distinguishes smoothing error from particle integration error.
- It associates failure to reproduce constant fields with inadequate particle quadrature and
  identifies partition of unity as a consistency condition for conservative SPH.
- Its relaxation result concerns its own formulation; no claim is made that particle relaxation
  or an increased neighbour count automatically qualifies Maelstrom's pressure projection.
- The artificial modulus and manufactured-force predictions in the project are independently
  derived and measured, not attributed to unread parts of this paper.

#### Date added

29/10/26
