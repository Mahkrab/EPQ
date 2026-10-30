# Pressure replacement feasibility

**Decision, 29 October 2026: GO for a bounded, isolated compatible finite-volume fluid
prototype; NO-GO for production adoption.** A staggered face-flux pressure projection passes
the fundamental tests that the sampled-density PBF formulation failed. A restricted direct
solver also demonstrates a credible pressure budget on the RTX 4070. General moving surfaces,
transport and viscous coupling remain unqualified.

This study follows the [pressure diagnosis](/docs/project/development/milestones/05/pressure-projection-diagnosis.md).
It does not replace its failures, revise the five-second quietness result, or change production
behaviour. The assessed Maelstrom HEAD remains
[`250932784790ba26cdc55fc38a877ccefacbf054`](https://github.com/Mahkrab/Maelstrom/tree/250932784790ba26cdc55fc38a877ccefacbf054);
EPQ remains at `814f88a7f4122b1b24ea645b210d89e1200a0c44`. New sources and observations are
uncommitted experiments, with checked standalone snapshots rather than a historical checkpoint.

## Scope and mathematical admission

The [protocol](/docs/project/development/milestones/05/assets/pressure-feasibility-v1/protocol.json)
preceded implementation. At most three lightweight prototype families were allowed; failed
candidates were screened rather than developed into fluid solvers. Thresholds were constant-pressure,
adjoint-work and periodic-momentum errors below scaled `1e-10`, affine-divergence error below
`1e-9`, pressure/velocity/hydrostatic/volume errors below 1%, no projection energy increase above
scaled `1e-10`, and solve residual below `1e-8`. Spatial admission required at least three levels
and the two finest passing. Perturbed sampling could not be calibrated away.

The [admission record](/docs/project/development/milestones/05/assets/pressure-feasibility-v1/admission.json)
and continuum checks of each cost geometry preceded GPU timing. Eight final independent tests
cover invariants, a continuum pressure gradient, spatial convergence, timestep normalisation,
counterexamples and invalid inputs. The additional normalisation measures velocity error against
the intended pressure impulse, so a small timestep cannot conceal a poor pressure correction.

These are **pressure-operator gates**. Fixed-domain cell volumes and instantaneous volume flux
are tested; material-volume transport, transient particle compression and complete-fluid settling
are not qualified by them. No complete fluid model is declared physically acceptable here.

## Alternatives and decisive counterexamples

| Candidate | Evidence and decision |
| --- | --- |
| Locally linear-consistent weighted least-squares divergence, paired with its exact mass adjoint | Reject this shortcut. With 10%-spacing perturbations, constant-pressure acceleration scaled by `rho*h/p` is **0.347, 0.299, 0.362** at 8, 16, 32 sites per direction. Translation and total pressure-force cancellation still pass. An adjoint and local linear reproduction do not ensure local constant-pressure invariance. |
| Unweighted Voronoi cells treated as material parcels | Reject this shortcut. Total area is correct to round-off, but a determinant-one affine shear changes individual areas. Central-difference fractional volume rates per unit shear are **0.1044, 0.06311, 0.09406** on the perturbed 8², 16², 32² sets. Results agree for strain increments `1e-3` and `1e-5`; this is not just finite-strain truncation. |
| Compatible staggered finite-volume face projection | Admit for fixed rectangular domains with periodic horizontal directions, a flat impermeable bed and a planar pressure-free surface; fully periodic and fractional-top-layer cases also tested. |

The two meshless counterexamples are two-dimensional periodic manufactured tests. A 2D failure
is sufficient to reject those particular shortcuts; it does not establish impossibility for
meshless methods in general. Regular lattices hide both failures. The Voronoi affine test shears
the periodic fundamental cell with the particles; a separate sinusoidal isochoric map keeps the
box fixed. Both preserve material area analytically.

The full **Power Particles** method remains a serious volume-based alternative. Its weights,
centroid-based parcel evolution, volume optimisation and compatible operators are central parts
of the algorithm. It was not implemented, and failure of the unweighted shortcut does not reject
it. The paper describes a pressure solve plus weight-optimisation solves and evolving clipped
3D power diagrams; construction is average-case linear and worst-case quadratic. That geometry
and additional nonlinear work give it a less direct GPU feasibility path than the tested regular
grid. Its RTX 4070 cost is unknown.<sup><a href="#ref-s077">S077</a></sup>

DFSPH controls divergence as well as density drift, but its stated SPH formulation still uses
kernel-derived quantities. Merely changing iteration level does not establish the consistency
missing here. It was considered from its formulation and not reproduced; this is a bounded
shortlist decision, not an experimental rejection of every DFSPH variant.<sup><a href="#ref-s079">S079</a></sup>

## Recommended pressure discretisation

Use a [staggered grid](https://en.wikipedia.org/wiki/Staggered_grid): cell pressures and face-normal
velocities, with one shared geometric description for divergence, pressure gradient and kinetic
energy. This follows the established variational interpretation of pressure as a mass-metric
projection onto compatible divergence-free velocities.<sup><a href="#ref-s078">S078</a></sup>

For diagonal cell volumes `V`, face areas `A`, centre-to-centre or centre-to-interface distances
`d`, density `rho`, and oriented incidence `C` with owner −1 and neighbour +1, the local derivation is

```math
M_f=\operatorname{diag}(\rho A_f d_f),\qquad
D=-V^{-1}C\operatorname{diag}(A_f),\qquad
G=\operatorname{diag}((\rho d_f)^{-1})C^T=-M_f^{-1}D^TV.
```

```math
L=C\operatorname{diag}(A_f/(\rho d_f))C^T,\qquad
Lp=C\operatorname{diag}(A_f)u^*/\Delta t,\qquad
u^{n+1}=u^*-\Delta t Gp.
```

The resulting matrix is positive definite with the free-surface pressure condition, or positive
semidefinite with the constant-pressure gauge removed in a fully periodic/closed domain. No
artificial pressure, correction scale or density regularisation is needed in this pressure solve.
An existing divergence-free velocity is a fixed point. With homogeneous external pressure and
stationary walls, the projection cannot increase kinetic energy in its defined mass metric.

A wall prescribes normal flux; pressure supplies its normal reaction. No-slip tangential traction
belongs to viscosity. At the top, atmospheric pressure is imposed at the **physical interface**,
using its actual dual distance. A constant-pressure offset is tested with the external pressure
offset by the same amount. Holding atmospheric pressure fixed while changing internal pressure
would describe a physical load, not a gauge-invariance test. General embedded-boundary geometry
must retain compatible weights; those extensions are established research but are not locally
validated by the planar prototype.<sup><a href="#ref-s078">S078</a></sup>

## Physical and convergence results

The reference slab has `rho=1000 kg/m³`, dimensions `0.2 × 0.05 × 0.2 m`, volume `0.002 m³`
and mass `2 kg`. Horizontal directions are periodic. Spatial refinement changes the grid while
preserving these dimensions. Fractional top-layer heights of 1, 0.37 and 0.1 preserve the same
physical height and use consistent volumes, face areas and distances.

| Vertical cells | Free-surface pressure error, full top cell | Worst fractional-top pressure error | Fully periodic pressure error |
| ---: | ---: | ---: | ---: |
| 4 | 0.7388% | 0.9270% | **9.6575%, fail** |
| 8 | 0.1839% | 0.2027% | **2.3241%, fail** |
| 12 | 0.08169% | 0.08686% | **1.0256%, fail** |
| 16 | 0.04594% | 0.04804% | 0.57549% |
| 24 | Not run | Not run | 0.25532% |

These are volume-weighted L2 errors against an independently differentiated smooth pressure
solution, not a discrete right-hand side generated by the tested gradient. The vertical periodic
mode has four times the wavenumber of the free-surface mode. This explains the different resolution
requirements; the data do not establish a universal minimum of four fluid layers. Approximately
second-order convergence and the failed coarse periodic grids are retained. The initial 27-case
screen and the 29-case reproduction, including two finer periodic levels, are both archived.

Error in the projected velocity, normalised by the intended pressure impulse rather than the
background shear, decreases from **0.2497% to 0.01547%** in the full-layer free-surface refinement.
For periodic refinement it decreases from **3.2369% to 0.08486%**; the two finest levels pass both
pressure and velocity gates. Pure periodic shear is preserved exactly. Gravity-supported shear
varying through depth is preserved within `3.1e-14` relative error over the main slab campaign.

Hydrostatic pressure agrees with `rho*g*(H-y)` within `4.9e-14` relative error over that campaign;
the extrapolated bed force agrees with the **19.62 N** liquid weight within `4.0e-14` relative error.
Maximum residual hydrostatic speed is `5.6e-14 m/s`. Periodic momentum impulses are below
`4.8e-18 kg m/s`; adjoint work discrepancies are below `4.8e-18` in the tested fields. Projection
energy changes are nonpositive. These results test pressure support and normal reaction; they
do not claim tangential viscosity or arbitrary solid-boundary accuracy.

In a separate 16-case policy study, timesteps range from 4 to 0.5 ms and CG tolerances from
`1e-4` to `1e-10`, one variable at a time. Pressure error remains about **0.20271%** for the
fractional-top geometry. Tighter solves reach the spatial-error floor. Absolute residual velocity
scales with timestep, while velocity error relative to the pressure impulse stays constant.
There is no pressure-derived shear stiffness repaired by taking smaller steps.

![Pressure convergence and same-accuracy pressure-stage cost](/docs/project/development/milestones/05/assets/pressure-feasibility-v1/feasibility.svg)

## Cost at equivalent pressure accuracy

Primary-PC measurements used the **RTX 4070, 12,282 MiB, driver 610.88, CUDA 13.3.73**, FP64,
without fast math. Both algorithms solve the same admitted operator. Each proposed cost geometry
first passed the continuum tests: pressure errors were 0.04594%, 0.06441% and 0.04653% for the
small slab, wide slab and deep column respectively. The GPU algebraic test then used an independently
reconstructed multi-mode pressure plus hydrostatic ramp. This algebraic reference checks coding
and solve errors; it does not replace the continuum tests.

Thirty timed trials used three alternating solver pairs per case. Each process warmed up three
pressure steps. Wall-clock time covers force kick, divergence, complete pressure solve, projection
and completion; allocation, planning, field output and teardown are excluded. Raw setup, process
wall and CUDA-event times are retained. Setup medians are about 0.23–0.26 s. Wall time is the cost
authority; small differences between event and wall timers are not used to infer GPU mechanisms.

The predeclared cost policy is advective CFL 0.5 at assumed maximum speed 0.5 m/s. Steps are
rounded to cover exactly 0.1 simulated seconds; the additional one-second case checks horizon
sensitivity. This is a **component-cost policy**, not a qualified timestep for complete fluid motion.

| Pressure geometry, cells | dt | Direct solve: median [range] s / simulated s | Jacobi PCG: median [range] s / simulated s | PCG iterations |
| --- | ---: | ---: | ---: | ---: |
| Small slab, 64×16×64 = 65,536 | 3.125 ms | **0.0380** [0.0375, 0.0446] | 10.950 [10.777, 10.996] | 111–115 |
| Wide slab, 256×12×171 = 525,312 | 4.545 ms | **0.1723** [0.1661, 0.1732] | 16.418 [16.232, 16.789] | 149–152 |
| Deep column, 64³ = 262,144 | 6.25 ms | **0.0570** [0.0570, 0.0635] | 14.093 [13.951, 14.881] | 235–237 |
| Small slab, half timestep | 1.5625 ms | **0.0726** [0.0725, 0.0731] | 21.823 [21.514, 23.783] | 111–115 |
| Small slab, one-second horizon | 3.125 ms | **0.03594** [0.03564, 0.03697] | 10.993 [10.752, 11.184] | 111–115 |

An independent long-wave scale follows from `eta_t + H*u_x = 0` and `u_t + g*eta_x = 0`:
`c = sqrt(g*H)`. If subsequent explicit coupling instead requires
`dt = 0.5*h_min/(0.5+c)`, the corresponding direct-pressure costs, **projected from measured
cost per step**, are about **0.091, 0.416 and 0.283 s per simulated second** for these three
geometries. Those are not measured coupled timings or a validated stability/accuracy policy.
The timestep sensitivity measurement supports the local cost scaling; gravity-wave dispersion,
advection error and any capillary physics still need independent temporal qualification.

All 30 trials passed the independent retained-field audit. Maximum true relative residual was
`9.98e-11`, pressure error against the discrete manufactured field `6.08e-13`, final velocity error
`4.32e-12 m/s`, and free-surface volume flux `1.34e-14 m³/s`. Measured accepted kinetic-energy
change was zero at recorded precision. A separate small GPU admission run also agreed with the
independent sparse CPU solve. No unsuccessful or slow timed sample was discarded.

The direct solver applies two horizontal Fourier transforms and a vertical tridiagonal solve,
with fixed-geometry factors prepared once. It costs `O(N*(log Nx+log Nz))` work and `O(N)` storage.
Its restriction to periodic sides and a flat bed/surface is essential: the measured timing does
**not** apply to obstacles, changing occupancy or curved surfaces.

The general pressure stencil requires a seven-point cell traversal per matrix application,
not a particle-neighbour search. Jacobi PCG costs `O(kN)`, plus reductions and host completion in
this ordinary baseline. Its measured cold-start cost is unacceptable for real time. A geometric
multigrid preconditioner is the proposed general-domain route; near-linear work and fewer
iterations are expectations to verify, **not measured performance**. Warm starting, FP32,
preconditioner changes and GPU launch optimisation were not used to improve these numbers.

There is no valid same-accuracy speedup ratio against current PBF: it failed physical admission.
These grid-cell counts also do not establish a particle capacity or a whole-solver frame rate.

## Next implementation and validation gate

Proceed only with an isolated compatible finite-volume prototype. Keep the direct solver as a
restricted reference and introduce a general solver only behind the same physical gates.

1. Extend geometric compatibility to oblique walls and moving free surfaces. Recheck pressure
   offsets, affine fields, bed/obstacle reactions, fractional volumes and spatial convergence.
   Small-cell conditioning must not be hidden by a correction multiplier or arbitrary compliance.
2. Select and qualify conservative interface/material-volume transport and, if particles carry
   state, the particle/grid transfer. Test constant and affine velocity reproduction, uniform
   translation across cells, volume-preserving shear, mass/momentum budgets and energy over a
   full advection period. Grid pressure does not automatically make these operations consistent.
3. Couple dimensional viscosity and boundary traction, then repeat shear decay, hydrostatics,
   standing-wave/sloshing references, transient density, resolved collisions and settling together.
   Preserve all original results and thresholds, including 5% p95 compression and the original
   quietness result. Any alternative observable or quietness criterion needs its own physical
   justification. Require simultaneous spatial, timestep and solver-tolerance convergence, with
   pressure/velocity/reference observables within 1% and geometric volume within 1%.
4. Only after that gate, measure complete-fluid cost per simulated second on the PC, including
   transport, surface reconstruction, viscosity, general pressure solving and observations.
   Use timestep error studies alongside advective CFL and relevant viscous/gravity-wave scales.
   Stop pressure iterations by physical divergence/volume error and verified residual, rather
   than inheriting eight Jacobi iterations. The tested `1e-10` solve is a conservative reference;
   the `1e-8` mathematical plateau is not a measured GPU saving.

**Real-time feasibility is credible but bounded.** The measured direct pressure stage consumes
about 3.6–17.2% of a real-time budget at the declared policies; the stricter illustrative long-wave
policy projects 9.1–41.6%. This leaves a credible, unproven path for the remaining stages. The
current iterative PCG baseline does not. For arbitrary moving free
surfaces, the feasibility decision remains conditional on general-solver and transport qualification.
No general real-time liquid regime or production replacement has yet been established.

## Reproducibility and preservation

The [evidence guide](/docs/project/development/milestones/05/assets/pressure-feasibility-v1/README.md)
contains commands, source/build identities, raw arrays, every solve history and timed observation,
and checksummed local/primary-PC readback receipts. The prior 450-file pressure-diagnosis archive
was rechecked locally and on its independent primary mirror. All 13 guarded native source files,
both HEADs and the pre-existing Maelstrom working state remain unchanged, preserving all ten CUDA
optimisations. No production tests or whole-fluid benchmark are claimed from this pressure study.
There was no production integration, history operation or system-setting change.

## References used

- <a name="ref-s077"></a> S077: de Goes et al. (2015), *Power Particles*. [Reading record](/docs/research/sources/077-de-goes-power-particles.md).
- <a name="ref-s078"></a> S078: Batty (2010), *Simulating Viscous Incompressible Fluids with Embedded Boundary Finite Difference Methods*. [Reading record](/docs/research/sources/078-batty-embedded-boundary-fluids.md).
- <a name="ref-s079"></a> S079: Bender and Koschier (2017), *Divergence-Free SPH for Incompressible and Viscous Fluids*. [Reading record](/docs/research/sources/079-bender-koschier-divergence-free-sph.md).
