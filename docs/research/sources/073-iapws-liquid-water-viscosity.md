# S073 — IAPWS (2011)

## Full reference:

International Association for the Properties of Water and Steam (2011)
*Revised Supplementary Release on Properties of Liquid Water at 0.1 MPa*, SR6-08(2011).
Read section 3 of the official 12-page release on 29 October 2026.

#### https://iapws.org/technical-guidance/release/LiquidWater

## Relevance:

Supports the order of magnitude of room-temperature water viscosity, separately from the chosen
ideal constant-density Newtonian model and its independently specified viscous comparison fluid.

## Reliability:

Official formulation from the responsible scientific association. Section 3 gives the viscosity
correlation, temperature range and uncertainty. The website's extracted PDF title is inconsistent
with the document identity; the page and actual section identify the liquid-water release. This
source does not justify increasing water viscosity to make a simulation quiet sooner.

## Tags

`viscosity`, `water`, `physical-model`

## Reading notes

- Section 3.2 equation 7 and table 5 yield about 1 mPa s at 293.15 K.
- The experiment's rho=1000 kg/m3, nu=1e-6 m2/s fluid is a waterlike approximation, not an exact
  thermodynamic state. The nu=1e-3 comparison defines a different synthetic Newtonian liquid.
- The release's correlation applies from 253.15 to 383.15 K; no extrapolation is used.

#### Date added

29/10/26
