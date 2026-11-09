# A published-equation PBF baseline

The independent `paper-baseline` mode reconstructs Macklin and Müller's equations and Algorithm 1,
while keeping reference as the application default during that comparison. Experimental is now
the application default, as specified in the [settings contract](/docs/project/development/milestones/05/scene-settings-contract.md). It preserves the earlier
[response-calibration findings](/docs/project/development/milestones/05/performance-pbf-contract.md).
Those findings describe existing motion; they do not establish the minimum work needed by PBF.
The [evidence index](/docs/project/development/milestones/05/assets/paper-baseline-v1/README.md)
identifies the assessed source, rendered comparisons, measurements and limitations.

## Equations and implementation audit

The published method assumes equal mass, drops mass from subsequent expressions, uses Poly6 density
and Spiky gradients, solves immutable Jacobi passes, and reconstructs velocity from corrected
positions. Its Dam Break example uses four substeps per 16 ms frame and three iterations per substep.
Neither its regularisation value nor a complete dimensional calibration is supplied.
<sup><a href="#ref-s004">S004</a></sup>

Let `d` be nominal spacing, `h` support radius, `m` equal particle mass, `rho0` physical rest density,
and `R=rho0/m` the number-density rest value. `W` is the unit-integral three-dimensional Poly6
kernel and `G` the Spiky gradient with respect to the owning position. Self density appears once;
self gradient is zero. Strict support is `r<h`.

| Paper expression | Existing Maelstrom | Independent baseline |
| --- | --- | --- |
| Algorithm 1, lines 2–3: `v*=v+dt*a`, `x*=x+dt*v*` | Semi-implicit prediction | Reused unchanged |
| Eq. 2: `rho_i=sum m W_ij` | Stores `D_i=sum W_ij`, reports `m D_i` | Same algebra; nominal `m=rho0*d^3`, `R=1/d^3` |
| Eq. 1: `C_i=D_i/R-1` | Signed constraint, including deficient free surfaces | Reused; no unilateral density clamp |
| Eqs. 7–8: owner `g_ii=sum G_ij/R`, neighbour `g_ij=-G_ij/R` | Includes owner and every active neighbour in denominator | Reused unchanged |
| Eq. 11: `lambda_i=-C_i/(sum_k |g_ik|^2+epsilon)` | `epsilon=relaxation_scale/h^2` | Same regularised equation; independent constant selection |
| Eq. 13: `s_ij=-k*(W_ij/W(q))^n` | `k=strength_scale*h^2`, `q=ratio*h` | Reused, with explicit dimensional assumptions |
| Eq. 14: `delta_i=sum_j (lambda_i+lambda_j+s_ij)*G_ij/R` | Multiplies this result by `correction_scale`; historical refinement divides scale by `N^2` | Full expression; scale must be exactly one; refinement changes only `dt` |
| Algorithm 1, lines 13–17: collisions within each iteration | Ordered static plane projection after the simultaneous fluid update | Reused; no boundary density particles or ghost support |
| Algorithm 1, line 21: `v=(x_new-x_old)/dt` | Complete projected displacement | Reused unchanged |
| Eq. 17: XSPH velocity differences weighted by kernel | Rest-volume quadrature `W/R`, coefficient once per step | Enabled, coefficient 0.01 in that convention |
| Eqs. 15–16: curl, normalised gradient of curl magnitude, confinement | Rest-volume Spiky quadrature, neighbour differences for the magnitude gradient, `dt*strength*(N cross omega)` | Available through the existing explicit switch; disabled in the assessed baseline |

The existing kernel and solver arithmetic implements these expressions; the audit did not reveal a
missing equal-mass factor, wrong gradient sign or an in-place Jacobi update. No CUDA production file
needs rewriting. Mass normalisation, boundary representation, regularisation and kernel quadrature
are choices requiring declaration, rather than defects merely because the paper leaves them open.
The empirical complete-correction attenuation is an explicit departure from Eq. 14.

The paper writes velocity-effect sums without specifying a transferable SI coefficient. Maelstrom's
XSPH uses `c_volume=0.01/R` multiplying the dimensional Poly6 sum; 0.01 is a dimensionless rest-volume
coefficient, **not** an assertion that the paper's literal 0.01 can multiply an SI kernel unchanged.
Similarly the existing optional confinement uses a volume-weighted curl and a strength in m/s.
These choices preserve the published mechanisms with an explicit quadrature convention. They do not
claim identical velocity-effect strengths to the authors' unpublished scene parameters.

## Reconstructed contract and assumptions

`pbf_formulation="paper2013"` is retained in configuration, provenance, comparison identity and
recorded reruns. It selects nominal cubic particle mass and disables empirical correction refinement.
It rejects attenuated correction scales. Legacy inputs omit this new field and keep their historical
mass, comparison identity and refinement semantics. The reusable CPU and CUDA solver stages operate
on the independently resolved parameters.

At `h=2d`, nominal volume and discrete Poly6 integration do not exactly agree: a fully populated cubic
lattice starts slightly above nominal rest density. Existing modes instead choose mass so that that
particular lattice is exactly at rest. The baseline deliberately records the nominal-volume
assumption without altering kernels, support, spacing or rendered geometry to hide quadrature error.
Both are legitimate calibrations; neither is mandated by the paper.

Multipliers and artificial pressure have units m², substituted constraint directions m⁻¹,
regularisation m⁻² and position corrections m. Expressing the solve in coordinates `x/h` motivates
`epsilon=epsilon_hat/h²` and `k=k_hat*h²`. This gives a consistent change of length units. It does not
make any coefficient universal across support ratios or step rates. The first published-equation
screen used 240 Hz, three passes, `epsilon_hat=1`, `k_hat=0.1`, `q/h=0.2`, `n=4`, rest-volume XSPH
0.01 and no confinement. The schedule approximates the paper's 4 ms Dam Break example.

Neighbour lists are built once after prediction, with distances and active membership recomputed
each iteration. Particles newly entering support from outside that list are absent until the next
step. This is also a limitation acknowledged in the paper. No hidden correction clipping, adaptive
substepping, global damping or minimum-distance projection is introduced.
<sup><a href="#ref-s004">S004</a></sup>

Plane constraints act on particle centres in their existing order; there is no new particle radius,
restitution impulse or wall-density support. Contact velocity follows projected displacement. Sparse
wall neighbourhoods can therefore contract or stack, and projection can redistribute fluid correction
energy. The paper itself identifies boundary stacking and the tension/clustering trade-off. These
limits must be assessed from trajectories rather than repaired by arbitrary global scaling.
<sup><a href="#ref-s004">S004</a></sup>

## Bounded calibration and comparison protocol

The initial slope screen exploded into sustained high-speed scattering after contact. Two controls
changed one mechanism each: `epsilon_hat=20` with pressure unchanged, and `k_hat=0.001` with
regularisation unchanged. The first produced stable sheet flow on this scene; the second introduced
visible clumping and breakup. The retained `paper-baseline` uses `epsilon_hat=20`, with the complete
published correction still unattenuated. This is a measured Maelstrom calibration, not a numerical
constant recovered from the paper. No further parameter frontier is authorised by this comparison.

The full comparison covers slope-slide, falling-block-20, two-blocks, shallow-tank and large-impact,
for five simulated seconds each, with matched initial particle bytes, cameras, renderer and 30 Hz
observations. Diagnostics report current-position density, compression, separation, coincidences,
kinetic/potential energy and containment separately. No arbitrary accuracy cutoff decides visual
acceptance. Destructive instability, widespread coincidence and visibly broken collisions remain
rejection grounds. Native diagnostic replays must match production endpoint bytes before admission;
their timings are excluded from solver throughput.

Performance uses the primary PC's RTX 4070, CUDA device zero and block size 128. Each mode runs five
simulated seconds at 8,000 and 110,592 particles, with one full warmup followed by five samples,
reversing mode order on alternating rounds. Builds, tests, renders and audits finish before these
samples begin. Solver time sums complete accepted calls; complete CLI time includes startup and
output. Steps and passes per simulated second are disclosed alongside measured throughput. The
baseline includes XSPH; reference and experimental retain their scene settings. Rendered compile
clocks and any actual viewer redraw measurement remain separate from headless solver timing.

## Measured outcome and decision

The final comparison uses the calibrated baseline: **240 Hz, three full Jacobi passes,
regularisation 20, nominal cubic mass and XSPH 0.01**. This is a faithful implementation of the
published position equations with explicit Maelstrom constants, rather than a reproduction of
unpublished author scene settings. All ten retained CUDA optimisations and the existing rendering,
encoding and hashing implementations remain unchanged.

Median complete solver cost on the RTX 4070, in wall seconds per simulated second:

| Particles | Reference | Experimental | Paper baseline | Paper/reference speedup | Paper/experimental speedup |
| --- | ---: | ---: | ---: | ---: | ---: |
| 8,000 | 0.92623 | 0.46148 | 0.29085 | 3.185× | 1.587× |
| 110,592 | 5.64128 | 2.80314 | 1.95889 | 2.876× | 1.432× |

Speedups are medians of the five paired ratios; every paper sample was faster than both controls.
Complete CLI medians were respectively **0.99369 / 0.53144 / 0.36115** at 8,000 and
**5.76878 / 2.93502 / 2.08544** at 110,592. These are measured clocks. The separate theoretical work
counts are 3,840 / 1,920 / 720 Jacobi passes per simulated second: 81.25% fewer than reference and
62.5% fewer than experimental for the baseline. Neighbour construction, transactional validation,
velocity effects and other fixed work still run; a pass-count ratio is not a throughput result.
There is no live FPS result: the attempted viewer failed in WSLg/X11 before its redraw counter
could be captured. Offline compile timing is not substituted for viewer performance.

Visually, the regularised baseline retains falling-block deformation, slope spreading, collision
sheets and settling on the smaller scenes. It does not show the initial unstable screen's sustained
scattering. Its sampled minimum separations were **0.715d** for falling water, **0.703d** for two-block
collision, **0.789d** for shallow flow and **0.730d** on the slope, with no exact coincidences in those
samples. Peak sampled p95 compression was 17.54%, 6.06%, 6.31% and 4.82%, respectively. These are
diagnostics, not physical-accuracy acceptance thresholds. The two-block comparison has less splash and breakup, and the shallow flow has a
rounder outline with less spreading. These differences do not establish more convincing water.
The shallow case retains more late motion than the controls; the slope retains less. Lower final kinetic energy alone does not prove better
water or a correct viscosity.

The large-impact result prevents a general recommendation:

| Large impact, sampled observations | Reference | Experimental | Paper baseline |
| --- | ---: | ---: | ---: |
| Peak particles with an exactly coincident neighbour | 6 | 7 | 89 |
| Such particles at five seconds | 4 | 2 | 87 |
| Maximum sampled speed, m/s | 7.636 | 10.138 | 57.514 |
| Maximum speed over every accepted step, m/s | 17.136 | 16.174 | 74.800 |
| CFL-warning steps / total steps | 940/2400 | 654/1200 | 1167/1200 |
| Peak p95 compression | 89.30% | 86.83% | 68.38% |
| Peak maximum compression | 136.29% | 133.28% | 381.22% |
| Kinetic energy at five seconds, J/kg | 0.01310 | 0.00615 | 0.05326 |

The CFL warning is diagnostic rather than an automatic veto. This is not widespread collapse of the entire body: 89 particles are about 0.0805% of the population.
It is nevertheless persistent local failure, accompanied by conspicuous high-speed outliers in the
rendered large impact and poorer settling. The improved bulk compression statistic does not erase
that observation. The independent audit does not establish net ongoing energy creation: total
mechanical energy generally falls below its initial value, with only small initial rearrangement
excesses. The concern is the observed local motion and particle geometry, rather than a fabricated
energy-budget violation.

The equation checks support the implemented signed density constraints, mass normalisation and
full correction. They do not prove that three local Jacobi passes converge adequately at large
impact, or that cached neighbourhoods and unsupported wall densities are adequate there. Both are
plausible contributors, consistent with the paper's stated limits; this comparison does not isolate
their individual shares.<sup><a href="#ref-s004">S004</a></sup> At exact coincidence Spiky has no unique separating direction, so the
existing zero-direction convention cannot repair the collapsed pair through artificial pressure.
No arbitrary correction multiplier is added to hide these outcomes.

**Retain the independent baseline implementation; do not retain its assessed calibration as the
general practical candidate. Recommend experimental for the tested mixture of scenes, and keep
reference as the default.** Experimental gives about twice the reference throughput with closer
reference-like motion and far fewer large-scene overlaps than the three-pass baseline. Neither old
mode is perfect, and their rare coincidences remain disclosed. Three full passes demonstrate a
lower workload for the smaller scenes; they do not establish a universally sufficient or globally
minimal PBF workload. The bounded comparison stops here.

## References used

- <a name="ref-s004"></a> **S004** — Macklin and Müller (2013), *Position Based Fluids*.
  [Source record](/docs/research/sources/004-macklin-muller-position-based-fluids.md).
