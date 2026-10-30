# Shallow-collision spatial resolution and operating limits

**Spatial refinement removes the experimental model's 8.1% shallow-pool centroid failure within
the predefined macroscopic accuracy budgets. It does not establish convergence to exact continuum
hydrostatics or qualify a production policy.** The first passing collision has 2.18 nominal particle
spacings of liquid depth. All four impact resolutions fail the settled-motion criterion. Production,
all ten retained CUDA optimisations and both Git histories are unchanged.

This follows the [physical-convergence study](/docs/project/development/milestones/05/physical-convergence.md).
The [complete evidence and reproduction guide](/docs/project/development/milestones/05/assets/shallow-resolution-v1/README.md)
retain successful runs, rejected initialisers, raw observations, independent audits and timing samples.
It is an isolated physical-model study, not an amendment to the production
[numerical contract](/docs/project/development/milestones/00/phases/phase-00-design-contract.md)
or a retained optimisation under the
[performance assessment policy](/docs/project/development/milestones/05/performance-assessment.md).

## Controlled model and independent references

All main simulations ran on the primary Ryzen 9 7900X through `ssh pc`, using an isolated binary64
C++ reference and eight OpenMP workers. EPQ remained at
`814f88a7f4122b1b24ea645b210d89e1200a0c44`; Maelstrom remained at
`250932784790ba26cdc55fc38a877ccefacbf054`. Existing unrelated changes were preserved. The thirteen
native control files still match the previous retained source hashes. This reference does not
exercise production CUDA, its cancellation/rollback API or binary32 arithmetic.

The box is 1.2 × 1.2 × 0.8 m. Two 0.3 m cubes begin at (0.1, 0.375, 0.2) and
(0.8, 0.375, 0.2) m, with horizontal velocities +0.5 and −0.5 m/s and gravity −9.81 m/s².
Their physical extents, total mass **52.23230175835605 kg** and box remain fixed. Sampling each
cube with n³ particles gives:

```math
\Delta x=0.3/n,\quad N=2n^3,\quad m=M/N,\quad h=2\Delta x,
\quad d_{\rm inset}=0.5\Delta x,\quad d_{\rm contact}=0.51\Delta x.
```

The experimental Wendland C2 density and matching gradient, compression-only constraints,
εh²=0.02, correction scale 0.5, eight Jacobi passes and zero artificial pressure are held fixed.
Two half-offset wall-sample layers retain the same spacing and particle volume. Each pass rebuilds
neighbours at current positions; fixed walls contribute only to movable constraints. The timestep
scales as (1/240)(Δx/0.05) s. Separate half-timestep and doubled-iteration controls isolate temporal
effects from this spatial ladder.

The independent uniform-density hydrostatic reference is:

```math
V_*=M/1000=0.05223230175835605\ {\rm m^3},\qquad
H_*=V_*/(1.2\times0.8)=0.05440864766495422\ {\rm m},\qquad \bar y_*=H_*/2.
```

It assumes a fully spread, settled pool without surface-tension curvature. A different realised
wet area does not change this test's reference. The audit uses a SciPy KD tree, separate kernel
implementation and continuum quadrature, rather than the solver's flat-grid neighbour search.
Particle-site density includes self and configured wall support. Off-particle density uses 384 fixed
physical probes at H*/2, compared with the analytic slab's kernel convolution, so missing air-side
support is not mislabelled as compression. Its error divides by max(expected density ratio, 0.2).

The immutable protocol set transient positive-density p95 ≤5%, maximum ≤25%, separation ≥0.5Δx,
physical-plane violation ≤10⁻⁶ m; settled centroid error ≤5%, height and reconstructed volume errors
≤10%, interparticle field p95 absolute error ≤10%, and kinetic energy ≤0.00125 J/kg over t=5–6 s.
Successive spatial centroid/height changes must decrease and lie within the respective error
budgets at the finest pair; temporal/iteration controls must preserve the conclusion. The field's
10% budget is distinct from the 5% compression budget. Finite state, geometry and mechanical energy
are also recorded. This new spatial screen does not supersede the previous study's energy gate.

Runs last six simulated seconds and save every 0.05 s, including both endpoints. All reported
transient extrema and settled bounds are sampled, not guarantees between observations. The height
statistic is p95 particle y plus Δx/2, a finite-particle envelope proxy rather than a measured sharp
interface. Volume is independently reconstructed at t=5, 5.5 and 6 s from the wall-normalised fluid
field. The identically reconstructed analytic slab removes the diagnostic's convolution bias; raw
observed and analytic volumes are both retained. This calibration is applied only by the reader,
never as feedback to the solver.

## Spatial results and the residual calibration floor

Signed geometry/volume errors below are at six seconds; field error is the worst settled p95.
Compression is the maximum sampled particle-site p95 over the entire run.

| Δx (mm) | Particles | H*/Δx | Centroid error | Height error | Field error | Volume error | Compression |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 50.00 | 432 | 1.088 | −8.103% | −8.103% | 30.979% | −2.251% | 0.295% |
| 25.00 | 3,456 | 2.176 | +0.995% | −1.579% | 6.696% | +0.643% | 0.565% |
| 16.67 | 11,664 | 3.265 | +2.602% | +1.810% | 6.370% | +1.537% | 0.655% |
| 12.50 | 27,648 | 4.353 | +3.312% | +3.643% | 7.333% | +2.209% | 0.722% |

![Spatial accuracy and diminishing changes](/docs/project/development/milestones/05/assets/shallow-resolution-v1/spatial-errors.png)

The coarse pool's particle centres are pinned at 25 mm. Its reference centroid is 27.204 mm, so
the observed −8.103% error follows directly from a single resolved layer. A static, inset-valid
full-width pool with the same mass reproduces **−8.103%**, zero settled kinetic energy and 22.407%
field error. The impact is therefore unnecessary to cause this geometry failure. That static
comparison passes the declared checks at 25 and 16.67 mm, with centroid errors +1.092% and +2.124%.

![Final particle centres projected across the box; marker size is illustrative](/docs/project/development/milestones/05/assets/shallow-resolution-v1/settled-projections.png)

Successive changes in mean settled centroid are **2.488, 0.463 and 0.197 mm**; changes in mean
height are **3.745, 2.098 and 0.955 mm**. They decrease and the finest pair lies within the
protocol's physical-error budgets. However, error relative to the physical reference does not
decrease monotonically towards zero. The finest result is consistent with an independently
calculable mass/kernel calibration floor:

```math
R_0=8270.744069418484\ {\rm m^{-3}}\quad(\Delta x=0.05\ {\rm m}),\qquad
R_0\Delta x^3=1.0338430086773107.
```

The inherited mass choice m=1000/R₀ gives a lattice particle-site kernel density of 1000 kg/m³,
but a geometric mass density m/Δx³ of **967.2648473769639 kg/m³**. An incompressible pool retaining
that geometric density would have height 56.25 mm, **3.3843%** above H*. The finest collision's
+3.3116% centroid error is consistent with that bias. Keeping h/Δx fixed preserves this lattice
quadrature discrepancy as spacing shrinks. This is a parameter/estimator calibration problem,
not evidence that physical mass was lost. It is not a proof of the asymptotic state of disordered PBF.
The SPH literature separately distinguishes estimates at particle sites from unoccupied locations
and discusses self-contribution bias; its force-based corrections have not been adopted or
qualified here.<sup><a href="#ref-s071">S071</a></sup>

Thus refinement resolves the original failure to the stated budgets, while failing to demonstrate
strict continuum consistency. A future mass/support change must hold physical M and geometry fixed
and repeat qualification; substituting ρΔx³ silently would change this workload's mass.

## Isolating inset, wall density and free-surface sampling

At fixed resolution and other model settings, the final centroid errors are:

| Control | Δx=50 mm | Δx=25 mm |
|---|---:|---:|
| Inset 0, wall density on | −25.647% | −6.074% |
| Inset 0.25Δx, wall density on | −25.006% | −5.903% |
| Inset 0.5Δx, wall density on | −8.103% | +0.995% |
| Inset 0.5Δx, wall density off | −1.009% | +18.922% |

![Boundary controls](/docs/project/development/milestones/05/assets/shallow-resolution-v1/boundary-controls.png)

Removing boundary density makes the coarse centroid appear better while field error reaches
**82.75%**. At 25 mm it produces **106.89% height error** and 43.03% field error. Collision geometry
and wall density solve different problems; neither removing walls nor selecting an inset by centroid
alone is supported. The half-spacing inset consistently accounts for represented particle extent.

At Δx=25 mm, a separate full-width depth ladder varies mass with depth, keeping each particle's
mass, support, box and timestep fixed. Physical depth is 0.967264847 times the nominal initial
geometric depth because of the measured mass convention. Isotropic one-, two-, three- and four-stratum
initial states are geometrically valid. Their physical H*/Δx values are 0.967, 1.935, 2.902 and 3.869.
One stratum has a seemingly acceptable +3.384% centroid error but **19.00% field error**; two strata
have +3.220% centroid and **8.12% field error**. Three and four strata have field errors 5.17% and
6.09%. The last three pass this spatial study's declared checks.

Fractional-depth controls test whether this is merely an integer-lattice coincidence. An important
experimental defect was found and corrected: the original anisotropic flat/depth samplers placed
some centres inside the isotropic collision inset. Eleven completed auxiliary controls are retained
but excluded from positive qualification. Corrected samplers preserve count, mass, physical region
and centre of mass, fit centres inside the inset, and check initial separation before stepping.
Two attempted aligned two-stratum samplers at nominal depths 1.25Δx and 1.5Δx cannot meet the
configured distance target; they stop before stepping and retain their initial observations.

The corrected floor-stratum controls at physical depths 1.209Δx and 1.451Δx still fail height and
field accuracy: height errors **48.25% and 31.64%**, field errors **21.34% and 15.97%**. At 2.418Δx,
floor/ceil initialisations give centroid errors +2.182/+2.225%, height +5.84/+6.43% and field
7.85/7.69%. At 3.627Δx they give +2.868/+2.987%, +1.17/+0.85% and 5.88/6.29%. These settled results
support a depth effect, but several fractional controls start overcompressed: their initial p95
compression reaches 16.03%, and constraint release can increase mechanical energy by 4.54 J/kg.
They are not acceptable fluid transients. Even corrected flat initialisers exhibit small initial
constraint-energy releases. Geometry validity alone does not establish a stress-free initial fluid.

![Depth and initialisation controls](/docs/project/development/milestones/05/assets/shallow-resolution-v1/depth-controls.png)

The evidence brackets a useful lower macroscopic bound around **two nominal spacings**, with the
first passing collision at **2.176 spacings**. It does not establish a universal sharp threshold,
nor that every irregular two-layer initialisation is safe. H*/Δx is a resolution measure, not a
claim that each local region always contains that many complete layers.

## Time convergence, stability and diagnostic limitations

Halving the timestep at 25 and 16.67 mm changes final centroid by only **0.0133 and 0.0486 mm**.
Doubling the passes to 16 at 25 mm changes it by **0.0112 mm**. Both controls preserve macroscopic
accuracy; neither repairs the coarse layer representation. All main collision samples are finite,
contained, separated by at least 0.5Δx and never exceed initial mechanical energy.

Nevertheless their maximum settled kinetic energies are **0.002388, 0.001660, 0.003234 and
0.003387 J/kg**, all above 0.00125 J/kg. Half-timestep controls at 25/16.67 mm retain
0.002498/0.003449 J/kg; 16 passes at 25 mm retain 0.001556 J/kg. Time refinement and additional
iterations improve density residuals without eliminating persistent impact motion. This reference
has no calibrated physical viscosity. The data do not isolate how much motion comes from insufficient
dissipation versus density/contact projection. No fully qualified dynamic operating policy was found.

Volume measurements require caution. The coarse geometric column volume changes from 0.042 to
0.048 m³ when the horizontal bin width changes from Δx to 2Δx; wet fractions change from 0.875 to 1.
For the calibrated kernel-field volume, halving audit grid spacing changes final error by **0.340
percentage points** at 50 mm and **0.029** at 25 mm. Thresholds 0.45/0.50/0.55 are retained.
Low reconstructed-volume error alone plainly does not certify the one-layer pool. Independent
all-pairs and KD-tree final coarse density agree within 4.55×10⁻¹³ kg/m³; order-24 and order-48
full-support quadratures integrate to 0.99999288 and 0.99999988. These validate the diagnostic
calculation, not the fluid model or a sharp free surface.

## Computational cost and bounded recommendation

Only after macroscopic assessment, matched CPU costs were measured on the primary PC: one warm-up
then five alternating-resolution serial rounds, eight workers, **0.5 simulated seconds starting
from the collision initial state**. Complete-step timers include neighbour construction,
constraints, contact and accepted updates, and exclude construction, observations, compression,
audits and teardown. All timing trajectories exactly match their six-second run's first-half-second
observations. All samples, including the slower 16.67 mm sample, are retained.

| Δx (mm) | Median solver seconds per 0.5 simulated seconds | Observed range (s) |
|---:|---:|---:|
| 50.00 | 0.0891 | 0.0875–0.0896 |
| 25.00 | 1.6053 | 1.6011–1.6811 |
| 16.67 | 9.0769 | 8.8937–12.6017 |
| 12.50 | 29.5320 | 28.2215–31.1027 |

![Physical accuracy and reference CPU cost](/docs/project/development/milestones/05/assets/shallow-resolution-v1/accuracy-cost.png)

At the cheapest macroscopic passing collision resolution, particle count increases eightfold and
step count doubles relative to the failing coarse case; measured CPU cost increases about **18×**.
It does not run in real time in this reference. These costs cover fall/impact, not sustained
six-second throughput, production whole-application timing or a CUDA prediction. Since the combined
physical gate failed, no production performance or adoption campaign was undertaken.

For further isolated macroscopic experiments only, use **H*/Δx≥2.2**, h=2Δx, mass consistently tied
to fixed physical M, inset 0.5Δx, contact target 0.51Δx and the tested C2 settings. Use valid,
well-conditioned initial states, verify the transient density/energy independently, and assess
locally shallow regions separately. This is an observed lower screening bound for this geometry
and error budget; curvature, wetting, films below it, narrower containers, arbitrary particle
distributions and binary32 CUDA remain unqualified. Extra resolution cannot be sold as zero-bias
accuracy while the mass/estimator convention remains unchanged.

A complex thin-film method is not justified by this result. The original macroscopic failure is
removed by modest spatial refinement and correct finite extent; the residuals point to calibration
and motion rather than demonstrated necessity for a new free-surface solver. No volume-aware
solver alternative was introduced. The volume-aware field reconstruction is an independent
measurement only. If sub-two-spacing films become an explicit requirement, or a corrected
mass/support convention fails the same controlled tests, a simple volume-aware surface experiment
would then have a concrete failure to address.

The evidence contains **64 complete raw streams and two deliberately rejected initial-only
streams, 5,106 observations and 1,204,730,520 uncompressed bytes**. Scheduled records, compressed
and raw hashes are verified; both durable copies are checked independently. Twelve focused local
tests pass. This does not recover the first study's lost archive. No production changes, new
Rust/CUDA qualification, history changes or system-wide settings changes were made.

## References used

- <a name="ref-s071"></a> **S071** — Dehnen and Aly (2012), *Improving convergence in smoothed
  particle hydrodynamics simulations without pairing instability*, §2.5.
  [Source record](/docs/research/sources/071-dehnen-aly-sph-convergence.md).
