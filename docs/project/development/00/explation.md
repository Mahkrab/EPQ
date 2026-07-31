# Position Based Fluids Mathematics

## State and prediction

### Apply external acceleration

#### Variables 

- $i$: the index of the particle.
- $\mathbf{v}_i$: particle $i$'s current velocity.
- $\mathbf{v}_i^*$: its velocity after external acceleration has been applied.
- $\mathbf{a}_{\mathrm{ext},i}$: external acceleration, such as gravity.
- $\Delta t$: the duration of one simulation step.

```math
\mathbf{v}_i^*
=
\mathbf{v}_i+\Delta t\,\mathbf{a}_{\mathrm{ext},i}
```

#### Meaning

The particle's velocity is changed by acceleration: 

```math
\text{new velocity} 
= 
\text{old velocity} 
+ 
\text{acceleration}\times\text{time}
```

For example, gravity makes the downward velocity increase during every timestep.

*The star in $`\mathbf{v}_i^*`$ means that this is an intermediate velocity, $\therefore$ it is not necessarily the final velocity for the step.*

### Predict the new position 

#### Variables 

- $\mathbf{x}_i$: particle $i$'s position at the start of the timestep.
- $\mathbf{p}_i$: its predicted position.
- $\mathbf{v}_i^*$: its post-acceleration velocity.
- $\Delta t$: the timestep duration.

```math
\mathbf{p}_i
=
\mathbf{x}_i+\Delta t\,\mathbf{v}_i^*
```

#### Meaning

The solver predicts where the particle would move if it travlled at $\mathbf{v}_i^*$ for one timestep. 
This position is only a prediction. The density and boundary solvers may subsequently move it.

### CFL timestep check

#### Variables

- $\Delta t$: the proposed timestep.
- $\lambda_{\mathrm{CFL}}$: a dimensionless safety factor, usually less than
  $1$.
- $d_p$: the characteristic particle diameter.
- $\mathbf{v}_i^*$: particle $i$'s post-acceleration velocity.
- $\lVert\mathbf{v}_i^*\rVert$: particle $i$'s speed.
- $\max_i\lVert\mathbf{v}_i^*\rVert$: the greatest speed of any particle.

```math
\Delta t
\leq
\lambda_{\mathrm{CFL}}
\frac{d_p}{\max_i\lVert\mathbf{v}_i^*\rVert}
```

A prticle should not travel too far during a single timestep. The fastest particle therefore determines the maximum timestep:

```math
\text{maximum timestep}
\approx
\frac{\text{particle size}}{\text{fastest speed}}
\times
\text{safety factor}
```

For example, if particles are $`0.02\,\mathrm{m}`$ wide, the fastest one travels at $`1\,\mathrm{m,s^{-1}}`$, and the safety factor is $0.4$, then:


```math
\Delta t
\leq
0.4\frac{0.02}{1}
=
0.008\,\mathrm{s}
```

## Finding neighbouring particles

### Support and interaction sets

#### Variables

- $i$: the particle whose neighbours are being found.
- $j$: a possible neighbouring particle.
- $\mathbf{p}_i$ and $\mathbf{p}_j$: predicted particle positions.
- $\lVert\mathbf{p}_i-\mathbf{p}_j\rVert$: the distance between particles $i$
  and $j$.
- $h$: the kernel support radius.
- $\mathcal{S}_i$: particles within $h$, including particle $i$ itself.
- $\mathcal{N}_i$: interacting neighbours, excluding particle $i$.

```math
\mathcal{S}_i
=
\lbrace
j\mid
\lVert\mathbf{p}_i-\mathbf{p}_j\rVert<h
\rbrace
```

```math
\mathcal{N}_i
=
\mathcal{S}_i\setminus\{i\}
```

#### Meaning

$\mathcal{S}_i$ contains every particle closer than $h$ to particle $i$. It inclues $i$ itself becuase its distance from itself is zero.

$\mathcal{N}_i$ removes partivle $i$ itself. It is used for interactions that require a direction between two different particles. 

The initial solver checks every pair of particles. For ${N}$ particles, it requires approximately $N^2$ comparisons.

$\therefore$ its time complexity is:

```math
\Theta(N^2)
```

This is slow for large simulations, but it is straightforward and useful as a reference implementation.

## SPH kernels

A kernel is a weighting function. Nearby particles receive a large $\text{weight}$, while particles new or betond the support radius recieve a small or zero $\text{weight}$

### Relative displacement and distance

#### Variables

- $\mathbf{p}_i$ and $\mathbf{p}_j$: predicted particle positions.
- $\mathbf{r}_{ij}$: the displacement vector from particle $j$ to particle
  $i$.
- $r_{ij}$: the scalar distance between the particles.
- $\lVert\cdot\rVert$: vector length.

```math
\mathbf{r}_{ij}
=
\mathbf{p}_i-\mathbf{p}_j
```

```math
r_{ij}
=
\lVert\mathbf{r}_{ij}\rVert
```

#### Meaning

$`\mathbf{r}_{ij}`$ records both distance and direction. $`r_{ij}`$ contains only the distance.

*The two r's are different if you look closely.*

#### Variables

- $r$: the distance between two particles.
- $h$: the kernel support radius.
- $W_{\mathrm{poly6}}(r,h)$: the scalar density weight.

```math
W_{\mathrm{poly6}}(r,h)=\begin{cases}\dfrac{315}{64\pi h^9}(h^2-r^2)^3, & 0\leq r<h,\\[0pt]0, & r\geq h.\end{cases}
```

#### Meaning 

When another particle is inside the support radius, it contributes to the density estimate:

- A very close particle has a large weight. 
- The weight decreases smoothly as $r$ approches $h$
- At or beyond $h$, the contribution is 0.

Poly6 produces a scalar weight. It tells us how much a particle contributes to density, but it does not provide a correction direction.

### Spiky gradient

#### Variables

- $\mathbf{r}$: the displacement vector between two particles.
- $r=\lVert\mathbf{r}\rVert$: the distance between them.
- $h$: the kernel support radius.
- $\mathbf{r}/r$: a unit vector giving their relative direction.
- $\mathbf{G}_{\mathrm{spiky}}(\mathbf{r},h)$: the vector used to construct
  position-correction directions.
- $\mathbf{0}$: the zero vector.

```math
\mathbf{G}_{\mathrm{spiky}}(\mathbf{r},h)=\begin{cases}-\dfrac{45}{\pi h^6}(h-r)^2\dfrac{\mathbf{r}}{r}, & 0<r<h,\\[0pt]\mathbf{0}, & r=0\text{ or }r\geq h.\end{cases}
```

#### Meaning

The Spiky gradient supplies both: 

- A strength based on how close the particles are
- A direction based on $\mathbf{r}/r$

It is zero outside the support radius.

At $r=0$, the direction $\mathbf{r}/r$ would require division by zero.
$\therefore$ two particles at the same position do not define a unique direction. The implementation therefore returns the zero vector. 

This prevents invalid floating point values, but it does not seperate two perfectly overlapping particles. 

## Density estimation

### Physical and normalised density

#### Variables

- $m$: the common mass of every fluid particle.
- $\rho_i^{\mathrm{phys}}$: the physical mass density around particle $i$.
- $\widetilde{\rho}_i$: the normalised, or mass-divided, density.
- $\mathcal{S}_i$: the support set, including particle $i$.
- $r_{ij}$: the distance between particles $i$ and $j$.
- $h$: the support radius.
- $W_{\mathrm{poly6}}$: the Poly6 density kernel.

```math
\rho_i^{\mathrm{phys}}
=
m
\sum_{j\in\mathcal{S}_i}
W_{\mathrm{poly6}}(r_{ij},h)
```

```math
\widetilde{\rho}_i
=
\sum_{j\in\mathcal{S}_i}
W_{\mathrm{poly6}}(r_{ij},h)
```

#### Meaning 

The physical density is estimated by adding the kernel contributions of nearby particles and multiplying each contribution by particle mass. 

Because every particle has the same mass, the solver can divide density by $m$: 

#### Variables

- $\widetilde{\rho}_i$: the mass-divided density.
- $\rho_i^{\mathrm{phys}}$: the physical density.
- $m$: the common fluid-particle mass.

```math
\widetilde{\rho}_i
=
\frac{\rho_i^{\mathrm{phys}}}{m}
```

#### Meaning 

This removes a repeated mass factor from later equations. Although it is called "normalised density", $\widetilde{\rho}$ is not necessarily dimensionsless.

### Density constraint 

#### Variables

- $C_i(\mathbf{p})$: the density constraint value for particle $i$.
- $\widetilde{\rho}_i$: the estimated normalised density.
- $\widetilde{\rho}_0$: the desired normalised rest density.
- $\rho_i^{\mathrm{phys}}$: the estimated physical density.
- $\rho_0^{\mathrm{phys}}$: the desired physical rest density.
- $\mathbf{p}$: the collection of all predicted particle positions.

```math
C_i(\mathbf{p})
=
\frac{\widetilde{\rho}_i}{\widetilde{\rho}_0}-1
=
\frac{\rho_i^{\mathrm{phys}}}{\rho_0^{\mathrm{phys}}}-1
```

#### Meaning

This measures the relative differece btween the current density and the target density: 

- $C_i=0$: the density is exactly correct;
- $C_i>0$: the region is too dense or compressed;
- $C_i<0$: the region is less dense than the rest density.

For example, if the density is $`5\%`$ too high, then:

#### Variables

- $C_i$: the resulting relative density contraint error.
- 1.05: the current density divided by the rest density.

```math
C_i
=
1.05-1
=
0.05
```

#### Meaning

The solver tries to move particles until $C_i$ is close to zero.

## Density correction directions

### Substituded gradient direction 

#### Variables 

- $i$: the particle whose density constraint is being solved.
- $k$: the particle whose effect on constraint $i$ is being considered.
- $\mathbf{g}_k^{(i)}$: the correction direction associated with particle $k$
  and constraint $i$.
- $\widetilde{\rho}_0$: the normalised rest density.
- $\mathcal{N}_i$: the neighbours of particle $i$, excluding itself.
- $\mathbf{r}_{ij}$: the displacement from particle $j$ to particle $i$.
- $\mathbf{r}_{ik}$: the displacement from particle $k$ to particle $i$.
- $\mathbf{G}_{\mathrm{spiky}}$: the Spiky gradient.
- $h$: the support radius.

```math
\mathbf{g}_k^{(i)}
=
\begin{cases}
\dfrac{1}{\widetilde{\rho}_0}
\displaystyle\sum_{j\in\mathcal{N}_i}
\mathbf{G}_{\mathrm{spiky}}(\mathbf{r}_{ij},h),
& k=i,\\[0pt]
-\dfrac{1}{\widetilde{\rho}_0}
\mathbf{G}_{\mathrm{spiky}}(\mathbf{r}_{ik},h),
& k\in\mathcal{N}_i,\\[0pt]
\mathbf{0},
& \text{otherwise.}
\end{cases}
```

#### Meaning 

This equation asks: 

- In which direction would moving particle $k$ change particle $i$'s density constrint? 

There are three cases:

1. When $k=i$, add the effects of every neighbour.
2. When $k$ is one of $i$'s neihbours, use the opposite pairwise direction.
3. When $k$ is unrelated to $i$, it has no effect, so the result is zero.

The density itself is calculated using Poly6. However the correction direction is deliberately built using the Spiky gradient becuase it generally provides more usefull pressure like correction directions. 

Therefore. $\mathbf{g}_k^{(i)}$ is a solver defined substituted direction. It is not literally the analytical gradient of the Poly6 density formula. 

## Constraint projection

### Genric Position based dynamics correlation

#### Variables

- $C_i$: the value of constraint $i$.
- $\Delta\mathbf{p}_k^{(i)}$: the correction applied to particle $k$ because
  of constraint $i$.
- $m_k$: the mass of particle $k$.
- $w_k=1/m_k$: the inverse mass of particle $k$.
- $\nabla_{\mathbf{p}_k}C_i$: the direction in which moving particle $k$
  changes constraint $i$.
- $j$: an index covering every particle affected by the constraint.
- $\varepsilon$: a small positive regularisation value.

```math
\Delta\mathbf{p}_k^{(i)}
=
-\frac{
w_k C_i
}{
\displaystyle
\sum_j
w_j
\left\lVert
\nabla_{\mathbf{p}_j}C_i
\right\rVert^2
+
\varepsilon
}
\nabla_{\mathbf{p}_k}C_i
```

#### Meaning

This is the general Position-Based Dynamics rule for moving particles so that a constraint becomes closer to zero. 

The correction depends on: 

- How severly the constraint is violated
- Whihc direction changes it
- How freely each particle is allowed to move
- The combined strength of all relevant correction directions.

Inverse mass controls how much a particle moves: 

- A smaller mass means a larger inverse mass and more movement
- A larger mass means a smaller inverse mass and less movement
- A fixed particle has $w_k=0$, so it does not move.

This small $\varepsilon$ prevents divisio by zero or by a very small denominator.

### PBF constraint multiplier

#### Variables

- $\lambda_i$: the scalar correction multiplier for particle $i$'s density
  constraint.
- $C_i$: the density constraint error.
- $\mathbf{g}_k^{(i)}$: the substituted correction direction associated with
  particle $k$.
- $\sum_k$: a sum over particle $i$ and its affected neighbours.
- $\varepsilon$: a positive regularisation value.


```math
\lambda_i
=
-
\frac{C_i}{
\displaystyle
\sum_k
\left\lVert
\mathbf{g}_k^{(i)}
\right\rVert^2
+
\varepsilon
}
```

#### Meaning 

$\lambda_i$ converts particle $i$'s density error into a correction strength. 
A large density error generally produces a larger correlation. The denominator prevents an excessive correction directions are present.

For positive density error, $C_i>0$, the leading minus normally makes $\lambda_i$ negative. The final direction of movement also depends on the Spiky gradient.

### Fluid particle position correction

#### Variables 

- $\Delta\mathbf{p}_i$: the total correction for particle $i$.
- $\widetilde{\rho}_0$: the normalised rest density.
- $\mathcal{N}_i$: the set of interacting neighbours.
- $\lambda_i$ and $\lambda_j$: the density multipliers for particles $i$ and
  $j$.
- $s_{\mathrm{corr},ij}$: an optional artificial-pressure term.
- $\mathbf{r}_{ij}$: the displacement between particles $i$ and $j$.
- $\mathbf{G}_{\mathrm{spiky}}$: the correction-direction operator.
- $h$: the support radius.

```math
\Delta\mathbf{p}_i
=
\frac{1}{\widetilde{\rho}_0}
\sum_{j\in\mathcal{N}_i}
\left(
\lambda_i+\lambda_j+s_{\mathrm{corr},ij}
\right)
\mathbf{G}_{\mathrm{spiky}}(\mathbf{r}_{ij},h)
```

#### Maning

Every neighbour contributes a small movement to particle $i$. The contribution uses: 

- Particle $i$'s density error
- Neighbour $j$'s density error
- An optional artificial pressure correction
- The direction between the particles 

Adding all the neighbour contributions gives the total change in predicted position.

### Apply the correction

#### Variables

- $\mathbf{p}_i$: the current working predicted position.
- $\Delta\mathbf{p}_i$: the correction calculated for this iteration.
- $\leftarrow$: replace the value on the left with the result on the right.


```math
\mathbf{p}_i
\leftarrow
\mathbf{p}_i+\Delta\mathbf{p}_i
```

#### Meaning

This moves the predicted position by the calculated correction.

The solver must use **Jacobi ordering**:

1. Calculate every $\lambda_i$ from the same position state.
2. Calculate every $\Delta\mathbf{p}_i$ from that same state.
3. Store the corrections separately.
4. Only then update all predicted positions.

Particle $0$ must not be updated before particle $1$'s correction has been
calculated. Otherwise, later particles would see newer data than earlier
particles, and the result would depend on iteration order.

## Reconstructing velocity

### Final velocity and position

#### Variables

- $\mathbf{x}_i$: the position at the start of the timestep.
- $\mathbf{p}_i$: the corrected final predicted position.
- $\mathbf{v}_i$: the reconstructed velocity.
- $\Delta t$: the timestep.

```math
\mathbf{v}_i
\leftarrow
\frac{\mathbf{p}_i-\mathbf{x}_i}{\Delta t}
```

```math
\mathbf{x}_i
\leftarrow
\mathbf{p}_i
```

#### Meaning

The solver calculates the velocity that would have produced the particle's
actual corrected movement:

#### Variables

- velocity: the reconstructed velocity.
- change in position: the corrected displacement during the timestep.
- time: the timestep duration.

```math
\text{velocity}
=
\frac{\text{change in position}}{\text{time}}
```

#### Meaning

This is important because density and boundary corrections may have moved the
particle away from its original predicted position.

After calculating velocity, the corrected predicted position becomes the
particle's new current position.

## Measuring density error

### Per-particle error

#### Variables

- $e_i$: the relative density error for particle $i$.
- $\widetilde{\rho}_i$: the measured normalised density.
- $\widetilde{\rho}_0$: the target normalised density.
- $\lvert\cdot\rvert$: absolute value.


```math
e_i
=
\left\lvert
\frac{\widetilde{\rho}_i}{\widetilde{\rho}_0}-1
\right\rvert
```

#### Meaning

This reports how far the density is from the target without caring whether it
is too high or too low.

For example:

- a density $1.03$ times the target gives $e_i=0.03$;
- a density $0.97$ times the target also gives $e_i=0.03$.

Both represent a $`3\%`$ error.

### Mean and maximum density error

#### Variables

- $\mathcal{E}$: the set of particles selected for evaluation.
- $\lvert\mathcal{E}\rvert$: the number of particles in the evaluation set.
- $e_i$: particle $i$'s relative density error.
- $E_{\mathrm{mean}}$: the average density error.
- $E_{\max}$: the largest density error.

```math
E_{\mathrm{mean}}
=
\frac{1}{\lvert\mathcal{E}\rvert}
\sum_{i\in\mathcal{E}}e_i
```

```math
E_{\max}
=
\max_{i\in\mathcal{E}}e_i
```

#### Meaning

The mean answers:

> How accurate is the simulation on average?

The maximum answers:

> How bad is the worst particle?

Both are useful. A low mean can hide a few particles with extremely large
errors, while the maximum alone does not describe the typical particle.

The evaluation set must be defined carefully. For example, surface particles
naturally have fewer neighbours and may behave differently from interior
particles.

## Simple plane boundaries

### Plane constraint

#### Variables

- $\mathbf{p}_i$: the predicted particle position.
- $\mathbf{n}$: a unit normal pointing towards the permitted side of the
  plane.
- $d$: the plane offset.
- $\mathbf{n}\cdot\mathbf{p}_i$: the dot product.
- $C_{\mathrm{plane}}$: the signed plane constraint value.

```math
C_{\mathrm{plane}}(\mathbf{p}_i)
=
\mathbf{n}\cdot\mathbf{p}_i-d
\geq 0
```

#### Meaning

This defines which side of a plane the particle is allowed to occupy. Because
$\mathbf{n}$ is a unit vector:

- $C_{\mathrm{plane}}>0$: the particle is on the permitted side;
- $C_{\mathrm{plane}}=0$: the particle is on the plane;
- $C_{\mathrm{plane}}<0$: the particle has penetrated the boundary.

### Remove plane penetration

#### Variables

- $\mathbf{p}_i$: the penetrated particle position.
- $C_{\mathrm{plane}}(\mathbf{p}_i)$: the negative signed distance.
- $\mathbf{n}$: the outward unit normal.

```math
\mathbf{p}_i
\leftarrow
\mathbf{p}_i
-
C_{\mathrm{plane}}(\mathbf{p}_i)\mathbf{n}
```

#### Meaning

When the constraint is negative, subtracting it creates a positive movement
along the normal.

For example, suppose the particle is $`0.02\,\mathrm{m}`$ inside the boundary:

#### Variables

- $C_{\mathrm{plane}}$: the signed penetration distance.



```math
C_{\mathrm{plane}}
=
-0.02
```

The resulting movement along the normal is:

#### Variables

- $\mathbf{n}$: the outward unit normal.
- $0.02$: the penetration depth in metres.

```math
-(-0.02)\mathbf{n}
=
0.02\mathbf{n}
```

#### Meaning

This places the particle exactly on the plane.

Plane projection prevents penetration, but it does not contribute to the SPH
density estimate. Fluid next to the wall can therefore appear to have missing
neighbours.

## Density-aware boundary particles

### Boundary sample volume and pseudo-mass

#### Variables

- $b$: a boundary sample.
- $l$: a neighbouring boundary sample.
- $\mathbf{x}_b$ and $\mathbf{x}_l$: the fixed positions of boundary samples.
- $W$: the selected scalar SPH density kernel.
- $h$: the support radius.
- $V_b$: the volume represented by boundary sample $b$.
- $\rho_0^{\mathrm{phys}}$: the physical rest density.
- $\Psi_b$: boundary sample $b$'s SPH pseudo-mass.

```math
V_b
=
\left(
\sum_l
W(\mathbf{x}_b-\mathbf{x}_l,h)
\right)^{-1}
```

```math
\Psi_b
=
\rho_0^{\mathrm{phys}}V_b
```

#### Meaning

The first equation estimates how much volume one boundary sample represents.
If many boundary samples are packed closely together, their kernel sum is
large, so each sample represents a smaller volume.

The second equation converts this volume into a density contribution that
behaves like mass in SPH calculations.

$\Psi_b$ is a pseudo-mass used for density estimation. It is not the physical
inertial mass of the solid object.

### Density including boundary samples

#### Variables

- $\rho_i^{\mathrm{phys}}$: the physical density estimated for fluid particle
  $i$.
- $\mathcal{S}_i$: the nearby fluid particles, including $i$.
- $m_j$: the mass of fluid particle $j$.
- $\mathbf{p}_i$ and $\mathbf{p}_j$: fluid-particle positions.
- $\mathcal{B}_i$: the boundary samples near fluid particle $i$.
- $\Psi_b$: the pseudo-mass of boundary sample $b$.
- $\mathbf{x}_b$: the fixed boundary-sample position.
- $W$: the density kernel.
- $h$: the support radius.


```math
\rho_i^{\mathrm{phys}}
=
\sum_{j\in\mathcal{S}_i}
m_jW(\mathbf{p}_i-\mathbf{p}_j,h)
+
\sum_{b\in\mathcal{B}_i}
\Psi_bW(\mathbf{p}_i-\mathbf{x}_b,h)
```

#### Meaning

Density now has two parts:

#### Variables

- fluid contribution: density supplied by neighbouring fluid particles.
- boundary contribution: density supplied by nearby boundary samples.

 

```math
\text{density}
=
\text{fluid contribution}
+
\text{boundary contribution}
```

#### Meaning

The boundary samples replace some of the density contribution that would
otherwise be missing near a solid wall. This can produce more consistent fluid
density near boundaries than simple plane projection.

### Normalised boundary weight

#### Variables

- $\Psi_b$: the boundary pseudo-mass.
- $m$: the common fluid-particle mass.
- $\widetilde{\Psi}_b$: the boundary contribution expressed in the solver's
  normalised scale.

 

```math
\widetilde{\Psi}_b
=
\frac{\Psi_b}{m}
```

#### Meaning

The rest of the equal-mass solver has divided physical density by the common
fluid mass $m$. Boundary pseudo-mass must be divided by the same value to use
the same density scale.

### Correction direction with boundaries

#### Variables

- $\mathbf{g}_i^{(i)}$: the correction direction for particle $i$'s own
  constraint.
- $\widetilde{\rho}_0$: the normalised rest density.
- $\mathcal{N}_i$: nearby fluid neighbours.
- $\mathcal{B}_i$: nearby boundary samples.
- $\mathbf{r}_{ij}$: the displacement between fluid particles.
- $\widetilde{\Psi}_b$: the normalised boundary weight.
- $\mathbf{p}_i-\mathbf{x}_b$: the displacement from boundary sample $b$ to
  particle $i$.
- $\mathbf{G}_{\mathrm{spiky}}$: the correction-direction operator.
- $h$: the support radius.

 

```math
\mathbf{g}_i^{(i)}
=
\frac{1}{\widetilde{\rho}_0}
\left[
\sum_{j\in\mathcal{N}_i}
\mathbf{G}_{\mathrm{spiky}}(\mathbf{r}_{ij},h)
+
\sum_{b\in\mathcal{B}_i}
\widetilde{\Psi}_b
\mathbf{G}_{\mathrm{spiky}}(\mathbf{p}_i-\mathbf{x}_b,h)
\right]
```

#### Meaning

The particle's correction direction now accounts for both:

- nearby fluid particles;
- nearby solid-boundary samples.

Changing the density formula alone would be insufficient. Because boundaries
affect density, they must also affect the direction used to reduce density
error.

This updated $\mathbf{g}_i^{(i)}$ also changes the denominator used to
calculate $\lambda_i$.

### Fluid correction with static boundaries

#### Variables

- $\Delta\mathbf{p}_i$: the total correction for fluid particle $i$.
- $\widetilde{\rho}_0$: the normalised rest density.
- $\mathcal{N}_i$: the fluid neighbours.
- $\mathcal{B}_i$: the nearby boundary samples.
- $\lambda_i$ and $\lambda_j$: the fluid density multipliers.
- $s_{\mathrm{corr},ij}$: the artificial-pressure term.
- $\widetilde{\Psi}_b$: the normalised boundary weight.
- $\mathbf{G}_{\mathrm{spiky}}$: the correction-direction operator.
- $\mathbf{r}_{ij}$: the fluid-particle displacement.
- $\mathbf{p}_i-\mathbf{x}_b$: the fluid-to-boundary displacement.
- $h$: the support radius.

 

```math
\Delta\mathbf{p}_i
=
\frac{1}{\widetilde{\rho}_0}
\left[
\sum_{j\in\mathcal{N}_i}
\left(
\lambda_i+\lambda_j+s_{\mathrm{corr},ij}
\right)
\mathbf{G}_{\mathrm{spiky}}(\mathbf{r}_{ij},h)
+
\lambda_i
\sum_{b\in\mathcal{B}_i}
\widetilde{\Psi}_b
\mathbf{G}_{\mathrm{spiky}}(\mathbf{p}_i-\mathbf{x}_b,h)
\right]
```

#### Meaning

The first sum is the usual fluid-to-fluid correction. The second sum is the
fluid-to-boundary correction.

Only $\lambda_i$ appears in the boundary term because the boundary samples are
static:

- they do not have their own density constraints;
- they do not calculate their own $\lambda_b$;
- they do not receive position corrections.

The fluid particle moves while the boundary remains fixed.

## Complete solver loop

In plain language, one timestep is approximately:

1. Apply gravity or another external acceleration.
2. Predict every particle's new position.
3. Find each particle's neighbours.
4. Begin a fixed number of solver iterations.
5. Estimate every particle's density from the same position state.
6. Calculate every density constraint $C_i$.
7. Calculate every multiplier $\lambda_i$.
8. Calculate every correction $\Delta\mathbf{p}_i$.
9. Apply all corrections simultaneously.
10. Project particles out of boundaries if required.
11. Repeat the density-correction iteration.
12. Reconstruct velocity from the final corrected movement.
13. Accept the corrected positions.
14. Record mean and maximum density errors.

The most important Jacobi rule is:

> Read from one shared position state, write corrections into separate storage,
> and apply those corrections only after every particle has been processed.

## Parameters that are still undecided

| Parameter | Simple meaning |
| --- | --- |
| $\Delta t$ | How much simulated time passes in one step. |
| $\Delta x$ | Initial spacing between particle centres. |
| $d_p$ | Characteristic particle diameter used by checks such as CFL. |
| $h$ | Distance over which particles interact. |
| $h/\Delta x$ | Roughly controls how many neighbours contribute to each estimate. |
| $m$ | Common mass represented by each fluid particle. |
| $\rho_0^{\mathrm{phys}}$ | Target physical density of the liquid. |
| $\widetilde{\rho}_0$ | Target density after dividing out the common particle mass. |
| Solver iterations | Number of times positions are corrected per timestep. |
| $\varepsilon$ | Prevents unstable division by very small gradient sums. |
| $k_{\mathrm{corr}}$ | Expected strength of artificial pressure. |
| $\Delta q$ | Expected reference separation used by artificial pressure. |
| $n_{\mathrm{corr}}$ | Expected exponent controlling how sharply artificial pressure changes with distance. |
| Boundary model | Either simple plane projection or density-aware boundary particles. |
| $\mathcal{E}$ | Particles included in the reported density-error statistics. |

The $k_{\mathrm{corr}}$, $\Delta q$ and $n_{\mathrm{corr}}$ parameters imply
that an artificial-pressure formula is intended, but that formula is currently
missing from the numerical design.

## Boundary-model comparison

### Plane projection

- Simple and inexpensive.
- Easy to test.
- Stops visible penetration.
- Does not compensate for missing fluid neighbours near a wall.
- May produce inaccurate density near boundaries.

### Density-aware boundary particles

- More complex.
- Allows boundary samples to contribute to density.
- Usually gives better density behaviour near walls.
- Requires boundary sampling, pseudo-mass calculation and modified correction
  equations.
- Introduces more implementation and validation work.

Only one should be selected for the initial reference solver so that the
baseline remains clearly defined.
