# Calibration and settled-motion qualification of the C2 reference

**A lattice-derived particle-site correction removes the demonstrated bulk calibration bias.
The evidence does not establish a combined physically qualified operating regime.** The corrected
collision still needs spatial resolution, and making it quieter with a specified Newtonian
viscosity exposes a separate boundary-consistency failure in the viscosity discretisation.
No production, CUDA, Git-history or system-wide settings changes were made.

This investigation follows the [spatial study](/docs/project/development/milestones/05/shallow-resolution.md).
The [evidence guide](/docs/project/development/milestones/05/assets/calibration-motion-v1/README.md)
owns reproduction commands, exact requests, complete scheduled particle states, every-step energy
ledgers, source identities and raw readback. Earlier archives are preserved. The production
[numerical contract](/docs/project/development/milestones/00/phases/phase-00-design-contract.md)
and [performance plan](/docs/project/development/milestones/05/performance-plan.md) remain unchanged.

## Experimental model and criteria

The experiments use a separate binary64 C++ reference on the primary Ryzen 9 7900X. EPQ remains
at `814f88a7f4122b1b24ea645b210d89e1200a0c44`, Maelstrom at
`250932784790ba26cdc55fc38a877ccefacbf054`, with unrelated existing changes preserved. Native source
hashes are checked separately. The instrumented raw solver reproduces the retained coarse
collision observations exactly. Bitwise agreement checks the instrumentation; physical admission
uses independent references. Small timestep-representation differences in some refined requests
are explicit in the recorded commands and are assessed physically.

The fixed collision retains M=52.23230175835605 kg, the 1.2 × 1.2 × 0.8 m box, two 0.3 m blocks,
velocities ±0.5 m/s and gravity 9.81 m/s². Spatial refinement keeps total mass and geometry fixed,
with Δx=0.3/n, N=2n³, m=M/N, density support h=2Δx, collision inset 0.5Δx and separation target
0.51Δx. Eight Jacobi passes, εh²=0.02, correction scale 0.5 and zero artificial pressure are held
fixed except in the explicit iteration controls. The usual timestep is (1/240)(6/n) s.

The independent settled reference is H*=M/(1000A)=54.40864766495422 mm and centroid H*/2.
A second full-width tank has fixed initial geometric depth 0.3 m, with mass inherited consistently
from particle volume; its reference depth is 0.290179454213089 m. Static shallow pools retain the
collision's mass and footprint. References always use recorded physical mass, rather than fitting
wet area or redefining rest density after observing a result.

Before experiments, the protocol retained positive compression p95 ≤5%, maximum ≤25%, separation
≥0.5Δx, plane violation ≤10⁻⁶ m, settled centroid error ≤5%, height and independently reconstructed
volume errors ≤10%, and interparticle density-field p95 error ≤10%. It additionally required
**≤1% centroid error at the two finest tested endpoints** to demonstrate removal of calibration
bias, rather than merely crossing the original 5% screen. Quietness remains ≤0.00125 J/kg over
t=5–6 s. Mechanical energy may not exceed its initial value by more than 0.004905 J/kg.
Stage/gravity energy identities must close within 10⁻⁹ J/kg, internal impulses within 10⁻¹⁰ m/s,
and viscosity must not increase kinetic energy beyond 10⁻¹² J/kg. The independent viscosity
decay-amplitude budget is 5%. No threshold was loosened after a failure.

Particle observations are saved every 0.05 s, with independent KD-tree density/geometry audits.
Complete energy and momentum ledgers are saved at every accepted step. Density and surface extrema
are therefore sampled bounds; energy/quietness checks also use the full accepted-step ledger.
The field probes and volume reconstruction retain the spatial study's independent continuum-slab
comparison, threshold sensitivity and explicit convolution calibration. Neither feeds a correction
back into the solver. The reported height remains a particle-envelope proxy.

## Separating physical mass from particle-site calibration

The inherited lattice mass makes particle-site density 1000 kg/m³ while the initial geometric mass
density is 967.2648473769639 kg/m³. Changing m alone would change this fixed-mass experiment, and
would not remove the underlying dimensionless kernel-sum discrepancy.

The new correction uses the physical particle-volume spacing, not the observed centroid:

```math
\ell=(m/\rho_0)^{1/3},\qquad
B=m\sum_{\mathbf k\in\mathbb Z^3}W(\ell\mathbf k,h)-\rho_0,
\qquad \rho_{i,c}=m\sum_jW(\mathbf x_i-\mathbf x_j,h)-B.
```

At the tested fixed h/Δx, **B=32.2382586510778 kg/m³** at every resolution. The sum is finite
because the kernel has compact support. It makes the particle-site density exact for the physical
rest cubic lattice. B is constant during a run, so its position derivative is zero: the matching
analytic gradient and the unit-integral C2 kernel remain unchanged. Physical mass, initial geometry,
support and hydrostatic references also remain unchanged. Off-particle density uses the original
unit-integral kernel with the actual masses, without this particle-site subtraction.

The fixed-mass initial cube envelopes occupy 54 litres, while M/ρ₀ is 52.232 litres. They are a
dilute particle initial condition, not fully dense continuum cubes. This limits interpretation of
the collision transient even when the final hydrostatic reference is unambiguous. Separate
geometric-mass controls set m=ρ₀Δx³, giving collision M=54 kg, H*=56.25 mm and tank M=288 kg,
H*=0.3 m. Crossing raw/self calibration at unchanged particle positions isolates changing mass
from correcting the estimator. Their independent references change explicitly; they are not
silently substituted into the fixed-mass spatial ladder. Geometric mass gives B=33.8430086773
kg/m³ and makes wall sample mass consistent with geometric wall-cell volume.

The density-estimation literature motivates constant self-contribution subtraction. This particular
coefficient is a project lattice calculation, not the published fitted neighbour-count law, and
SPH conservation claims do not automatically qualify a PBF projection.<sup><a href="#ref-s071">S071</a></sup>

In the 25 mm deep tank, changing only this convention moves final centroid error from **+3.147%
to −0.258%**. Worst settled field error changes from 3.725% to 3.370%; corrected particle-site
compression stays below 0.780% p95. Settled kinetic energy remains small, about 5.48×10⁻⁵ J/kg.
Independent impulse and energy accounting pass. This is evidence for the proposed calibration
cause, rather than a centroid fit or a loss of physical mass.

The geometrically consistent mass control independently confirms the mechanism. With tank M=288
kg and reference depth 0.3 m, raw calibration gives **+3.455% centroid error** and injects up to
**0.384336 J/kg** above initial mechanical energy. Changing only its site estimator gives
**−0.229%**, 3.013% field error and no accepted energy growth. Collision mass correction alone
likewise injects 0.160174 J/kg; adding the independently derived site correction removes that
initial source, but its few-layer centroid and motion screens still fail. Physical geometric
mass and point-site calibration must be consistent; simply replacing the mass formula is insufficient.

A separate ratio control divides particle-site density and its gradient by the physical-rest
lattice normaliser 1.03223825865108. It gives −0.257% deep-tank error, independently supporting
the calibration mechanism. It rescales gradients and would change the kernel integral if extended
to a continuous density field; it has not received the complete spatial qualification of the
constant-subtraction candidate. It is not adopted.

Boundary quadrature is isolated separately: changing only each fixed wall sample's represented
volume from m/ρ₀ to its geometric cell volume Δx³ moves the 25 mm corrected collision from
−2.097% to −1.733% centroid error. The raw control moves from +0.995% to +1.395%. Boundary-volume
consistency matters at finite resolution, but this small effect is distinct from the bulk bias.
It does not cure the corrected coarse collision's field or motion failures.

Correction does not rescue an unresolved free surface. At 50 mm spacing both raw and corrected
collisions retain −8.103% centroid error. At 25 mm, the corrected collision has **−2.097% centroid
and 10.838% field error**, compared with +0.995% and 6.696% before correction. The previous coarse
agreement partly compensated errors. At 16.67 mm the corrected centroid error falls to **−1.154%**
and field error to **3.864%**, but the predefined strict 1% calibration budget still fails there.
At 12.5 mm, corrected centroid error reaches **−0.407%**, with height error −0.224%, volume error
−1.054% and field error 4.462%. Unlike the raw curve, its physical centroid error decreases
monotonically through the spatial ladder. No coarse crossing of zero is treated as convergence:

| Spacing (mm) | Raw centroid error | Corrected centroid error | Corrected field error | Corrected maximum settled K (J/kg) |
|---:|---:|---:|---:|---:|
| 50.00 | −8.103% | −8.103% | 38.134% | 0.003436 |
| 25.00 | +0.995% | −2.097% | 10.838% | 0.001913 |
| 16.67 | +2.622% | −1.154% | 3.864% | 0.003877 |
| 12.50 | +3.312% | −0.407% | 4.462% | 0.004025 |

![Calibration and independent fluid-field convergence](/docs/project/development/milestones/05/assets/calibration-motion-v1/calibration-spatial.png)

At 25 mm, halving the timestep changes corrected final centroid error from −2.097% to −2.081%;
16 passes give −2.174%. Those small changes and much smaller density residuals do not repair the
remaining spatial/surface error. The regularisation and correction scale were not tuned jointly
with calibration. At 16.67 mm, half dt gives −0.952% and sixteen passes −1.153%. Across the
recorded temporal/iteration comparisons, the largest mean-centroid change is **0.0616 mm**, within
the predefined 1% target-centroid change budget. Quietness remains failed. The corrected deep-tank
spatial pair passes all declared case checks, including strict calibration; its centroid error
falls from −0.386% at 50 mm to −0.258% at 25 mm.

## Accounting for motion through the solver

Each step records K=mean(|v|²)/2, U=g mean(y), linear/angular momentum per unit mass, and signed
kinetic/potential work across density correction, plane projection, particle separation and
viscosity. Correction magnitudes, active constraints, boundary activity and reconstruction errors
are retained. Intermediate kinetic energy uses v_stage=(x_stage−x_old)/dt; the final viscosity stage
uses actual accepted velocities. This gives a telescoping account of the trajectory actually taken,
not an assumption that a component's positive work independently caused the final motion.

Independent particle states reproduce accepted K, U and momentum. Density's net internal impulse
is separated from its fixed-wall impulse; contact and viscosity pair impulses cancel. Gravity,
wall-density impulse and plane impulse close the total fluid momentum budget. Fixed walls can
exchange momentum with the liquid, so conservation does not mean fluid momentum must remain zero.
The reconstructed velocity agrees with predicted velocity plus accumulated displacement/dt.
There is no evidence of a duplicate velocity update or unaccounted momentum source.

That algebraic closure does not make a miscalibrated pressure correction physically safe. A
separate free cluster begins on its physical-rest lattice, with zero gravity, no wall/contact
interactions, a prescribed mild compressive strain and nonzero angular momentum. Its initial
K is **0.0196885 J/kg**. The raw estimator falsely reports bulk compression even before prediction;
only the site convention changes between the matched runs:

| dt (s) | Raw final K (J/kg) | Corrected final K (J/kg) | Corrected angular-momentum drift |
|---:|---:|---:|---:|
| 1/240 | 0.079087 | 0.017576 | 0.1892% |
| 1/480 | 0.260272 | 0.017589 | 0.0950% |
| 1/960 | 0.965221 | 0.017596 | 0.0476% |

The raw maximum energy increases above the initial value are **0.05940, 0.24362 and 0.97988 J/kg**.
All work is in the density stage; gravity, plane and contact work are zero. A spurious finite
position correction becomes Δv=Δx/dt during the otherwise correct velocity reconstruction.
Its kinetic contribution therefore grows towards a 1/dt² dependence as dt shrinks. This is a
demonstrated calibration-driven numerical energy source. The corrected version instead removes
compressive kinetic energy and converges to a finite result. More accurately enforcing the wrong
density constraint cannot establish physical convergence.

At dt=1/480, increasing passes from eight to sixteen reduces the raw last-pass input residual
from 0.1303% to 0.00490%, while final K worsens from 0.260272 to 0.266490 J/kg. Corrected final K
stays 0.0175894 J/kg at both iteration counts. The first-pass displacement evidence is also
distinct: raw maximum corrections approach a nonzero value as dt shrinks, whereas corrected
corrections halve with dt in this prescribed-strain test. Reduced density residual is not a
physical accuracy criterion for a wrongly calibrated constraint.

![Calibration-dependent pressure displacement and timestep energy behaviour](/docs/project/development/milestones/05/assets/calibration-motion-v1/initial-pressure-energy.png)

Linear momentum closes to floating-point accuracy in these unforced tests. Pressure projection
and finite-step velocity reconstruction are **not exactly angular-momentum conserving**: the raw
case retains about 1% angular drift, while corrected drift decreases approximately linearly with
dt. Exact angular conservation is only claimed for the separately tested central viscosity pair
stage. No general conservation claim is inferred from density statistics alone.
Pair corrections are central at their current predicted positions, while reconstructed angular
momentum depends on the old positions crossed with displacement/dt. These separation vectors
differ under shear. The central-force angular-conservation argument therefore does not carry
over exactly to this finite-step position projection; the measured timestep convergence matters.

Positive constraint work alone is misleading. For semi-implicit gravity prediction:

```math
\Delta(K+U)_{\rm prediction}=-\tfrac12g^2\Delta t^2.
```

A stationary constrained particle must recover this integration loss when projection restores its
position. In the deep static tank, positive density/plane work largely cancels that known loss,
while accepted total energy decreases. Treating all positive stage work as injection would
misdiagnose ordinary hydrostatic support.

In the raw 25 mm collision, accepted total energy decreases by **0.0010023 J/kg over t=5–6 s**,
with no positive accepted-energy steps in that interval. K falls from **0.0016605 to 0.0009775
J/kg** while potential energy also decreases. The corrected collision similarly loses 0.0009479
J/kg over that interval. Thus the failing quietness screen is not explained by net energy generation.
The energy loss is not calibrated physical viscosity either: inviscid PBF, contact and projection
already dissipate energy numerically.

Three matched one-second integrations start from the exact five-second observations:

| Diagnostic, 25 mm | Raw final K (J/kg) | Corrected final K (J/kg) |
|---|---:|---:|
| Unchanged continuation | 0.0009775 | 0.0011597 |
| Contact stage disabled only | 0.0009852 | 0.0011906 |
| Initial velocities zeroed only | 0.0002528 | 0.0001940 |

Removing contact barely changes late decay, rejecting contact pumping as its main explanation.
Zeroing velocities is a causal diagnostic, **not a damping policy**. It removes measured kinetic
energy/momentum from the initial state. Some motion returns as the snapshot settles, but its
kinetic gain is accompanied by greater potential-energy loss; total energy still decreases. This
does not prove an energy source in pressure reconstruction.

An unchanged raw continuation to physical t=12 s reaches **7.247×10⁻⁵ J/kg**. The motion is decaying,
not a demonstrated perpetual numerical-energy floor. Insufficient physical dissipation and retained
flow are consistent with the observations. They do not establish correct wave frequencies,
turbulence or a physical decay time. Halving dt or increasing iterations cannot supply a specified
viscosity, and reduced numerical dissipation can leave more motion at the same physical time.
The original t=5–6 s criterion remains failed; the later quiet interval does not retroactively pass it.
That deadline is a qualification requirement, not a physical law that every waterlike or inviscid
pool must satisfy. No independent reference here establishes that this nonlinear collision should
be quiet by five seconds. Changing the deadline or damping until it passes would not validate
the decay dynamics; a material- and boundary-specific physical reference is still needed.

![Kinetic energy and the closed late-time mechanical budget](/docs/project/development/milestones/05/assets/calibration-motion-v1/motion-energy.png)

## Testing dimensional viscosity without fitting away motion

The physical alternatives are isothermal, constant-density Newtonian liquids with ν=10⁻⁶ and
10⁻³ m²/s, equivalent to μ=0.001 and 1 Pa s at ρ=1000 kg/m³. The first is a waterlike approximation;
the official room-temperature water correlation supports that scale.<sup><a href="#ref-s073">S073</a></sup>
The second defines a different synthetic viscous liquid. It cannot be presented as corrected water.
Both values were fixed before fluid experiments. No global damping or fitted XSPH coefficient is used.

The central strain operator uses physical particle volume m/ρ₀ and the three-dimensional factor
2(d+2)=10. Equal-and-opposite central impulses conserve linear/angular momentum, rigid rotation
has zero strain, and an explicit row bound guarantees non-increasing kinetic energy. These
properties are independently checked. The continuum interpretation is the incompressible
Newtonian viscous term; velocity-divergence errors can introduce additional bulk-viscosity
effects in this strain approximation.<sup><a href="#ref-s072">S072</a></sup>

The first prescribed-position periodic shear test rejects viscosity support 2Δx: after one
analytic decay time, amplitude error tends to **50.5%** under spatial refinement. Support 3Δx
still tends to about 7%. Support 4Δx passes the unchanged 5% bulk amplitude budget once there are
at least 18 cells per tested wavelength. Density support remains 2Δx. This is a quadrature change
at fixed material viscosity, not a viscosity coefficient fitted to quietness.

At 25 mm, waterlike viscosity still fails settled quietness. The corrected ν=10⁻³ liquid passes
quietness with maximum K about **0.000510 J/kg**, but has **11.630% field error** and −2.349%
centroid error. At 16.67 mm, it has good field error, but **−1.604% centroid error**, failing the
strict calibration criterion. Density-only or quietness-only success does not qualify it.
At 12.5 mm, the corrected viscous collision passes all aggregate PBF case checks: centroid
−0.897%, field error 2.292% and maximum settled K 0.000388 J/kg. That individual success does
not pass the predefined two-finest-resolution calibration rule, and the independent boundary
material test below still fails at these few-layer resolutions.

A stronger independent boundary test then rejects the low-resolution material interpretation.
In a slab periodic horizontally and free-slip vertically, u_x=sin(2πz/L), uniform through depth,
must decay as exp(−ν(2π/L)²t), independently of slab depth. There is no gravity, pressure projection,
contact or velocity reconstruction in this test. It isolates the implemented viscosity operator
on a prescribed lattice, using an exact Fourier reduction of its horizontal stencil.

With missing fluid neighbours simply omitted, two layers give **39.08%** amplitude error and four
layers about **19.95%**, despite adequate horizontal bulk resolution. At fixed L=0.6 m and H=0.05 m,
refining from 2 to 4, 8, 16 and 32 layers reduces error to **39.08%, 18.92%, 10.02%, 5.87% and 3.87%**.
Half-timestep checks preserve the result. Boundary truncation therefore converges in this test,
but not at the few-layer resolutions of the collision. Merely increasing ν to compensate would
misrepresent the material and is rejected.
An independently assembled operator matrix reproduces native discrete evolution within
8.6×10⁻¹³ in amplitude. Replacing explicit Euler by the exact discrete matrix exponential changes
amplitudes by only about 10⁻⁵, leaving the large shallow-slab physical errors intact. This isolates
spatial quadrature and boundary truncation from timestep integration and implementation mistakes
in the Fourier test.

![Bulk and free-slip slab viscosity qualification](/docs/project/development/milestones/05/assets/calibration-motion-v1/viscosity-qualification.png)

## Outcome and remaining limits

The bulk mass/kernel calibration cause is demonstrated and a minimal isolated correction is
supported. Finite free-surface/boundary errors remain resolution dependent. The motion audit
rejects large sustained late-time energy injection, duplicated velocity reconstruction and contact
pumping as explanations for the observed five-second collision failure. The unforced physical-rest
test nevertheless demonstrates a large initial pressure-energy source when calibration is wrong,
including worsening under timestep refinement. Correcting calibration removes that source in the
test. The collision data support decaying flow with insufficient
specified physical dissipation, while leaving the physical accuracy of that flow's decay unproven.

No combined regime is admitted. The waterlike liquid does not meet the original settling deadline;
the more viscous liquid's improved quietness does not compensate its calibration and boundary-
viscosity failures. A passed bulk shear test cannot certify a shallow free surface. The 32-layer
operator result is not qualification of an unrun full PBF simulation at that resolution.

Further physical work should assign mass from explicitly represented physical fluid volume,
independently correct the site estimator, test consistent wall volumes separately, and resolve
or correct the viscous traction
discretisation at free surfaces/free-slip walls. Material viscosity and wall traction conditions
must remain explicit. No complex thin-film model is justified by these results. No CUDA performance,
production speedup or adoption assessment was undertaken. Instrumented solver wall times in raw
collection metadata are not comparative performance measurements.

The constant correction is calibrated for a cubic physical-rest lattice. Arbitrary disorder,
variable particle volumes/support, curved surfaces, moving walls and binary32 CUDA remain
unqualified. Finite-step pressure angular drift is measured, not claimed absent. All ten retained
CUDA optimisations remain intact; the thirteen native control files still match their retained
hashes. The evidence contains 58 complete simulation streams, 5,156 scheduled particle observations
and 152,256 accepted-step ledger records. Raw particle data total 2,113,012,768 bytes and ledgers
401,219,881 bytes before compression. Twenty-six focused local tests pass. No fresh production
Rust/CUDA qualification is claimed.
All three native fluid executables rebuild exactly from the retained source snapshots on the
primary PC. This establishes source/binary identity; it does not replace physical validation.

## References used

- <a name="ref-s071"></a> **S071** — Dehnen and Aly (2012), density estimation and correction, §2.5.
  [Source record](/docs/research/sources/071-dehnen-aly-sph-convergence.md).
- <a name="ref-s072"></a> **S072** — Koschier et al. (2019), Newtonian and explicit viscosity,
  §§6.1–6.2, maintained author PDF.
  [Source record](/docs/research/sources/072-koschier-sph-viscosity.md).
- <a name="ref-s073"></a> **S073** — IAPWS (2011), liquid-water viscosity correlation, §3.
  [Source record](/docs/research/sources/073-iapws-liquid-water-viscosity.md).
