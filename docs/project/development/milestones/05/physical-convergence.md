# Physical-convergence corrections and remaining resolution limits

**The isolated reference now passes the declared thick-tank timestep and iteration convergence
checks. No model passes the combined original-scene gate, so production is unchanged and no cost
campaign was run.** Density-aware walls, a consistent Wendland density/gradient pair, weak
regularisation and explicit separation improve the resolved-fluid results. Finite particle extent
also corrects a thin-tank boundary error. A shallow collision pool still fails settled geometry and
motion criteria, including after timestep refinement.

The [protocol and complete evidence](/docs/project/development/milestones/05/assets/physical-convergence-v2/README.md)
retain the raw observations of this study in durable local and primary-PC storage. This is a new
campaign; it does not recover the missing raw observations from the
[previous investigation](/docs/project/development/milestones/05/performance-physical-accuracy.md).

## Authority, method and acceptance

The current [numerical contract](/docs/project/development/milestones/00/phases/phase-00-design-contract.md)
and [performance plan](/docs/project/development/milestones/05/performance-plan.md) remain unchanged.
EPQ started at `814f88a7f4122b1b24ea645b210d89e1200a0c44`, Maelstrom at
`250932784790ba26cdc55fc38a877ccefacbf054`. Existing unrelated work was preserved. All thirteen
native source/licence files still match the previous retained control; this task made no simulator
edits, history changes or system-setting changes. All ten production optimisations remain in place.

Experiments use a separate binary64 C++ PBF reference in parent tooling. Local physical tests ran on
the Core 7 150U; the 128-pass convergence test, matched eight/32-pass controls and larger tank also
ran through `ssh pc` on the Ryzen 9 7900X. These are CPU physical tests, not new CUDA qualification.
The reference preserves immutable Jacobi stages but uses freshly rebuilt current-position rows;
it does not implement the production GPU ownership, failure or cancellation API. All requests start
fresh simulations from the recorded initial state.

Before experiments, `protocol.json` defined:

| Assessment | Requirement |
|---|---|
| Transient density | Observed p95 positive error ≤5%; maximum positive error ≤25% |
| Stability | Finite state, separation ≥0.025 m, plane violation ≤10⁻⁶ m |
| Energy | Mechanical energy increase ≤0.004905 J kg⁻¹ above the initial value |
| Settled hydrostatics | Centroid error ≤5%; p95 particle height plus half spacing within 10% of analytical depth |
| Settled motion | Maximum mean kinetic energy over t=5–6 s ≤0.00125 J kg⁻¹ |
| Bulk density | Absolute density error p95 ≤5%, where an interior bulk region exists |
| Convergence | Settled centroid and surface changes ≤5 mm and decreasing under successive refinement |

The two-second mechanism screen and six-second qualification use complete observations every
0.05 s, including the initial and final states. These are sampled bounds, not guarantees between
observations. The initial protocol is immutable. Dated supplements introduced contact, particle
distribution, kernel, depth and finite-extent hypotheses before their respective runs, without
loosening acceptance. More highly resolved scenes were added to diagnose failures; they cannot
erase failures in the original scenes.

The hydrostatic reference is independent of SPH density:

```math
H=\frac{M}{\rho_0 A},\qquad \bar y=H/2.
```

It assumes a settled, uniform-density, full-width pool without surface-tension curvature. Failure
to spread into that state is a model/representation failure for this test, not permission to change
the reference area afterwards. An all-pairs auditor independently recalculates fluid and wall
kernel sums, separation, energy and geometry. Bulk/free-surface labels use the analytical depth
and distance to walls, not a density threshold. Uniform Eulerian probes supplement particle-site
density statistics. Ballistic centre-of-mass motion is checked against semi-implicit Euler's known
gravity displacement; horizontal internal momentum cancels.

## Supported mechanisms and corrections

### Wall density and geometric containment are separate responsibilities

The experimental wall model fills two half-offset lattice layers outside each physical face,
including edge/corner cells once. Their fixed volume is consistent with the lattice mass. Samples
contribute density and the owning fluid constraint's gradient; they own no fluid constraint, receive
no correction and contribute no movable inverse-mass denominator term. This is a project volumetric
wall experiment, rather than a production boundary-method change.

With the corrected C2 model's other settings fixed, disabling wall density produces **40.07% tank
centroid error at two seconds**, against **0.63%** with wall density. In the earlier Poly6 screen,
adding only wall support reduced centroid error from **47.89% to 28.90%**, but did not meet density
criteria. Missing wall support is important; repairing it alone is insufficient.

Point-centre projection still permits represented particle volume to straddle the physical wall.
Insetting collision planes by half the nominal spacing, 0.025 m, is a separately tested change.
It reduces a one-layer tank's centroid error from **44.50% to 3.38%** and the shallow falling-block
error from **9.69% to 3.34%**. Keeping wall samples fixed while changing only the collision inset
isolates this geometric effect.

### A tiny density residual does not establish correct liquid volume

With walls, compression-only constraints, εh²=0.02, correction scale 0.5 and no empirical pressure,
the consistent Poly6-gradient variant has only **0.50% worst sampled p95 compression**, but
**15.13% centroid error** and near-coincident particles at two seconds. A separate equal-mass
minimum-distance Jacobi stage prevents coincidence. With a 0.0255 m target and 8/32/128 passes,
the Poly6 tank centroid errors remain **11.33 / 11.14 / 11.13%**. At 128 passes its worst sampled
p95 compression is only **0.000266%**. This is not an unresolved density-iteration residual.

Independent uniform interior probes in the Poly6 case measure mean density error **+13.47%** and
p95 **+21.47%**, even while particle-site residuals are small. With the 32-pass distance stage,
the probe mean/p95 are still **+5.93 / +12.24%**. The particle distribution makes conditional
particle-site kernel statistics misleading about the intervening density field and geometric volume.

Increasing the distance target alone from 0.0255 to 0.04 m does not cure this: the Poly6 centroid
error remains **9.30%**. Spiky directions with that exclusion distance give **5.12%** error and
substantial residual motion. Stronger exclusion is not a substitute for an accurate fluid model.

### Kernel consistency helps, but does not guarantee separation

The isolated C2 experiment changes the density kernel and its matching analytic gradient together,
keeping support radius h=0.1 m. It recomputes lattice rest density and mass as required by that
kernel change. The selected normalisation is:

```math
W(r)=\frac{21}{2\pi h^3}(1-r/h)^4(1+4r/h),\qquad 0\le r<h.
```

The independent lattice sum is **8270.744069418484 m⁻³**, rather than Poly6's
8078.201335157481 m⁻³. Numerical radial integration checks unit normalisation and central
differences check the implemented derivative. Equal support does not imply equal smoothing scale
when changing kernel. The SPH pairing/convergence literature motivates this experiment but does
not prove the stability of a PBF projection.<sup><a href="#ref-s071">S071</a></sup>

C2 without a distance constraint improves the two-second centroid error to **0.60%**, but still
fails the separation guard. The 0.0255 m distance constraint is therefore retained in the candidate.
Its zero-distance fallback is deterministic and antisymmetric; all corrections use complete
snapshots. This is a changed particle model, not an invisible optimisation.

### Regularisation, free-surface constraints and artificial pressure

At fixed weak correction scale, reducing only εh² from 20 to 2 to 0.02 reduces the Poly6/wall
screen's worst sampled p95 compression from **41.42% to 11.40% to 4.60%**, but creates severe
near-collisions. Changing correction scale alone also fails to qualify that model. These results
support the earlier finding that strong regularisation suppresses constraint work, while showing
why merely removing it can expose another failure.

The candidate uses a unilateral compression constraint. It does not pull a free surface inward
to replace missing air-side neighbours. The PBF paper discusses the negative-pressure clustering
problem and the cohesion trade-off when clamping it.<sup><a href="#ref-s004">S004</a></sup>
Clamping alone was insufficient in the Poly6 screen. Conversely, a signed C2 control also has a
small two-second centroid error; the data do not establish that clamping alone explains the C2
improvement or that every signed formulation must fail.

Disabling artificial pressure alone in the weak Poly6/wall model worsens compression and separation.
Adding it to the corrected C2 model changes spacing and motion, while the tested two-second
centroid errors remain small at both timesteps and iteration counts. The evidence therefore does
**not** support blaming artificial pressure as the sole cause of all previous failures. The
zero-pressure candidate avoids an uncalibrated empirical repulsion in the hydrostatic reference.
Physical surface tension would need a separately specified coefficient and capillary validation.
The original paper describes the artificial term's surface effect as empirical and nonphysical.
<sup><a href="#ref-s004">S004</a></sup>

The tested candidate keeps εh²=0.02 and correction scale 0.5 fixed when changing dt. Neither is
silently divided by refinement squared. This separates temporal error from deliberately weakening
the positional solve. Existing production refinement semantics remain intact.

## Sustained qualification and convergence

The candidate uses eight passes, compression-only constraints, C2 density and derivative, wall
volume support, εh²=0.02, scale 0.5, zero empirical pressure and 0.0255 m minimum-distance target.
Spacing remains 0.05 m. This table uses point-centre collision planes and the six-second results:

| Case | Worst sampled p95 compression | Final centroid error | Declared per-scene checks |
|---|---:|---:|---|
| 512-particle tank, dt=1/120 s | 2.280% | 1.664% | Pass |
| Same tank, dt=1/240 s | 0.530% | 0.881% | Pass |
| Same tank, dt=1/480 s | 0.102% | 0.670% | Pass |
| 3,200-particle tank, primary PC | 0.401% | 0.432% | Pass |
| More highly resolved falling block, 1,000 particles | 2.200% | 0.428% | Pass |
| More highly resolved collision, 1,024 particles | 1.443% | 0.552% | Pass |
| Original shallow falling block, 512 particles | 0.631% | 9.691% | Fail geometry/motion |
| Original shallow collision, 432 particles | 0.321% | 25.477% | Fail geometry/motion |

For the tank, settled-window mean centroid changes under dt=1/120→1/240→1/480 s are
**1.510 mm then 0.428 mm**. Surface-height changes are **2.625 mm then 0.907 mm**.
Both decrease and stay below the predefined 5 mm limit. On the primary PC, increasing
8→32→128 passes changes centroid by **0.514 mm then 0.024 mm**, and surface height by
**0.434 mm then 0.183 mm**. The local and primary eight/32-pass raw streams match exactly;
that is a reproducibility receipt, not the physical admission criterion.

![Tank convergence](/docs/project/development/milestones/05/assets/physical-convergence-v2/tank-convergence.png)

### The remaining shallow-fluid failure is spatial and geometric

The depth ladder changes only the number of fluid layers at fixed spacing, support and model:

| Mass-derived depth / h | Final centroid error with point-centre planes |
|---:|---:|
| 0.484 | 44.50% |
| 0.967 | 10.11% |
| 1.934 | 3.12% |
| 3.869 | 0.88% |

Finite extent fixes the first static tank, but does not qualify the collision scene. With the
0.025 m inset, that pool has **8.10284% centroid error at both 1/120 and 1/240 s**, and
**8.10281% at 1/480 s**. Refinement reduces sampled compression to below 0.1% without correcting
the settled geometry. Its residual-motion window also fails the original limit at 1/240 s.

The observed pool becomes essentially a single layer at the collision inset. Its centroid is then
set by that inset, while the independent reference H/2 depends on total mass and tank area.
For this mass and area, those values differ by about 8.1%. More density iterations cannot create
the missing vertically resolved layer. Remaining lateral gaps and free-surface representation also
need assessment; a low centroid error alone would not admit a partially wetted or granular film.

![Particle distributions](/docs/project/development/milestones/05/assets/physical-convergence-v2/particle-distribution.png)

![Depth sensitivity](/docs/project/development/milestones/05/assets/physical-convergence-v2/depth-resolution.png)

## Recommendation and production decision

Use the C2/consistent-gradient, density-aware-wall, weakly regularised compression-only model with
explicit separation as the **experimental reference for resolved liquid volumes**. Include a
half-spacing collision inset when assessing finite particle extent. Keep the original failing
scenes in regression evidence. The tested depth range suggests an envelope around H/h≥2 for
further study, with larger margin in the deeper cases; it is not a universal resolution guarantee.

The corrections establish bounded thick-fluid convergence and identify why more iterations could
not repair the previous Poly6 density/volume disagreement. They do not establish a general
thin-film or free-surface model. Improving spatial resolution and validating an explicitly
consistent free-surface/volume representation is the next physical task. Retuning epsilon, adding
empirical pressure or fitting an inset to each scene would conceal that unresolved issue.

**Do not merge the experimental model into production or measure its production suitability yet.**
The original combined gate is false. No computational-cost campaign, GPU speedup, real-time factor
or cheapest-policy claim was produced. Even the successful binary64 cases still require binary32
and backend qualification, compatibility with the ten retained optimisations, and production
failure/cancellation/rollback validation before adoption. The isolated reference is not that API.

Twelve focused tests passed, including analytic derivatives, C2 normalisation, corner support,
free-surface deficiency, ballistic centre of mass, corrupt observations, atomic parallel executable
pinning and rejection of density-only admission. All **54 successful raw streams** were independently
read back and re-audited with **no common-field numerical differences**. Failed and interrupted
requests remain explicit. No fresh Rust suite, CUDA accuracy test, capillary pressure reference,
moving/curved boundary test, spatial-limit extrapolation or engineering-CFD validation is claimed.

## References used

<a name="ref-s004"></a> **S004** — Macklin and Müller (2013), *Position Based Fluids*, equations 1–14 and sections 3–4.
[Source record](/docs/research/sources/004-macklin-muller-position-based-fluids.md).

<a name="ref-s071"></a> **S071** — Dehnen and Aly (2012), *Improving convergence in smoothed particle hydrodynamics simulations without pairing instability*.
[Source record](/docs/research/sources/071-dehnen-aly-sph-convergence.md).
