# Coupled finite-volume fluid qualification

**Decision, 29 October 2026: NO-GO for this coupled candidate, its CUDA port and production
qualification.** The isolated prototype conserves material volume and momentum and retains the
pressure projection's algebraic compatibility. It nevertheless fails gravity-wave velocity/energy
accuracy and collision energy/convergence. No coupled RTX 4070 throughput benchmark was admitted.
The compatible pressure family remains a valid foundation; its pressure-only results have not
been replaced by these failures.

This follows the [pressure feasibility study](/docs/project/development/milestones/05/pressure-feasibility.md).
Maelstrom remains at `250932784790ba26cdc55fc38a877ccefacbf054` and EPQ at
`814f88a7f4122b1b24ea645b210d89e1200a0c44`. Nothing was integrated into production. The experiments
are uncommitted standalone sources, not a Git checkpoint. The
[evidence guide](/docs/project/development/milestones/05/assets/coupled-fluid-v1/README.md) identifies
the original and corrected versions, every accepted state, failed prefixes and reproduction commands.

## Model and predefined admission

The [protocol](/docs/project/development/milestones/05/assets/coupled-fluid-v1/protocol.json) preceded
the calculations. The minimal model is two-dimensional incompressible two-fluid Euler flow,
with liquid density **1000 kg/m³**, gas density **1.2 kg/m³**, zero viscosity and zero surface
tension. These are explicit idealised material assumptions, not a numerical density floor or
an attempt to model viscous settling. The domain is **0.2 × 0.1 m**, periodic horizontally, with
either periodic vertical boundaries for manufactured tests or a flat impermeable bed and rigid,
free-slip gas lid. Quantities are per unit out-of-plane depth: mass kg/m, energy J/m, force N/m.
Curved solids, wall friction, real coalescence physics and three-dimensional flow are outside this model.

A geometric volume-of-fluid (VOF) interface transports liquid volume. A monotone algebraic
MUSCL transport is retained as a control. The geometric scheme freezes its split compression
indicator across directions, so that its source cancels with the same discrete divergence used
by pressure. Momentum uses the phase-derived mass flux. These principles are established in
VOF research; the local averaging of staggered masses is a separate approximation, not a
reproduction of the complete published staggered-reconstruction algorithm.<sup><a href="#ref-s080">S080</a></sup>

No particles or particle/grid transfers were introduced. They were unnecessary to these tests
and would have added another unqualified coupling. The interface is internal to an explicitly
modelled gas; the reference is therefore a two-fluid wave under a rigid lid, not a vacuum surface.

For cell density `rho`, a face's inertial density is the arithmetic average of neighbouring cell
densities. Its momentum mass is `M_f=rho_f*hx*hy`. Averaged material mass fluxes satisfy the same
staggered mass update. The pressure divergence and gradient retain the admitted incidence form:

```math
D=-V^{-1}C A,\qquad G=-M_f^{-1}D^T V,\qquad
u^{n+1}=u^*-\Delta t Gp.
```

Euler and midpoint coupling were compared without changing the interface or pressure formulation.
The rectangular direct solver is valid only for the appropriate constant-density rectangular
operator. Constant-density FFT/cosine controls agreed with the previously admitted 3D projection.
Evolving material density changes the coefficients, so the coupled reference uses a small sparse
direct solve. The previous free-top CUDA factorisation was not applied to this different operator.
No multigrid implementation or pressure-performance extrapolation was needed to diagnose the failure.

Predefined gates included relative material mass/volume errors below `1e-10`, periodic momentum
error below `1e-9`, pressure residual and `dt*max|div u|` below `1e-8`, and phase bounds within
`1e-10`. Reference velocity, pressure, interface-volume error, wave amplitude/frequency and
inviscid energy error had **1%** limits. Spatial admission required three levels and the two
finest passing; timestep studies used three policies at fixed geometry. No threshold was relaxed.

For gravity waves, the energy gate uses the small **wave energy**, not the much larger background
gravitational energy. This was specified in the
[energy protocol](/docs/project/development/milestones/05/assets/coupled-fluid-v1/energy-and-cases-protocol.json)
before the wave runs. Geometric subcell liquid moments define potential energy; cell-centre
potential is retained only as a diagnostic. The old PBF compression and quietness results remain
unchanged. A particle-free prototype is not assigned a pass for the old particle-density test.

## Incremental controls and one corrected implementation defect

Independent tests cover half-plane geometry, subcell moments, uniform translation, constant
pressure, projection energy, momentum, hydrostatic shear, the wave reference's vacuum limit,
failed-step rollback and rejection of false raw summaries. **All ten final tests passed.**

Using a different mass flux for momentum than for material transport gives a **1.0336 m/s**
velocity error from a **0.1 m/s** uniform initial flow. Using the same mass flux reduces the
one-step error to `2.8e-17 m/s`. The mismatched coupling was rejected, not tuned.

After a full horizontal translation, independently integrated circular-interface L1 errors were:

| Horizontal × vertical cells | Algebraic transport | Geometric transport |
| --- | ---: | ---: |
| 32 × 16 | 21.48% | 4.249% |
| 64 × 32 | 8.272% | 1.282% |
| 128 × 64 | 3.398% | **0.3307%** |

Both conserve material volume to round-off; interface accuracy distinguishes them. Geometric
transport is promising, but these levels do not satisfy the two-finest-passing rule. The
algebraic control was not carried into more coupled development.

The pressure and full coupled steady controls pass. A flat liquid/gas interface under gravity
with a steady affine tangential shear remains unchanged over 0.2 s at all three resolutions.
At 128 × 64, maximum velocity change is **8.96e-12 m/s** and hydrostatic pressure error is
**1.93e-12 relative**. Separate fractional-interface hydrostatic tests have at most **0.556%**
bulk pressure error at 32 × 16, decreasing to **0.03695%** at 128 × 64; bed–lid reaction matches
total material weight within `1e-11` relative error.

A periodic manufactured travelling shear has the exact material map
`x=x0+U*t`, `y=y0+V*t*sin(k*x0)`, with constant pressure. At 128 × 64, shear-mode amplitude
error is **0.0815%**, velocity error **0.0876%**, and energy drift **0.00160%**. Its interface
error remains **1.152%**, so the complete test fails. The coarsest version exceeded its CFL
guard after numerical velocity errors grew; its prefix is retained. This is not a claim of
a universal resolved shear regime.

Early wave runs also exposed a genuine geometry implementation defect: subtracting four
squared terms in a half-plane area formula loses precision for nearly horizontal/vertical
interfaces. An independent exact-area control found errors up to **2.29e-6**. Equivalent
triangular/linear branches eliminate the cancellation without changing the mathematical
scheme, physics, timesteps or bounds. Replaying each failed step with that sole change succeeds.
Original sources and failures are retained separately. The corrected wave runs complete, and
their large physical errors below remain.

## Gravity waves: surface timing passes while velocity and energy fail

The independent reference comes from harmonic velocity potentials, normal-velocity continuity
and pressure continuity between two layers. With liquid depth `Hl=0.05 m`, gas depth `Hg=0.05 m`,
`k=2*pi/0.2 m` and amplitude `a=5e-5 m`, it gives

```math
\omega^2=\frac{(\rho_l-\rho_g)gk}
{\rho_l\coth(kH_l)+\rho_g\coth(kH_g)},\qquad
E_0=\frac{(\rho_l-\rho_g)gLa^2}{4}.
```

The period is **0.37417 s**. Cell volumes and staggered reference momenta are independently
integrated; velocity comparisons do not simply sample across a discontinuous phase boundary.
Amplitude/depth is `1e-3`, and the finite-density gas is included in the reference.

| Grid | Frequency error | Fitted amplitude error | Worst quarter-period velocity error | Maximum wave-energy error |
| --- | ---: | ---: | ---: | ---: |
| 32 × 16 | 2.608% | 0.2380% | 207.4% | 752.9% |
| 64 × 32 | **0.8737%** | **0.07177%** | 113.6% | 280.0% |
| 128 × 64 | **0.2800%** | **0.01368%** | 63.50% | 95.80% |

At the finest level, even the liquid-only quarter-period velocity error is **9.35%**. Peak
sampled gas speed is **0.0866 m/s**, against **0.000895 m/s** in the independent potential-flow
reference. Pressure-perturbation error is approximately **10.84%**. Initial geometric potential
energy is accurate within `3.2e-6` relative to wave energy; the energy failure is not an initial
energy-calibration error. Sampling the exact reference introduces only **0.0398%** kinetic-energy
bias at the finest quarter-period control, far below the measured failure.

At 64 × 32, changing from 256 to 512 to 1024 steps per period leaves energy error near **280%**
and quarter-period velocity errors near **80.5% and 113.6%**. Euler coupling gives almost the
same failure as midpoint. Spatial errors decrease, but no tested moving-surface regime passes;
the data do not establish a wrong refinement limit or justify extrapolation to enormous grids.

Every pressure projection has nonpositive kinetic work and preserves its mass-weighted null-shear
impulse. At the finest level, the accepted-stage energy ledger over one period gives transport
kinetic change **−1.910 E0**, body-plus-pressure kinetic change **+2.485 E0**, and geometric
potential change **+0.000699 E0**. Thus numerical transport loss partly hides a larger erroneous
force/energy exchange. It would be incorrect to say the projection itself has positive kinetic
work or to add damping to cancel the final excess.

## Isolating the interface pressure/inertia error

The [frozen-interface control](/docs/project/development/milestones/05/assets/coupled-fluid-v1/interface-control-protocol.json)
turns transport off and measures the first gravity/pressure acceleration from rest. At 64 × 32,
the averaged-mass operator has **137.7%** acceleration error despite a pressure residual near
`1e-10`. Some staggered volumes geometrically containing only gas receive liquid inertia from
averaged neighbouring cell fractions. Total material mass is still correct; local inertia is not.

Replacing only the supplied masses by independently integrated physical staggered masses,
while changing gradient weights consistently, reduces that alignment's acceleration error to
**1.926%** and pressure-perturbation error from **15.57% to 0.243%**. This is a pressure-only
diagnostic, not a coupled repair: those masses would require matching transported mass fluxes.

It also fails as a general repair. Moving the interface by half a cell changes the original
acceleration error to **0.856%**, while the physical-mass-only alternative gives **21.94%**.
At a quarter-cell offset both are around **16%**. Changing gas density or wave amplitude changes
the error substantially. Those are controlled sensitivity observations, not permission to tune
the gas or interface alignment to make a case pass.

The offset controls change liquid depth by a fraction of a cell and update the physical reference,
holding relative wave amplitude fixed. They establish depth/alignment sensitivity, not a pure
translated-grid test at identical wall geometry. The main three-level refinement holds physical
depth and domain fixed. A complete separation using translated grids and cut walls remains unrun.

The supported diagnosis is an inadequate **interface representation linking staggered inertia,
pressure interpolation/traction and gravity work**. Exact adjoint algebra and shared mass fluxes
are necessary but insufficient. A density-weight substitution alone does not solve it. The
remaining error is not explained by iteration count, material-mass drift, the area-cancellation
bug, particle transfer, the old PBF shear modulus, or physically expected inviscid oscillations.
The study does not prove that every compatible finite-volume coupling has this failure.

## Controlled collision and timestep policy

Two equal liquid discs approach in an exactly divergence-free symmetric streamfunction field,
with zero gravity. The reference constraints are mass, momentum, symmetry, unforced energy and
spatial/timestep convergence; there is no invented exact post-contact shape solution.

The original fixed timestep based on initial speed fails at the finer levels as gas/jet speeds
increase. That is a timestep-policy failure, not proof of physical instability. A separately
recorded policy uses the evolving accepted velocity:
`dt <= CFL/(max|u|/hx + max|v|/hy)`, capped by the original timestep and remaining duration.
Only a stage CFL rejection permits a recorded half-step retry. No state is clipped or damped.

All adaptive runs complete 0.15 s, conserving mass, momentum and symmetry. Kinetic-energy errors
are **8.99%, 8.00% and 7.56%** at 32, 64 and 128 horizontal cells. At 64 cells, CFL values
0.2, 0.1 and 0.05 leave the error around **8.00%**. Height and spread are temporally converged,
but from 64 to 128 cells the conservatively restricted phase-field difference is **2.85%** and
vertical-spread difference **1.037%**. The energy and spatial gates fail even though centroids
and visible symmetry are excellent.

The loss is not attributed to physical viscosity: the model has none. Interface-contact and
unresolved topology changes remain limitations; this is not a validated physical coalescence
model and supplies no evidence that a thin-film method is required.

![Wave errors, force sensitivity and controlled collision interfaces](/docs/project/development/milestones/05/assets/coupled-fluid-v1/coupled-qualification.svg)

## Cost decision and bounded next step

**No complete coupled computational cost per simulated second was measured on the RTX 4070.**
The admission condition failed, so there was no CUDA port, multigrid tuning or performance
benchmark. Instrumented CPU times include Python assembly, sparse factorisation, diagnostics
and full raw-state output; they are not throughput measurements or GPU projections. The prior
constant-density flat-domain pressure timing does not cover the variable-coefficient pressure
solve, geometric transport or interface work here.

Geometric transport and shared momentum fluxes require linear grid traversals; midpoint adds
two pressure projections per accepted step. A general physical interface would also need coherent
geometry updates and a changing pressure system. Their complete cost at equivalent physical
accuracy is unknown. **This candidate has no established credible real-time operating regime.**
That is an accuracy-based no-go, not evidence that the RTX 4070 cannot run a different qualified model.

Do not extend this averaged-mass coupling or tune its damping. The next justified design task
is a common geometric/material description satisfying both staggered mass conservation and
interface pressure work. It must include all interface positions in its tests and demonstrate
that gravity work exchanges the same physical potential energy used by material transport.
For a liquid-only application, a one-phase geometric free boundary with atmospheric traction is
a reasonable narrower direction; embedded-boundary projection provides an established foundation,
not local validation of that coupling.<sup><a href="#ref-s078">S078</a></sup>

If finite-density gas is required, a finer material grid is an established alternative to the
present cell-mass averaging: Rudman's publisher abstract describes a material grid twice as fine
as the velocity/pressure grid. It was not implemented here.<sup><a href="#ref-s081">S081</a></sup>
Neither option is authorised by this report as a production change. Before another coupled
implementation, specify the geometric conservation law, matching momentum fluxes, compatible
pressure/traction and gravity-energy exchange. Then repeat frozen-interface accelerations,
cross-cell translation/shear, waves and collision gates. Benchmark only after they pass together.

## Evidence and preservation

The retained campaign contains **30 streamed experiments and 15,700 initial/stage/accepted states**,
including failed prefixes, plus geometry, hydrostatic, mass-flux and frozen-interface controls.
An independent reader recomputes mass, momentum, divergence and kinetic energy from every raw
state and checks pressure-force and stage-energy closure. Maximum force and kinetic-budget
discrepancies are `1.2e-16 N s/m` and `2.3e-16 J/m`. A complete wave case reproduced with final
sources differs by at most `1.1e-13 m/s` in velocity and retains its failed physical result.

Lossless raw streams, source versions, inputs, ledgers, analyses and plots have checked local and
independent primary-PC copies. The prior pressure feasibility and diagnosis archives are preserved.
All ten production CUDA optimisations, pre-existing Maelstrom work, repository HEADs and indices
remain unchanged. No production Rust/CUDA test or whole-fluid GPU benchmark is claimed here.
There was no history or system-setting change.

## References used

- <a name="ref-s078"></a> S078: Batty (2010), *Simulating Viscous Incompressible Fluids with Embedded Boundary Finite Difference Methods*. [Reading record](/docs/research/sources/078-batty-embedded-boundary-fluids.md).
- <a name="ref-s080"></a> S080: Arrufat et al. (2021), *A mass-momentum consistent, Volume-of-Fluid method for incompressible flow on staggered grids*. [Reading record](/docs/research/sources/080-arrufat-consistent-vof.md).
- <a name="ref-s081"></a> S081: Rudman (1998), *A volume-tracking method for incompressible multifluid flows with large density variations*. [Reading record](/docs/research/sources/081-rudman-volume-tracking.md).
