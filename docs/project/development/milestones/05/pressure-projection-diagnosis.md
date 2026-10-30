# Diagnosis of the C2 pressure projection's tangential-shear failure

**The dominant diagnosed mechanism is a discrete constitutive inconsistency: the particle-site
density constraint gives an incompressible liquid a pressure-dependent shear stiffness.** The
native implementation differentiates and applies that constraint correctly in the tested cases.
Its exact solution can still remove physically admissible shear. No replacement pressure solver
was implemented, and no production, optimisation, history or system-setting change was made.

The [preceding qualification](/docs/project/development/milestones/05/viscosity-traction.md) retains
the 59.1% full-trajectory pressure-mode loss and original physical failures. The new
[evidence guide](/docs/project/development/milestones/05/assets/pressure-diagnosis-v1/README.md)
owns exact requests, complete pressure-iteration arrays, independent matrices, source identities
and durable readback. This investigation stops at diagnosis and a validation strategy.

![Artificial shear modulus, constant-pressure force, spatial convergence to the wrong law and density-versus-shear trade-off](/docs/project/development/milestones/05/assets/pressure-diagnosis-v1/pressure-diagnosis.png)

## Controlled reference and scope

The physical reference is an exactly volume-preserving material map:

```math
x=X+S(Y),\quad y=Y,\quad z=Z,\qquad \det F=1.
```

Uniform physical density stays 1000 kg/m³. For a flat channel, tangential velocity depending
only on height and hydrostatic pressure P=ρg(H−y) require **zero tangential pressure correction**.
A fully periodic sinusoidal S with constant P requires **zero pressure force everywhere**.
The latter removes walls, free surfaces, viscosity, gravity forcing, advection and neighbour
evolution from the counterexample. The acceleration g=9.81 m/s² merely normalises its pressure
P₀=ρgH and reported force errors.

The geometry is H=0.05 m, horizontal periods 0.2 m, physical mass 2 kg, Δx=H/n and m=1000Δx³.
Experiments independently vary n, support q=h/Δx, strain, boundary closure, wall-sample phase,
regularisation, iteration count, timestep and neighbour refresh. There are 70 unique frozen
manufactured geometries, additional small-strain/frozen-graph controls, an independent kernel
Hessian calculation and 16 one-step native pressure-only cases. The native cases have zero
viscosity and no interparticle contact; plane corrections are normal. Every pressure iteration's
positions, constraint values, multipliers and corrections are retained.

The protocol preceded collection. Numerical agreement requires native/independent action error
within 10⁻⁹ at the stated scale and exact-solve residual below 10⁻⁹. Manufactured physical budgets
are 1% for spurious tangential force relative to g and 5% for shear loss. Density residuals are
reported independently. This is not a new long-duration simulation qualification.

## Correct implementation of an inconsistent constraint

PBF restores a sampled per-particle density by position projection and reconstructs velocity
from corrected displacement divided by timestep. Regularisation and finite Jacobi iterations
control that process. These are distinct operations in the original method.
<sup><a href="#ref-s004">S004</a></sup>

The tested constraint is

```math
C_i=V\sum_j W(\mathbf x_i-\mathbf x_j,h)-B(q)-1,\quad
J_{ij}=\partial C_i/\partial\mathbf x_j,\quad V=\Delta x^3.
```

B(q) still correctly calibrates the undeformed cubic particle sites. It is constant and cannot
remove the kernel sum's dependence on isochoric shear. Correct mass calibration at rest therefore
does not imply that C measures geometric density under deformation.

Horizontal translation symmetry allows an exact layer reduction of J. The native Jacobi
denominator is separately computed from **individual three-dimensional particle derivatives**;
using the reduced row norm would incorrectly change the preconditioner. Native sparse Jacobians,
their full row norms, every reduced pressure action and independent point-kernel finite differences
agree. The largest reduced Jacobian discrepancy is about 5.2×10⁻¹² m⁻¹ and point finite-difference
error about 1.1×10⁻⁷ m⁻¹. The instrumented baseline reproduces the existing reference's raw states
byte for byte. These verify instrumentation and implementation, not physical correctness.

## Pressure introduces artificial shear elasticity

An independent infinite-lattice calculation evaluates the C2 Hessian under uniform affine shear.
For small shear γ:

```math
C(\gamma)-C(0)=\tfrac12 b(q)\gamma^2+O(\gamma^4).
```

Under prescribed pressure, the discrete virtual-work potential contains P C. Its shear term is
therefore equivalent to an artificial modulus **Gnum=P b(q)**. An incompressible Newtonian fluid
has no such pressure-derived shear modulus. The coefficient comes from the kernel Hessian; it
is not fitted to a simulated trajectory or the manufactured force.

| Support q | Dimensionless b(q) | Gnum at mean hydrostatic P=245.25 Pa |
|---|---:|---:|
| 2 | +0.0377438 | +9.2567 Pa |
| 3 | −0.00835786 | −2.0498 Pa |
| 4 | +0.00217659 | +0.5338 Pa |

Changing support can change the sign of the response, not merely its magnitude. A negative
manufactured-pressure tangent stiffness can promote shear rather than restore it; this is not
a physical viscosity adjustment.

The independently predicted long-wave constant-pressure force is

```math
a_x=(P/\rho)\,b(q)\,S''(y).
```

For q=2, a separate periodic sinusoidal manufactured calculation approaches this **wrong,
nonzero force** as spatial resolution increases. Its relative discrepancy from the Hessian
prediction falls from 2.26% at 12 layers to 0.570% at 24, 0.321% at 32 and **0.0807% at 64**.
Refinement is resolving the artificial constitutive law. Since b depends on q, not Δx,
decreasing Δx at fixed q cannot remove that law.

The finite-strain constant-pressure counterexample is equally direct:

| Periodic layers, q=2, γ=0.3 | False tangential RMS force / g | Offline same-J equality projection loss |
|---|---:|---:|
| 8 | 3.313% | 81.71% |
| 12 | 3.476% | 76.20% |
| 24 | 3.588% | 72.48% |
| 64 | 3.622% | 71.38% |

The physical force is zero. A zero-pressure-offset invariance is lost: Jᵀ1 is nonzero in this
periodic fluid. Removing the mean density equation **only as an offline attribution control**
reduces the spurious mode removal dramatically. Odd layer counts retain the defect, excluding
an even-grid checkerboard as its necessary cause. At q=2 these strained periodic constraints
are all positive, so the counterexample is not created by forcing tensile rows that the native
compression clamp would exclude.

An offline SVD projection onto the same J's nullspace eliminates iterative error and regularisation
from that kinematic test. It is not the nonlinear, unilateral native position solver and does not
predict its final active set or numerical loss percentage.
At γ=0.01 it can remove almost all the physical shear while satisfying its discrete equations.
The spurious mean-density equation becomes a weak but nonzero constraint; enforcing it exactly
is not equivalent to conserving geometric volume. Other supports can have different active sets;
their all-row exact solves are mathematical diagnostics, not native compression-only predictions.
This is consistent with the known distinction between SPH smoothing error and particle
quadrature/constant-field consistency. <sup><a href="#ref-s076">S076</a></sup>

## Connection to the retained failure

A one-step pressure-only replay starts from the retained four-layer state at 0.2 s. It reproduces
the original complete model's next pressure-stage modal change within **3.3×10⁻¹⁵ m/s**. Viscosity
is disabled during replay; it is present only in the recorded initial history.

The replay's normalised shear-amplitude correction is −2.14074×10⁻⁵ m/s. Decomposing its unchanged
multiplier into spatial mean and fluctuation attributes **86.3% of that correction to the constant
component**. Its effective mean pressure is 247.54 Pa, close to the independent hydrostatic mean
245.25 Pa. The pressure magnitude is reasonable; its tangential constitutive response is not.

This links the manufactured mechanism to the actual failed solver. It does **not** claim that
86.3% of the whole earlier 59.1% loss has been apportioned: only one complete-model stage was
replayed. Full-history contributions are nonlinear and were not recomputed. Subtracting pressure
mean or dropping a constraint is not proposed as a fix: the free surface fixes pressure and normal
traction, so a periodic attribution control cannot simply be transplanted into that problem.

## Separating the other mechanisms

**Free-surface support.** The natural surface creates a particle-site density deficit and inactive
compression rows even in an undeformed constant-density slab. Closing the top with mirrored
support removes that deficit, but strained closed and fully periodic cases still alter valid
shear. Surface support changes the active set, normal escape modes and pressure response; it
is an additional modelling problem, not a necessary cause of the demonstrated bulk inconsistency.
No additive percentage of the full failure is assigned to it.

**Boundary treatment.** Translating the fluid by 0.37Δx relative to a flat bed leaves the mirrored
operator unchanged. Fixed bed samples instead change manufactured tangential force RMS/g from
0.00912 to 0.01551. This isolates the previously identified fixed-sample artefact. The present
mirrored model still fails without any boundary, so correcting that artefact cannot cure the
remaining pressure physics.

**Regularisation.** Setting εh² from 0.02 to zero changes the captured replay's wrong shear
correction by only **0.143%**. The ε-free exact constraint also fails the manufactured reference.
Regularisation can suppress or soften the response; it does not repair the constraint's meaning.

**Neighbour evolution.** Freezing neighbour identities while updating positions and reflected
coordinates changes the replay correction by about **1.25×10⁻⁹ relative**. Small-strain periodic
counterexamples occur before any neighbour identities change. Deformation of kernel weights
already suffices. This excludes neighbour churn as a necessary cause; it does not assert that
later disorder and topology changes never matter.

**Iteration convergence.** In the zero-force manufactured relaxation, increasing 24 passes to 96
reduces final p95 compression from 2.81×10⁻⁵ to 1.15×10⁻⁹, while the wrong shear displacement
increases by 3.24%. Finite fixed-pass convergence also varies with resolution: the full particle
row norm and low-frequency reduced operator scale differently. Neither a small scalar residual
nor extra passes establishes correct velocity.

**Timestep dependence.** With the same manufactured zero-velocity, zero-force point configuration,
halving Δt leaves the projected positions identical and doubles the reconstructed false velocity.
The sampling error in C is not proportional to Δt². Dividing its positional restoration by Δt
therefore does not make it a consistent physical pressure correction. This is a controlled
counterexample, not a claim that every full simulation doubles its error when Δt is halved.

**Support versus spacing.** Holding q fixed leaves the artificial modulus. Increasing q while
also reducing physical h improves the manufactured force: the sequence (n,q)=(12,2), (24,3),
(64,6) reduces false tangential RMS/g from 0.03476 to 0.01007 to 0.000645. This separates
neighbour-quadrature improvement from spatial refinement. It does not qualify a production q:
support changes pressure conditioning, the compression active set and surface resolution, and
the previous wider-support coupled failures remain failures.

## Classification and go/no-go decision

The evidence supports a **discrete formulation inconsistency**, not a newly discovered coding
error in the tested corrected gradient or transpose. It is a limitation of this particular
point-density PBF constraint at fixed support-to-spacing ratio. It is not a theorem that all
position-based or particle pressure methods must lose valid shear: an incompressibility
constraint consistent with volume change would place this motion in its nullspace.

**NO-GO** for more parameter fitting, production qualification or performance optimisation of
the current fixed-q model. More iterations solve its wrong equations more closely. Global mass
retuning, damping or compensatory vorticity would not remove the demonstrated pressure law.

**GO only for a bounded consistency-first pressure-discretisation feasibility study.** The evidence
justifies considering a volume-consistent constraint or a compatible discrete divergence/pressure
gradient projection. It does not yet select an algorithm, require abandoning PBF infrastructure,
or authorise implementation of another full solver. Gradient normalisation alone would also
need a matching constraint/volume derivation and conservation assessment.

Before implementation, a candidate needs this validation strategy:

1. Demonstrate periodic constant-pressure invariance, physical shear in the divergence nullspace,
   and linear hydrostatic pressure without tangential force, on regular and perturbed sampling.
   Preserve the paired divergence/gradient work identity and appropriate momentum conservation.
2. Establish spatial consistency with Δx, h and neighbour count controlled separately. Check
   nullspaces, conditioning and velocity/force errors after an exact solve before selecting a
   practical iteration policy. A small density or linear-system residual is insufficient.
3. Derive wall-normal pressure conditions and free-surface pressure/volume support explicitly.
   Do not replace the surface by a particle-site density fit or remove its pressure mean ad hoc.
4. Only after those operator gates pass, return to the retained viscous shear, hydrostatic,
   transient-density, settling and convergence tests together. CUDA cost and all ten retained
   optimisations remain a later, separate qualification.

The bounded diagnosis is complete. It has not supplied a production pressure policy or a new
physical model ready for qualification. The verification suite passes 52 tests of implementation,
references, instrumentation and documented counterexamples; the manufactured **physical** gates
fail for the existing model. Complete new raw evidence and checked source snapshots are retained
locally and on the primary PC, with the preceding archive unchanged.

## References used

<a name="ref-s004"></a> **S004** — Macklin and Müller (2013), *Position Based Fluids*, §3–4 and
Algorithm 1. [Reading record](/docs/research/sources/004-macklin-muller-position-based-fluids.md).

<a name="ref-s076"></a> **S076** — Litvinov, Hu and Adams (2015), *Towards consistence and
convergence of conservative SPH approximations*, institutional abstract read.
[Reading record](/docs/research/sources/076-litvinov-sph-consistency.md).
