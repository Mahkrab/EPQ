# Viscosity, boundary traction and settling qualification

**The experimental full PBF model is not ready for production qualification.** A dimensional
viscosity operator can reproduce the tested analytical shear modes, including free surfaces and
solid traction. Coupling it to the corrected C2 density projection introduces large errors under
gravity. Low compression, conservation, energy decay and apparent quietness do not establish
correct fluid dynamics. No production implementation or performance optimisation was retained.

This follows the [calibration and motion study](/docs/project/development/milestones/05/calibration-motion.md).
The new [evidence guide](/docs/project/development/milestones/05/assets/traction-qualification-v1/README.md)
links protocols, raw observations, exact commands, independent calculations and integrity checks.
The previous archive and its original acceptance results remain intact. This is a physical
qualification report, not a change to the production numerical contract or performance gate.

![Operator convergence, failed coupled decay, pressure quadrature and hydrostatic motion](/docs/project/development/milestones/05/assets/traction-qualification-v1/physical-qualification.png)

## Physical references and acceptance

The material models retain density 1000 kg/m³. Waterlike kinematic viscosity is 10⁻⁶ m²/s;
the separate viscous Newtonian model uses 10⁻³ m²/s, or dynamic viscosity 1 Pa s. The latter
is not a substitute value for water. The room-temperature water scale is supported independently.
<sup><a href="#ref-s073">S073</a></sup>

For unidirectional velocity independent of the flow direction, convection vanishes. The momentum
equation reduces to viscous diffusion after the hydrostatic pressure balances gravity.
<sup><a href="#ref-s075">S075</a></sup> The following are direct substitutions into that equation,
with the stated flat boundaries, rather than predictions fitted to a PBF trajectory:

```math
u_x=U f(y,z)e^{-\nu k^2t},\quad K=K_0e^{-2\nu k^2t},\quad \tau=(\nu k^2)^{-1}.
```

The profiles are sin(2πz/L) with periodic horizontal directions and uniform depth; cos(πy/H)
between free-slip planes; sin(πy/H) between no-slip planes; and sin(πy/2H) above a no-slip bed
with a traction-free upper surface. Free-slip means zero normal velocity and tangential traction;
no-slip fixes velocity at the stationary wall. A free fluid surface supplies natural traction,
without a solid-wall velocity condition. Newtonian stress supplies the dimensional traction.
<sup><a href="#ref-s072">S072</a></sup>

Before coupled tests, the protocols required at most 5% amplitude, decay-rate, velocity L2 and
traction error; energy identities within 10⁻⁹ J/kg; internal linear/angular impulse within
10⁻¹⁰ m/s; and no viscous kinetic-energy increase above 10⁻¹² J/kg. Physical screens also retain
p95 compression ≤5%, maximum ≤25%, separation ≥0.5Δx, plane violation ≤10⁻⁶ m, centroid error
≤1%, and height/volume error ≤10%. The preceding study's independent density-field 10% screen
and original K≤0.00125 J/kg over 5–6 s remain separate results. No limit was relaxed to obtain
a pass. Density and geometry extrema use scheduled states; energy and quietness use every
complete accepted-step ledger record.

Fixed-geometry operator refinements use H=0.05 m, L=0.2 m and 2, 4, 8, 12, 16 and 24 layers.
Their retained observations cover two decay times. Coupled shear tests cover one decay time,
rounded to 1.0125 s. A one-decay-time admission is not a two-decay-time qualification: relative
amplitude error accumulates with time. Both windows are explicitly assessed.

## Separating surface truncation from depth resolution

At the exact earlier horizontal geometry, L=0.6 m and Δx=0.025 m, the old omitted-neighbour
central pair operator has approximately 39.08% error at two layers and 19.95% at four.
This comparison holds spacing fixed, so H is 0.05 and 0.1 m respectively. It is distinct from
the fixed-H spatial-refinement family.

The new natural-surface edge operator reduces those errors to **1.676% and 1.771% at τ**,
and maximum 3.379% and 3.574% through 2τ. The corresponding free-slip mirror cases also pass.
Depth-uniform horizontal shear therefore does not have an intrinsic 39% two-layer limitation.
The old boundary truncation and constitutive quadrature were inadequate for that flow.

Vertical gradients do require depth resolution:

| Profile and layers | Amplitude error at τ | Maximum amplitude error through 2τ | Maximum traction error through 2τ |
|---|---:|---:|---:|
| No-slip/no-slip, 4 | 16.46% | 35.62% | 17.97% |
| No-slip/no-slip, 8 | 4.16% | 8.49% | 4.74% |
| No-slip/no-slip, 12 | 1.85% | 3.74% | 2.13% |
| No-slip/no-slip, 24 | 0.463% | 0.929% | 0.534% |
| No-slip/free surface, 4 | 1.56% | 3.34% | 3.46% |
| No-slip/free surface, 8 | 0.716% | 1.44% | 0.958% |

The free-slip/full-depth mode has the same amplitude convergence as the no-slip/full-depth mode.
Eight layers suffice for the tested full-depth mode through τ; **twelve are needed through 2τ**
under the unchanged 5% relative-amplitude budget. Four pass the tested mixed quarter-wave mode
through 2τ. The two finest endpoints pass and errors decrease with refinement. These are bounds
for specified modes and horizons, not a universal minimum layer count for arbitrary liquid motion.
A single natural particle layer has a rank-deficient three-dimensional gradient and is rejected.

## Experimental viscosity and boundary construction

The candidate reconstructs a first-order-consistent velocity gradient from local moment matrices.
For each neighbour edge it adds the velocity-jump residual to the mean reconstructed gradient,
then integrates symmetric-strain dissipation using positive, normalised C2 edge weights and
real fluid volumes. The force is the exact velocity adjoint of that dissipation functional.
Its coefficient is physical viscosity; there is no fitted velocity damping coefficient.
Rigid-motion invariance and linear-gradient consistency motivate conservation checks, rather
than establishing physical accuracy by themselves. <sup><a href="#ref-s074">S074</a></sup>

Free surfaces add no ghost mass or exterior dissipation volume. Solid mirrors extend gradient
support with tangential-even/normal-odd velocity for free-slip, and all-odd velocity for no-slip.
The full adjoint includes those mappings, hence the wall reaction. Ill-conditioned gradients
above 10⁶ are rejected. An earlier nodal-strain version passed smooth shear but left an alternating
non-rigid velocity pattern undamped; its failure is retained and it was excluded from coupled PBF.
Edge reconstruction removes that demonstrated null mode without an extra damping parameter.

Seven native force fields agree with independently assembled Fourier operators within 1.2×10⁻¹³
m/s². Regular and 8% perturbed free clouds preserve rigid motion, reproduce affine constitutive
power, conserve internal linear/angular impulse and pass a finite-difference dissipation-gradient
check. Prescribed analytical velocities on sheared lattices and actual deformed PBF positions
also remain within the 5% rate/traction budgets. These checks bound the operator's demonstrated
scope; they do not qualify arbitrary disordered free surfaces.

The coupled reference integrates viscosity with backward Euler, solving to relative residual
10⁻¹¹. The audit separates physical dissipation from the time-discretisation loss:

```math
\Delta K=-\Delta t\,\mathcal P(\mathbf v^{n+1})
-\tfrac12\langle|\mathbf v^{n+1}-\mathbf v^{*}|^2\rangle.
```

Every completed viscous stage loses or preserves kinetic energy; the identity closes well inside
10⁻⁹ J/kg. Dimensional viscosity scaled by 1000 scales the analytical clock by 1000, without
changing the dimensionless spatial error. Approximate PBF incompressibility can still introduce
bulk-strain effects; the tests do not qualify a compressible material law.

## Coupled pressure and traction failures

The new channel is 0.2×0.2 m horizontally, periodic in x/z, with 0.05 m fluid depth and a bed at
y=0. Its mass is exactly 2 kg at every resolution: m=1000Δx³. Baseline pressure uses corrected
C2 support 2Δx, the lattice-derived constant site bias, εh²=0.02, correction scale 0.5,
24 pressure passes, Δt=1/480 s, inset 0.5Δx, contact distance 0.51Δx and no artificial pressure.
Viscosity support remains 2Δx. The primary physical runs used the PC's CPU reference; production
and CUDA source were not involved.

First, fixed bed density samples produce **spurious tangential pressure traction**. In the
four-layer mixed shear with U=0.01 m/s and gravity, their cumulative tangential pressure impulse
is −0.009462 m/s. The shear reverses despite accurate height and low compression. Flat-bed
pressure support should be invariant under translation along the bed.

A controlled replacement reflects current fluid positions for density support, includes all
reflected-target/self derivatives, and uses the full constraint transpose. It adds no real mass.
The net tangential pressure impulse falls to round-off. An independent finite-difference probe
on a sheared, perturbed cloud verifies the actual native Jacobian, including normal ghost and
self derivatives, within 8.84×10⁻⁸ m⁻¹; native correction action agrees within 1.4×10⁻¹⁷ m.
This removes the fixed-sample traction defect, but **does not qualify the full model**:

| Mirrored pressure support | Final shear amplitude error | Maximum sampled p95 compression | Final centroid error |
|---|---:|---:|---:|
| 4 layers, g=0 | +1.72% | <0.000001% | +0.0367% |
| 4 layers, g=9.81 | −86.10% | 0.00684% | −0.00395% |
| 8 layers, g=9.81 | −144.37% | 0.1381% | −0.0978% |
| 12 layers, g=9.81 | −167.94% | 0.3851% | −0.2768% |
| 4 layers, half timestep | −87.65% | 0.00172% | −0.00120% |
| 4 layers, 48 passes | −86.10% | 0.000235% | +0.00122% |

Errors below −100% mean reversal of the shear mode. Gravity is exactly balanced by hydrostatic
pressure in the analytical reference, so the correct tangential decay is the same as at g=0.
The gravity-free mixed and horizontal controls pass their one-τ case screens. A free-slip-bed
horizontal shear also fails with gravity, ruling out no-slip treatment alone as the explanation.
U=0.1 m/s and a separately hydrostatically conditioned initial state both fail as well.
The conditioned state's removed residual kinetic energy was only 1.93×10⁻¹⁷ J/kg; it defines a
new analytical initial-value test, not a quieter continuation or a replacement settling result.

A modal stage ledger reproduces the uninstrumented raw trajectory byte for byte. Pressure
corrections remove 0.002954 m/s of the initial 0.005 m/s shear projection—**59.1% of its initial
value**—although the analytical tangential pressure force is zero. Global tangential momentum
still balances; pressure redistributes the profile. Contact is inactive and plane corrections
are normal. This directly identifies pressure coupling as a cause of the wrong decay, independently
of the viscosity energy sign. Additional pressure iterations improve density without fixing it.

Independent volume-preserving lattice calculations provide a related spatial explanation:
at shear strain 0.3, h=2Δx gives a spurious tangential/normal pressure-gradient ratio of −0.5545%.
The calibrated site density also changes under isochoric shear. Halving Δx at fixed h/Δx leaves
these dimensionless defects unchanged. Constant cubic-site calibration does not establish
shear-consistent pressure quadrature. At h=4Δx the force leakage drops to −0.00736%, but this
alone does not resolve free-surface or coupled pressure accuracy.

Changing only pressure support confirms that sensitivity without providing a solution. At
h=3Δx, eight-layer shear has +29.27% final amplitude error and 17.50% maximum velocity L2 error.
At h=4Δx, tangential amplitude initially looks close, but velocity L2 error is 10.03 times its
initial RMS at 0.05 s, predominantly additional motion. The latter run was rejected under the
predefined transient gate and stopped; its original request, produced raw prefix, ledger and
termination reason are retained. No full-duration or settled pass is claimed for it.

Pressure-induced profile redistribution is demonstrated. Kernel quadrature is an independently
demonstrated contributor consistent with the support controls. The remaining contributions from
free-surface pressure deficiency, regularisation and changing neighbours are not uniquely separated;
the evidence does not justify declaring any one pressure reformulation solved.

## Settling and the five-second requirement

For a specified shear mode the independently justified threshold time is
ln(K₀/Klimit)/(2νk²), when K₀ exceeds the limit. With U=0.1 m/s, H=0.05625 m and a no-slip bed/free
surface, waterlike viscosity needs **444.43 s** to halve K from 0.0025 to 0.00125 J/kg; K at five
seconds is 0.0024806 J/kg. The viscous model reaches the same threshold in 0.444 s. A free-slip
horizontal periodic mode of wavelength 0.8 m needs 5618 s and 5.618 s respectively. Uniform
tangential translation in a periodic free-slip channel never decays: momentum conservation
forbids viscosity from removing it. These results follow from viscous diffusion, not a quietness
fit. <sup><a href="#ref-s075">S075</a></sup>

Thus five seconds is not a material-independent physical law. It can be a separate application
requirement, or an appropriate deadline for a specified sufficiently viscous bounded flow. It
cannot justify increasing water viscosity or adding arbitrary damping. The revised *experimental
physical assessment* compares decay and traction with the applicable reference; it does not
erase the original quietness failures or change the production criterion. In particular these
shear examples do not predict nonlinear collision/sloshing decay with different wall conditions.
Prior collision failures remain failures; a closed free-surface reference is still needed before
reclassifying their remaining motion as physically expected.

The six-second hydrostatic control illustrates the distinction. Its maximum K over every accepted
step at 5–6 s is 1.553×10⁻⁷ J/kg, passing original quietness. Its final centroid error is −0.613%,
but free-surface interparticle density-field p95 error is **16.61%**, failing the preserved 10%
field screen. It also develops small motion after being almost stationary near one second.
A continuum flat hydrostatic state should stay at rest. The viscous stages never inject energy;
the observed rearrangement releases gravitational potential as the discrete surface/packing
changes. Quietness and a closing energy ledger cannot make this an accurate hydrostatic solution.

## Decision, supported scope and cost

The isolated viscosity reference supports the tested Newtonian shear modes, dimensional viscosity,
flat slip/no-slip traction and natural surfaces within the specified spatial and temporal bounds.
For a two-τ qualification across both tested full-depth boundary types, twelve layers are the
smallest passing tested depth; the particular mixed quarter-wave passes from four. Arbitrary
thin films, rank-deficient layers, strongly disordered support, moving/curved walls, compressible
constitutive response and long-time coupled flows remain unqualified.

**No combined physically acceptable gravity-supported PBF operating regime has been established.**
There is no defensible least-cost production parameter recommendation from this study. The next
physical work must address consistent pressure/incompressibility and free-surface support under
shear; tuning damping, iterations, timestep or a kernel radius against one scalar output is not
supported. A complex thin-film method was not introduced and these failures do not demonstrate
that one is necessary.

No CUDA port, real-time benchmark or further performance optimisation was attempted. Instrumented
CPU elapsed times are retained as operational observations; concurrent runs, stage ledgers and
different formulations prevent comparative performance claims. Resolved gradients and the full
adjoint add work, and finer spatial resolution increases particle count substantially, but no
production cost or speedup is inferred before the physics passes.

Verification comprises 41 focused/reference regression tests, native/Python force agreement,
finite-difference viscosity and pressure checks, independent scheduled density/field/volume audits,
and accepted-step energy accounting. All 508 checksums from the preceding archive were read back
successfully. The new evidence has a checked second copy on the primary PC. All thirteen retained
native source hashes and both repository HEADs remain unchanged; existing unrelated work is
preserved. No Git history, branch, tag, gitlink or system-wide setting was changed. Fresh production
Rust/CUDA tests were not claimed.

## References used

<a name="ref-s072"></a> **S072** — Koschier et al. (2019), Newtonian stress and SPH viscosity.
[Reading record](/docs/research/sources/072-koschier-sph-viscosity.md).

<a name="ref-s073"></a> **S073** — IAPWS (2011), liquid-water viscosity.
[Reading record](/docs/research/sources/073-iapws-liquid-water-viscosity.md).

<a name="ref-s074"></a> **S074** — Bonet and Lok (1999), variational and momentum preservation;
publisher preview only. [Reading record](/docs/research/sources/074-bonet-lok-variational-sph.md).

<a name="ref-s075"></a> **S075** — Burr, Akylas and Mei (n.d.), viscous diffusion and no-slip.
[Reading record](/docs/research/sources/075-mit-viscous-diffusion.md).
