# Separation, energy and convergence repair

This records the earlier four-iteration `defaults-v3` repair. The
[broader qualification repair](/docs/project/development/milestones/00/numerical-repair-03.md)
owns the current defaults and the later large-impact findings.

## Starting point and scope

The [first repair](/docs/project/development/milestones/00/numerical-repair-01.md) prevented severe
coincidence collapse, but small blocks retained large speeds. This repair adds meaningful separation,
correction-induced energy, convergence and impact regressions, then selects the smallest tested
parameter change that satisfies them. It leaves the equations, four Jacobi iterations and transactional
acceptance unchanged. The [numerical contract](/docs/project/development/milestones/00/phases/phase-00-design-contract.md)
owns the revised defaults and verification bounds.

The retained implementation is Maelstrom commit
[`54c5176fe0475b39e53759f11aab355c4c815583`](https://github.com/Mahkrab/Maelstrom/tree/54c5176fe0475b39e53759f11aab355c4c815583),
also pinned by EPQ's gitlink. This intermediate repair was not committed separately;
the links identify the final combined implementation, including subsequent changes.
The measurements below remain the local observations recorded during this repair.

## Decision and implementation

Six new behavioural tests failed with `defaults-v2`. Its `relaxation_scale = 1.0` made a nominally
spaced isolated pair cross during correction, injected excessive motion into stationary blocks,
and failed impact and compression-convergence bounds. Independent binary64 calculations reproduce
the pair inversion, so this is not a rounding-only defect.

Bounded controls compared relaxation and artificial pressure together. In both the 64- and
216-particle blocks, keeping artificial-pressure strength `0.1` and raising relaxation scale to
`10.0` improved separation and settling. Lower artificial-pressure strengths improved the mean
density score but worsened separation: strength `0.001` produced exactly coincident particles in
the 216-particle block despite a low mean density error. The paper describes an empirical trade-off
between clustering and surface tension and notes that artificial-pressure parameters depend on
resolution and timestep.<sup><a href="#ref-s004">S004</a></sup>

The [current defaults](https://github.com/Mahkrab/Maelstrom/blob/54c5176fe0475b39e53759f11aab355c4c815583/config/defaults-v3.toml), built-in defaults and all falling-block
scenes therefore select `relaxation_scale = 10.0`, nominally `1000 m⁻²` at support `0.1 m`.
Artificial pressure stays unchanged. `defaults-v1.toml` and `defaults-v2.toml` retain their original
contents for comparisons and replay. Input identity distinguishes every setting; backend arithmetic
remains `v2`. Stronger relaxation accepts slower constraint correction in exchange for better
separation and bounded motion in the tested states.

## Verification

Checks ran locally on 14 October 2026 under WSL2 Ubuntu 24.04.5, Rust/Cargo 1.98.1,
`x86_64-unknown-linux-gnu`, using locked, offline Cargo commands.

The eight [fluid stability tests](https://github.com/Mahkrab/Maelstrom/blob/54c5176fe0475b39e53759f11aab355c4c815583/tests/fluid_stability.rs) cover:

- Sparse-pair ordering during every correction, and filled interior equilibrium.
- Unforced 64-particle blocks and floor impacts at spacings `0.025`, `0.05` and `0.10 m`.
- Perturbed impact and nominal 64- and 216-particle blocks through 360 accepted steps.
- A block compressed to `0.8` of reference spacing, evaluated at 4, 8 and 16 corrections.
- An explicit negative control preserving the intermediate pair inversion and energy failure.

Every dynamic step checks the relevant separation and energy bounds. Impact fixtures also require
actual floor contact, finite state, stable identity, containment, limited excess density and settling.
Metrics independently use binary64 distances, kernels, lattice rest density and specific kinetic and
gravitational energy. Density deficits are distinguished from compression; free surfaces are not
required to reach interior rest density. The compression fixture also agrees with the independent
timestep oracle in position and reconstructed velocity, and distinguishes an incorrect in-place
update. The existing stage audit now spans 18 configurations, including the new relaxation setting.

Bounds are project regression guards: minimum block separation is half the initial spacing, and
the stationary RMS displacement budget is one fifth of spacing per step, converted to specific
kinetic energy. They scale with spacing and timestep. They are not a hidden particle radius or a
claim of exact conservation under empirical artificial pressure. Production still performs four
iterations; the additional counts are untimed convergence studies.

Release controls used 120 steps, checkpoints `0,1,4,12,60,120` and a 20-second limit per process.
The matrix tested `(relaxation, pressure strength)` pairs `(1,0.1)`, `(10,0.1)`, `(10,0.01)`,
`(10,0.001)` and `(100,0.01)` on both small scenes. All ten completed. Peak speed below is the
largest recorded post-acceleration speed; separation is measured at the final snapshot. These are
deterministic behaviour observations, not performance measurements.

| Scene | Peak speed, intermediate → current (m/s) | Final minimum separation / spacing, intermediate → current | Mean absolute density error, intermediate → current |
| --- | --- | --- | --- |
| `falling-block-04` | 9.02 → 3.06 | 0.639 → 0.780 | 9.06% → 7.56% |
| `falling-block-06` | 13.19 → 3.62 | 0.221 → 0.773 | 20.32% → 5.09% |
| `falling-block-10` | 5.49 → 4.40 | 0.659 → 0.748 | 2.66% → 3.88% |

Additional bounded controls completed 360 steps for both small blocks with final separation above
`0.79` of spacing. The 1,000-particle control completed 120 steps. Its slightly higher mean density
error illustrates why the default was selected using separation and energy alongside density.

Full debug and release suites each passed 138 integration tests and three unit tests, plus two
doctests in each profile. Formatting, all-target/all-feature checking and Clippy with warnings
denied, strict Rustdoc and whitespace checks passed. CLI tests verify current defaults in every
bundled scene and exact recorded replay for both historical settings after deleting their original
configuration files.

The reinstalled one-second command completed 120 steps with 36 CFL warnings and matched the
override control's state. Both saved historical results replayed exactly and remained unchanged.
A bounded 12-step check of 8,000 particles completed with 8,000 distinct positions and no warnings.

## Limits

This completes the requested bounded stability repair. It does not certify all particle counts,
support ratios, initial conditions, timesteps or longer runs. Static planes still lack boundary-density
support; artificial pressure remains empirical; viscosity and vorticity are disabled. The large
ten-second run, other platforms, hosted checks and performance qualification remain unverified.

## References used

- <a name="ref-s004"></a> **S004** — Macklin and Müller, *Position Based Fluids* (2013).
  [Research source record](/docs/research/sources/004-macklin-muller-position-based-fluids.md).
