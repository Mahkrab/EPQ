# PBF physical accuracy and convergence investigation

**No tested policy is qualified as physically acceptable across density, settled volume and
timestep convergence. Keep production behaviour and all ten retained optimisations.** A private
compression-only experiment is a useful starting point for further numerical work, but its density
pass is not sufficient authority to adopt it. The cheapest physically acceptable policy therefore
remains undetermined; the tested set contains no defensible winner.

The [evidence package](/docs/project/development/milestones/05/assets/physical-accuracy-v1/README.md)
contains hash-verified binary inputs, selected observations, campaign summaries, independent audits,
source and executable hashes, plots and timing samples. Most raw intermediate states were lost when
the PC temporary directory disappeared before final transfer; the evidence README defines that limit. Production Maelstrom is
`250932784790ba26cdc55fc38a877ccefacbf054`; EPQ started at
`814f88a7f4122b1b24ea645b210d89e1200a0c44`. Existing unrelated edits in both trees were
preserved. No production files, defaults, repository history or system settings were changed.

## Scope and criteria

The [numerical contract](/docs/project/development/milestones/00/phases/phase-00-design-contract.md)
and [current performance plan](/docs/project/development/milestones/05/performance-plan.md) own
the existing behaviour. This investigation evaluates explicit alternatives rather than treating
agreement with that behaviour as physical accuracy. Previous stability qualification did not impose
the present 5% density screen and is not invalidated retrospectively by its failure here.

All device experiments ran on the primary PC through `ssh pc`, using the RTX 4070, driver 610.88,
CUDA 13.3.73 and precise compute_89 arithmetic. Each request starts a fresh simulation. No renderer
or frame pacing participates in solver timings. The independent health reader uses binary64 Poly6
density, includes self, and searches fresh current-position neighbours independently of device rows.

The initial density/stability screen required p95 positive density error ≤5%, maximum positive error
≤25%, finite state, zero coincident pairs, minimum separation ≥0.025 m and plane violation ≤10⁻⁶ m.
These checks apply to observed states at zero, the first step, every quarter-second and five seconds;
they are not continuous bounds between observations. Free-surface under-density is reported, not
treated as fluid compression. A small initial criteria file briefly recorded a weaker separation
limit; this was corrected to the existing 0.025 m guard before the multi-scene validation.

After density screening, an additional hydrostatic falsification test used a full-width 1 m² tank.
Its physical depth is independently M/(ρ₀A), about 0.396128 m. Its uniform-density centroid is
0.198064 m. A prospective admission rule is centroid error ≤5%, together with decreasing shape
changes under independent timestep refinement and no visible collapse or persistent expansion.
This additional criterion was introduced after screening; it was not a pre-registered result.
No exact continuum velocity/pressure solution or experimentally measured water reference was used.

## Formulation and independently checked calculations

The inspected Rust and CUDA implementations use the declared equations:

```math
C_i=\frac{\sum_j W_{poly6}(p_i-p_j,h)}{\tilde\rho_0}-1,\qquad
\lambda_i=-\frac{C_i}{D_i+\varepsilon},\qquad
\Delta p_i=\frac{s_p}{\tilde\rho_0}\sum_j(\lambda_i+\lambda_j+s_{corr,ij})\nabla W_{spiky}.
```

Here D is the sum of squared substituted constraint directions. This matches the structure of
PBF's equations, including its use of different density and direction kernels. The paper does not
provide Maelstrom's SI regularisation or correction-refinement policy.<sup><a href="#ref-s004">S004</a></sup>

An independent all-pairs binary64 implementation was written without device helpers or grid code.
For a stationary, compressed 64-particle fixture, device/reference maximum position differences after
1/8/32 Jacobi iterations were **1.44×10⁻⁸ / 3.08×10⁻⁸ / 1.39×10⁻⁷ m**. This supports the arithmetic
and signs on that fixture; it does not prove all configurations or backend failure paths correct.

* **Mass is not missing.** Equal fluid masses cancel through the mass-divided density convention.
  An independent infinite-lattice sum gives 8078.201335157482 m⁻³ and mass
  0.12378993274751121 kg at Δx=0.05 m, h=0.1 m. Production binary32 values are
  8078.19921875 m⁻³ and 0.123789966 kg. The lattice mass is 0.99031946 times ρ₀Δx³:
  a roughly 0.97% discretisation difference, not an explanation of 20–41% compression.
* **The correction is heavily damped twice.** In the compressed reference fixture, D ranges from
  about 245 to 409 m⁻², against ε≈2000 m⁻². Regularisation accounts for 83–89% of the
  denominator; multiplying the remaining correction by 0.0625 leaves only about 0.68–1.06% of
  its unregularised magnitude. This is a fixture-specific calculation, not a general contraction rate.
  Before the 32nd pass, p95 compression still measures 22.81%, down from 37.22% initially.
* **Spiky is not the derivative of the density residual.** At r=0.05 m the normalised Poly6
  derivative is −3.272727 m⁻¹; the substituted Spiky value is −4.432900 m⁻¹, a ratio of 1.354497.
  The iteration is consequently not an exact Newton solve of the measured Poly6 constraint.
  Neither its squared residual nor its p95 statistic has an established monotonic descent guarantee.
* **Plane containment is not density support.** An ideal lattice truncated at a plane through one
  particle layer has only 80.9091% of the bulk kernel sum at that layer. A signed constraint treats
  this deficiency as attraction even at a solid wall or free surface. Projecting particle centres
  does not supply the missing wall volume, pressure or finite particle radius. Boundary density
  deficiency and density-aware alternatives are recognised in the research basis.<sup><a href="#ref-s052">S052</a></sup>

No missing mass, correction-sign or Jacobi snapshot defect was demonstrated. The problematic
policies are explicit in the current contract. One neighbour-refresh experimental harness initially
failed because it retained a stage-specific diagnostic index while invoking search operations.
Resetting that index repaired the private harness; this is not evidence of a production defect.

## Controlled experiments and convergence

The first screen varied one parameter at a time around an 8,000-particle falling block, for five
seconds. Unless named otherwise, it used eight iterations, dt≈1/480 s, εh²=20 and h/Δx=2.
The screen's regenerated regularisation differed from production by one binary32 ULP; the later
validation explicitly preserves the production constants and verifies baseline input bytes. Small
endpoint differences between these batches are not interpreted as physical disagreement.

| Experimental control | Worst observed p95 compression | Checked replay cost for 5 s |
|---|---:|---:|
| Correction scale 0.0625 | 20.00% | 4.332 s |
| Scale 0.25 | 5.67% | 4.249 s |
| Scale 0.5 | 4.08% | 4.254 s |
| Scale 1 | 3.49% | 4.276 s |
| Scale 0.25, εh²=0.2 / 2 / 200 | 5.41 / 5.17 / 20.96% | 4.215 / 4.202 / 4.362 s |
| Scale 0.25, dt=1/120 / 1/240 / 1/960 s | 53.18 / 18.26 / 3.56% | 1.157 / 2.167 / 8.443 s |
| Scale 0.25, 3 / 4 / 16 / 32 iterations | 11.11 / 6.78 / 4.03 / 3.57% | 2.611 / 2.938 / 6.905 / 12.187 s |
| Scale 0.25, h/Δx=1.5 / 2.5 | 9.69 / 2.21% | 3.479 / 5.304 s |
| Scale 0.25, artificial pressure disabled | 7.26%; coincidences | 4.202 s |
| Scale 0.25, compression-only constraint | 1.83% | 4.557 s |
| Compression-only, scale 0.5, εh²=2 | <0.01% | 3.825 s |

These are exploratory single trajectories, not repeated performance claims. Changing h recomputes
rest density, mass, regularisation and artificial-pressure kernel constants; otherwise the comparison
would introduce a mass-calibration error. The larger support improves this density screen but increases
neighbour work, wall influence and smoothing. It has not been qualified across the larger scenes.

A repaired every-iteration neighbour rebuild at scale 0.25 cost **12.080 s**, with worst p95 error
**5.581%**, compared with 4.249 s and 5.67% for frozen rows. It does not explain away this failure.
This does not prove stale rows harmless in other fast/crowded configurations.

An instrumented 8,000-particle trajectory records every correction at t≈0.5 s with 32 iterations.
Fresh p95 compression starts at **5.4483%**, rises to **5.4676%** after four passes, and reaches
**5.3899%** after 32. Thus even a fixed-step density percentile can briefly worsen while other
constraints and boundary projections are being applied. Comparing endpoint trajectories with different
iteration counts also changes velocities, contact history and later neighbour membership.

Refinement is especially easy to misinterpret. The supported refinement operation changes
dt→dt/N **and** sₚ→sₚ/N². In the regularisation-dominated regime, positional correction behaves
approximately like a soft restoring term whose effective acceleration scales as sₚ/dt². This recipe
roughly preserves that stiffness; it does not make the constraint projection more complete. Conversely,
reducing dt alone increases corrections and empirical artificial pressure per unit simulated time.
Neither experiment by itself establishes incompressible temporal convergence.

## Multiple scenes and the hydrostatic counterexample

Four policies were evaluated on 1,000-, 8,000- and 110,592-particle falling blocks, two colliding
1,000-particle blocks and a 3,200-particle shallow spreading pool. Velocity post-processes were disabled.
Each row below is the worst observed p95 positive error through five seconds.

| Policy | 1,000 block | 8,000 block | 110,592 block | Collision | Shallow pool |
|---|---:|---:|---:|---:|---:|
| Production: scale 0.0625, εh²=20, 8 passes, 1/480 s | 7.92% | 19.77% | 41.21% | 9.56% | 10.35% |
| Scale 1, otherwise production | 6.77% | 3.61% | 6.13% | 6.78% | 3.35% |
| Compression-only, scale 0.5, εh²=2, 8 passes, 1/480 s | <0.01% | <0.01% | 0.87% | <0.01% | <0.01% |
| Same compression-only parameters, 4 passes, 1/240 s | <0.01% | 5.01% | 10.81% | <0.01% | 0.28% |

The baseline large scene independently reproduces **8.624884% at one second and 20.918745% at five**.
At five seconds its wall/bulk p95 errors are **25.71% / 19.79%**: wall behaviour exacerbates the
problem, but is not the only cause. Its minimum sampled separation is 0.0202 m, below the guard.
The fine compression-only policy passes the declared density/stability screen on all five scenes:
largest sampled compression is 3.84%, with no coincidences or plane violations.

However, a sixth scene, the full-width hydrostatic tank, prevents admission:

| Policy in the tank | Final centroid (m) | Error against M/(2ρ₀A) |
|---|---:|---:|
| Production | 0.138443 | −30.10% |
| Production with scale 1 | 0.159854 | −19.29% |
| Compression-only, 8 passes, dt=1/480 s | 0.199036 | +0.49% |
| Compression-only, 4 passes, dt=1/240 s | 0.151531 | −23.49% |
| Compression-only, 8 passes, dt=1/960 s | 0.245395 | +23.90% |

The last two rows distinguish a combined cheaper-work experiment from a timestep-only experiment.
The latter keeps the iteration count and other parameters fixed. Removing artificial pressure from
the compression-only tank does not repair the issue: centroid errors remain −33.21% / −18.89%
at 1/240 and 1/480 s, with substantial residual motion (0.112 / 0.639 J kg⁻¹ kinetic energy).

![Settled tank projections](/docs/project/development/milestones/05/assets/physical-accuracy-v1/hydrostatic-projections.png)

The projections show excessive collapse in the baseline and a deeper, more dispersed pool when the
fine compression-only step is halved. The apparently excellent middle centroid is therefore not evidence
of a converged hydrostatic solution. These are inspected orthographic particle observations, not a
rendered animation or a validated reconstructed fluid surface. A centroid alone can hide a nonuniform
distribution; volume reconstruction, pressure and surface shape remain unqualified.

## Cost, recommendations and limits

One warm-up pair followed by five alternating ordinary checked native pairs at 110,592 particles,
480 steps, gave **2.971972 s** median for control (range 2.959613–2.979767) and **2.501890 s** for
the fine compression-only candidate (2.496785–2.513076). Different trajectories change neighbour
work; this is a policy-cost comparison, not an algorithmically neutral speedup. No audit, build or
other task GPU experiment overlapped these admitted timing pairs.

A fresh ordinary production CLI run cost **3.008001 s** per simulated second, with **259 CFL-warning
steps**. Its one-second position/velocity bytes match the native baseline exactly. The production
binary was reused from the earlier source-qualified export, not freshly Cargo-built. Its hash is
retained; the native experiment was freshly compiled from the unchanged device sources.

The native driver has a separate acceptance API, no cancellation callback or published CFL warnings,
and a fixed 512-neighbour capacity with an overflow audit. Its checked timings cannot be presented as
production timings. The experimental fine policy still needs approximately **2.5×** its measured
throughput to reach real time at this size. The cheaper four-pass 1/240 policy costs 5.357 s for five
simulated seconds, but fails both transient density and tank volume; near-real-time cost is not admission.

![Density and cost](/docs/project/development/milestones/05/assets/physical-accuracy-v1/density-cost.png)

Recommended disposition:

1. **Preserve production parameters and all ten optimisations.** Label the present policy as stable
   within its earlier bounded qualification, not as meeting this accuracy criterion.
2. For further isolated study, use **dt≈2.083 ms, eight passes, correction scale 0.5, εh²=2,
   h/Δx=2, lattice-calibrated mass and existing artificial pressure 0.1h² at 0.2h** with a
   compression-only constraint. These are candidate parameters, not a production recommendation.
   Do not substitute the cheaper 4.167 ms/four-pass setting or claim the candidate is converged.
3. Resolve density-aware wall support and free-surface treatment together, then qualify the
   artificial-pressure/timestep relationship. The signed under-density response, wall deficiency,
   strong regularisation and correction scaling have supported mechanisms and intervention evidence;
   their separate contributions to long-time error are not uniquely identified by this campaign.
4. Choose solver work from current-position residuals, tail compression, separation and boundary
   budgets, with finite iteration limits and explicit failure behaviour. Test whether residual-driven
   termination beats fixed work only after the equilibrium model passes the tank and independent
   timestep/iteration sweeps. This is a future design recommendation, not an implemented controller.
5. Repeat the accepted policy's scene/duration ladder and ordinary production performance campaign
   across backends before revising any defaults or physical comparison contract.

The independent calculations and parameter isolation tests passed locally: **nine focused tests**, including
self-density, strict support, symmetry, lattice calibration, baseline byte preservation, malformed health
input and containment/coincidence reporting. The complete Rust suite, fresh cross-backend trajectories,
device memcheck, effects-enabled physical qualification and hosted checks were not run. Most raw intermediate states could not be retained after the PC
temporary directory disappeared; the complete production output, selected tank states and numerical
summaries were transferred before that loss. There is no
claim of engineering-CFD accuracy, continuous-time stability, pressure accuracy, or validation beyond
five seconds. Fewer iterations, smaller timesteps, finite state and plausible images are individually
insufficient evidence of physical convergence.

## References used

<a name="ref-s004"></a> **S004** — Macklin and Müller (2013), *Position Based Fluids*, equations 1–13 and Algorithm 1.
[Source record](/docs/research/sources/004-macklin-muller-position-based-fluids.md).

<a name="ref-s052"></a> **S052** — Akinci et al. (2012), *Versatile Rigid-Fluid Coupling for Incompressible SPH*.
[Source record](/docs/research/sources/052-akinci-rigid-fluid-coupling.md).
