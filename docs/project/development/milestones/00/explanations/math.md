# Position-Based Fluids mathematics and behaviour

This document explains the Milestone 00 reference solver in accessible language. The
[Phase 0 design contract](phases/phase-00-design-contract.md) is the normative contract. If this explanation ever
disagrees with it, the milestone record wins and this document must be corrected.

The published method comes mainly from the SPH kernels in
[S003](/docs/research/sources/003-muller-charypar-gross-particle-based-fluid-simulation.md), the PBF equations and
loop in [S004](/docs/research/sources/004-macklin-muller-position-based-fluids.md), and the general position-based
update in [S050](/docs/research/sources/050-muller-position-based-dynamics.md). The exact numerical scale,
binary32 arithmetic, plane-only boundary, ordering, warnings and failure behaviour are Maelstrom project
decisions. The full provenance is recorded in the
[contract authority table](phases/phase-00-design-contract.md#contract-status-and-authority).

## Reference state, arithmetic and units

At the start of timestep $n$, particle $i$ has an accepted position $\mathbf{x}_i^n$ in metres and velocity
$\mathbf{v}_i^n$ in $\mathrm{m\,s^{-1}}$. A working predicted position is written $\mathbf{p}_i^{(l)}$, where
$l$ is the Jacobi iteration. Working values do not become accepted state until the entire timestep succeeds.

All configuration values, particle state, kernel calculations, solver arithmetic, derived values and serial
reductions use IEEE-754 binary32 (`f32`). Particle processing, neighbour lists and sums use ascending stable
particle identity. This stable order makes repeated serial runs deterministic on the same supported environment.
Fast-math reassociation or reduced precision would be a separate experiment.

The reference uses these project decisions:

| Quantity | Reference value or policy |
| --- | --- |
| Coordinates | Right-handed metres, positive $y$ upward |
| External acceleration | $(0,-9.81,0)\,\mathrm{m\,s^{-2}}$ |
| Fixed timestep | $\Delta t=1/120\,\mathrm{s}$ |
| Particle spacing and CFL diameter | $\Delta x=d_p=0.05\,\mathrm{m}$ |
| Kernel support | $h=2\Delta x=0.10\,\mathrm{m}$ |
| Physical rest density | $\rho_0^{\mathrm{phys}}=1000\,\mathrm{kg\,m^{-3}}$ |
| Solver work | Exactly four Jacobi iterations |
| Relaxation | $\varepsilon=10^{-6}h^{-2}=10^{-4}\,\mathrm{m^{-2}}$ nominally |
| Artificial pressure | Enabled: $k_{\mathrm{corr}}=0.1h^2=0.001\,\mathrm{m^2}$, $\Delta q=0.2h=0.02\,\mathrm{m}$, $n_{\mathrm{corr}}=4$ nominally |
| Boundaries | Static unit-normal planes acting on particle centres; no friction, restitution or boundary density |
| Optional velocity effects | XSPH viscosity and vorticity confinement disabled |
| Neighbour search | One rebuild after prediction per timestep |

The relationships in the table are authoritative. For example, $h$ comes from $2\Delta x$, and the relaxation
and artificial-pressure values come from $h$; they are not unrelated rounded values.

## Acceleration, prediction and CFL warning

External acceleration first produces an intermediate velocity:

```math
\mathbf{v}_i^*=\mathbf{v}_i^n+\Delta t\,\mathbf{a}_{\mathrm{ext},i}.
```

The initial position prediction is then:

```math
\mathbf{p}_i^{(0)}=\mathbf{x}_i^n+\Delta t\,\mathbf{v}_i^*.
```

The star means “working velocity”, not final velocity. Density correction and plane projection can change the
actual displacement, so the final velocity is reconstructed later.

The diagnostic maximum speed is

```math
v_{\max}=\max_i\|\mathbf{v}_i^*\|,
```

and the selected velocity CFL check is

```math
\Delta t\leq\lambda_{\mathrm{CFL}}\frac{d_p}{v_{\max}},
\qquad \lambda_{\mathrm{CFL}}=0.4.
```

This is a diagnostic, not an adaptive timestep. If $v_{\max}>0$ and the fixed timestep is greater than the
computed limit, the step continues and carries a non-fatal CFL warning. Equality passes. A successful warned run
accepts its state but cannot be described as a warning-free canonical baseline.

For an empty particle set, or any non-empty set whose post-acceleration speeds are all zero, Maelstrom defines
$v_{\max}=0$. The limit is then semantically unbounded, there is no division by zero and there is no warning.

## Three different kinds of neighbour set

The contract distinguishes fixed solver membership, active per-iteration membership and fresh audit membership.
Conflating them would change the experiment.

### Fixed interaction membership

After all initial predictions exist, brute force checks every distinct pair and builds:

```math
\mathcal{N}_i^{(0)}=
\lbrace j\ne i\mid
\left\|\mathbf{p}_i^{(0)}-\mathbf{p}_j^{(0)}\right\|\lt h
\rbrace.
```

The comparison is strict. A particle exactly $h$ away is not a neighbour. The list contains valid, unique
particles in ascending identity order and excludes $i$ itself. It is built once and is not rebuilt during the four
iterations.

### Active iteration support

Distances and kernel values are still recomputed from the current iteration positions. At iteration $l$:

```math
\mathcal{S}_i^{(l)}=
\{i\}\cup
\lbrace j\in\mathcal{N}_i^{(0)}\mid
\left\|\mathbf{p}_i^{(l)}-\mathbf{p}_j^{(l)}\right\|\lt h
\rbrace,
```

```math
\mathcal{N}_i^{(l)}=\mathcal{S}_i^{(l)}\setminus\{i\}.
```

Density support $\mathcal{S}$ includes the particle itself exactly once. Directional interaction $\mathcal{N}$
does not. An original neighbour that moves to $r\geq h$ contributes zero. A particle that was originally outside
and later moves inside is not added until the next timestep.

### Fresh correctness-audit support

At a requested accepted-state checkpoint, the audit ignores all solver-owned membership and performs a fresh
all-pairs strict-support search over the final accepted positions. This independently reveals error caused by the
fixed per-step approximation. Audit membership never feeds back into simulation.

## Poly6 density weight and Spiky correction direction

For displacement and distance

```math
\mathbf{r}_{ij}^{(l)}=\mathbf{p}_i^{(l)}-\mathbf{p}_j^{(l)},
\qquad
r_{ij}^{(l)}=\|\mathbf{r}_{ij}^{(l)}\|,
```

the three-dimensional Poly6 density kernel is

```math
W_{\mathrm{poly6}}(r,h)=
\frac{315}{64\pi h^9}(h^2-r^2)^3
\qquad\text{for }0\leq r\lt h,
```

```math
W_{\mathrm{poly6}}(r,h)=0
\qquad\text{for }r\geq h.
```

Poly6 is a scalar weight with units $\mathrm{m^{-3}}$. It is non-zero for self at $r=0$ and zero at the strict
support boundary.

The Spiky operator supplies a vector direction:

```math
\mathbf{G}_{\mathrm{spiky}}(\mathbf{r},h)=
-\frac{45}{\pi h^6}(h-r)^2\frac{\mathbf{r}}{r}
\qquad\text{for }0\lt r\lt h,
```

```math
\mathbf{G}_{\mathrm{spiky}}(\mathbf{r},h)=\mathbf{0}
\qquad\text{for }r=0\text{ or }r\geq h.
```

Its units are $\mathrm{m^{-4}}$. At zero distance, $\mathbf{r}/r$ has no unique direction. Returning zero is an
explicit Maelstrom numerical convention, not an analytical direction. It avoids invalid arithmetic but cannot
separate perfectly coincident particles.

These zero branches apply only to valid finite arguments. A negative scalar distance, non-positive $h$, or any
non-finite argument is invalid input and causes validation or timestep failure; it is not treated as
out-of-support zero.

## Physical density, normalised density and the lattice-derived mass

Every fluid particle has the same positive mass $m$. Physical density is

```math
\rho_i^{\mathrm{phys},(l)}=
m\sum_{j\in\mathcal{S}_i^{(l)}}
W_{\mathrm{poly6}}(r_{ij}^{(l)},h)
\quad[\mathrm{kg\,m^{-3}}].
```

Dividing out the common mass gives the solver's normalised density:

```math
\widetilde{\rho}_i^{(l)}=
\frac{\rho_i^{\mathrm{phys},(l)}}{m}
=
\sum_{j\in\mathcal{S}_i^{(l)}}
W_{\mathrm{poly6}}(r_{ij}^{(l)},h)
\quad[\mathrm{m^{-3}}].
```

“Normalised” here means mass-divided, not dimensionless.

The target $\widetilde{\rho}_0$ is derived from an interior cubic lattice rather than guessed. With
$h=2\Delta x$, strict support includes the 27 integer offsets whose length is less than $2\Delta x$:

```math
\widetilde{\rho}_0=
\sum_{\mathbf{r}\in\mathcal{L}}
W_{\mathrm{poly6}}(\|\mathbf{r}\|,h)
\approx8078.201335\,\mathrm{m^{-3}},
```

```math
m=\frac{\rho_0^{\mathrm{phys}}}{\widetilde{\rho}_0}
\approx0.123789933\,\mathrm{kg}.
```

The decimals are high-precision audit anchors, not copied runtime constants. The reference derives the values
with the binary32 kernel and lexicographic $(a,b,c)$ offset sum. Phase 1 must verify that calculation
independently with a justified floating-point tolerance.

## Density constraint and substituted directions

The dimensionless density error is

```math
C_i(\mathbf{p}^{(l)})=
\frac{\widetilde{\rho}_i^{(l)}}{\widetilde{\rho}_0}-1
=
\frac{\rho_i^{\mathrm{phys},(l)}}{\rho_0^{\mathrm{phys}}}-1.
```

$C_i>0$ means density is above rest density; $C_i<0$ means it is below rest density. The reference does not clamp
negative constraints or multipliers. Free-surface, isolated and single-particle states are valid even when their
density is far below the target.

PBF estimates density with Poly6 but deliberately uses Spiky for correction directions. Define
$\mathbf{g}_k^{(i,l)}$ as:

```math
\mathbf{g}_k^{(i,l)}
=\dfrac{1}{\widetilde{\rho}_0}
\displaystyle\sum_{j\in\mathcal{N}_i^{(l)}}
\mathbf{G}_{\mathrm{spiky}}(\mathbf{r}_{ij}^{(l)},h)
\qquad\text{for }k=i
```

```math
\mathbf{g}_k^{(i,l)}
=-\dfrac{1}{\widetilde{\rho}_0}
\mathbf{G}_{\mathrm{spiky}}(\mathbf{r}_{ik}^{(l)},h)
\qquad\text{for }k\in\mathcal{N}_i^{(l)}
```

```math
\mathbf{g}_k^{(i,l)}=\mathbf{0}
\qquad\text{otherwise}
```

$\mathbf{g}$ has units $\mathrm{m^{-1}}$. It is called a substituted direction because it is not literally the
analytical derivative of the Poly6 expression.

## Multiplier, artificial pressure and correction

The relaxed multiplier is

```math
\lambda_i^{(l)}=
-\frac{C_i(\mathbf{p}^{(l)})}
{\displaystyle\sum_{k\in\mathcal{S}_i^{(l)}}\left\|\mathbf{g}_k^{(i,l)}\right\|^2+\varepsilon}.
```

The denominator and $\varepsilon$ have units $\mathrm{m^{-2}}$, so $\lambda$ has units $\mathrm{m^2}$. The
relaxation prevents division by a zero or very small direction sum. The particular value
$10^{-6}h^{-2}$ is a scale-aware Maelstrom choice, not a calibrated material property.

Artificial pressure is mandatory in the reference:

```math
s_{\mathrm{corr},ij}^{(l)}=
-k_{\mathrm{corr}}
\left(
\frac{W_{\mathrm{poly6}}(r_{ij}^{(l)},h)}
{W_{\mathrm{poly6}}(\Delta q,h)}
\right)^{n_{\mathrm{corr}}}.
```

$0<\Delta q<h$ makes the denominator positive. The ratio is dimensionless, while
$k_{\mathrm{corr}}$ and $s_{\mathrm{corr}}$ have units $\mathrm{m^2}$ so they can be added to $\lambda$. The
paper supplies the empirical form and reported coordinate-space values; scaling the strength as $0.1h^2$ is the
project's dimensional choice.

The total fluid correction is

```math
\Delta\mathbf{p}_i^{(l)}=
\frac{1}{\widetilde{\rho}_0}
\sum_{j\in\mathcal{N}_i^{(l)}}
\left(\lambda_i^{(l)}+\lambda_j^{(l)}+s_{\mathrm{corr},ij}^{(l)}\right)
\mathbf{G}_{\mathrm{spiky}}(\mathbf{r}_{ij}^{(l)},h).
```

The units reduce to metres. Coincident distinct particles can have finite density, multipliers and artificial
pressure, but their Spiky direction is zero, so no arbitrary separating movement is created.

## Jacobi snapshots and plane projection

Each of the four iterations follows the same strict order:

1. Read only $\mathbf{p}^{(l)}$ and fixed membership $\mathcal{N}^{(0)}$ while calculating every active set,
   density, constraint, direction and multiplier.
2. After all multipliers exist, read the same position snapshot and complete multiplier snapshot while calculating
   every correction into separate storage.
3. Form every candidate with
   $\mathbf{q}_i^{(l)}=\mathbf{p}_i^{(l)}+\Delta\mathbf{p}_i^{(l)}$.

4. Project each candidate once against every configured plane in configuration order. The projected results form
   the next immutable snapshot $\mathbf{p}^{(l+1)}$.

No particle may see another particle's partly updated position or multiplier. This is Jacobi semantics even though
the first implementation is serial.

A plane uses a finite unit normal $\mathbf{n}$ pointing into the permitted halfspace and finite offset $d$:

```math
C_{\mathrm{plane}}(\mathbf{p})=\mathbf{n}\cdot\mathbf{p}-d\geq0.
```

If the computed value is negative, projection is

```math
\mathbf{p}\leftarrow
\mathbf{p}-C_{\mathrm{plane}}(\mathbf{p})\mathbf{n}.
```

The plane acts on the particle centre; $d_p$ does not create a hidden collision radius. A point exactly on the
plane is unchanged. A non-unit, zero or non-finite normal is invalid configuration and is rejected rather than
silently normalised. Phase 2 will freeze the input tolerance used to recognise unit normals.

Sequential projections are deterministic. After iteration four, every proposed position must satisfy every
configured plane. If a later projection has moved a point outside an earlier plane, the timestep fails rather than
accepting penetration. There is no friction, restitution, velocity reflection, boundary density or boundary
particle correction.

## Velocity reconstruction and atomic acceptance

After iteration four, velocity is reconstructed from the whole corrected displacement:

```math
\mathbf{v}_i^{n+1}=
\frac{\mathbf{p}_i^{(4)}-\mathbf{x}_i^n}{\Delta t},
\qquad
\mathbf{x}_i^{n+1}=\mathbf{p}_i^{(4)}.
```

The position and velocity arrays are still only proposed state. The step checks every produced value for
finiteness, checks identity and neighbour invariants, and checks all final plane constraints. Only when every
check passes are all positions and velocities accepted together.

If any stage fails, the complete working step is discarded. The previous accepted
$(\mathbf{x}^n,\mathbf{v}^n)$ remains unchanged; no partial particle or partial array update is visible. In a
multi-step run, the state after the last fully successful step remains accepted, and the failed step is not counted
as completed. Cancellation during a step follows the same rule. A CFL warning alone does not cause failure.

## Density-error audit

At a requested accepted-state checkpoint, fresh support sets produce:

```math
e_i=
\left|\frac{\widetilde{\rho}_i}{\widetilde{\rho}_0}-1\right|,
```

```math
E_{\mathrm{mean}}=
\frac{1}{|\mathcal{E}|}\sum_{i\in\mathcal{E}}e_i,
\qquad
E_{\max}=\max_{i\in\mathcal{E}}e_i,
```

where $\mathcal{E}$ contains every accepted fluid particle. A large finite density error is diagnostic and never
changes or invalidates state by itself. For an empty set, the audit reports sample count zero and both aggregates
as unavailable; it does not divide by zero or report zero, infinity or NaN.

The audit is outside primary solver timing and cannot mutate state. The primary backend-step boundary includes
step validation, acceleration, prediction, neighbour search, four iterations, reconstruction, final validation and
atomic commit. Scene/configuration loading, CLI parsing, audits, snapshots for presentation, serialisation,
logging, rendering and formatting are outside. Phase 7 later owns clock placement, warm-up, sampling and
aggregation policy without changing that logical boundary.

## Edge and failure classification

The behaviour most likely to be missed in tests is summarised here:

| Condition | Classification and behaviour |
| --- | --- |
| Empty particle set | Valid; unchanged successful step, speed zero, unbounded CFL limit, audit count zero and aggregates unavailable |
| One particle | Valid; self contributes to density, interaction set is empty, so only acceleration and planes move it |
| Coincident distinct particles | Valid; each is the other's neighbour, Poly6 contributes, Spiky is zero and no arbitrary separation is invented |
| Zero maximum speed | Valid; no division and no CFL warning |
| Exactly at $r=h$ | Valid edge; excluded from support and interactions, both kernels zero |
| Exactly on a plane | Valid edge; unchanged by that plane |
| Finite density error of any size | Valid state plus diagnostic value; no automatic rejection |
| CFL limit exceeded | Non-fatal warning; fixed timestep remains and otherwise valid state is accepted |
| Non-finite configuration value or invalid parameter domain | Invalid configuration; reject before work and preserve accepted state |
| Zero, non-finite or non-unit plane normal | Invalid configuration; reject, never silently normalise |
| Non-finite accepted position or velocity, duplicate identity, or invalid/out-of-range particle reference or index | Invalid simulation state; reject and preserve accepted state |
| Any non-finite intermediate or proposed value, broken neighbour invariant or final plane violation | Timestep failure; discard the whole proposal |

## Complete reference timestep

In one place, the ordered behaviour is:

1. Validate configuration, planes, identities, particle references and accepted-state finiteness.
2. Calculate every post-acceleration velocity and the warning-only CFL diagnostic without mutating accepted state.
3. Predict every $\mathbf{p}^{(0)}$.
4. Build one complete, stable, duplicate-free brute-force interaction set from the prediction snapshot.
5. Perform exactly four Jacobi iterations, each with immutable multiplier/correction reads and one ordered plane
   pass.
6. Reconstruct velocities from $\mathbf{p}^{(4)}-\mathbf{x}^n$.
7. Validate every produced value, invariant and final plane constraint.
8. Accept all positions and velocities together, or accept none.
9. Return the outcome and CFL status. Optional audits observe accepted state separately through a fresh search.

Every later backend must reproduce these mathematical sets, snapshots, edge cases, warning semantics and
transactional outcomes. Parallel reductions may be compared with justified tolerances, but different precision,
support inequalities, timesteps, iteration counts, mathematics, fast-math modes or adaptive updates are separate
experimental variants.

## Boundary alternative that is not part of the reference

[S052](/docs/research/sources/052-akinci-rigid-fluid-coupling.md) explains how sampled solid boundaries can
contribute pseudo-mass to density and reduce the missing-neighbour problem near walls. That approach changes the
density, direction and correction equations. It is retained in the normative record as researched context, but it
is not an alternative selectable by the Milestone 00 reference. Milestones 00 to 03 use planes only. Enabling
density-aware boundaries would require a separately documented experimental-contract revision.
