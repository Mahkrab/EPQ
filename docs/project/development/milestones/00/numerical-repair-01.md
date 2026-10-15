# Initial numerical regularisation repair

## Problem and scope

The public CLI exposed two separate defects: inaccurate axis contact and particle collapse during
falling-block runs. The axis repair remains documented in the
[numerical contract](/docs/project/development/milestones/00/phases/phase-00-design-contract.md).
This record covers the first repair of the collapse: an equation and scaling audit, independent
regressions, and a revised regularisation default. It does not establish final fluid quality.
It describes the historical `defaults-v2` setting; the
[second repair](/docs/project/development/milestones/00/numerical-repair-02.md) subsequently selected
`defaults-v3`. The implementation links therefore include subsequent repairs.

The retained implementation is Maelstrom commit
[`54c5176fe0475b39e53759f11aab355c4c815583`](https://github.com/Mahkrab/Maelstrom/tree/54c5176fe0475b39e53759f11aab355c4c815583),
also pinned by EPQ's gitlink. This intermediate repair was not committed separately;
the links identify the final combined implementation, not a reconstruction of the earlier working tree.
The measurements below remain the local observations recorded during this repair.

## Audit and decision

The audit compared density normalisation, correction directions, multiplier denominators and artificial
pressure with the PBF equations. The paper describes regularisation for small gradient
denominators and tensile instability at low neighbour counts; it does not specify Maelstrom's SI
parameter values.<sup><a href="#ref-s004">S004</a></sup> Equal particle mass cancels in the density
ratio. Normalised density has units of inverse cubic metres, substituted directions inverse metres,
relaxation inverse square metres, multipliers and artificial pressure square metres, and corrections
metres. The existing scaling follows those dimensions; no equation, sign or mass-normalisation
mismatch was found in the audited paths.

The original regularisation magnitude was insufficient. An independent binary64 calculation of a
pair at separation `0.9h` gives a per-particle correction of about `45.31h` with
`relaxation_scale = 1e-6`. With `relaxation_scale = 1.0`, it gives about `0.02852h`.
Production binary32 calculations reproduce this mechanism, so it is not explained by rounding alone.

The [first revised defaults](https://github.com/Mahkrab/Maelstrom/blob/54c5176fe0475b39e53759f11aab355c4c815583/config/defaults-v2.toml), built-in configuration and all seven
falling-block scene references initially selected `relaxation_scale = 1.0`, hence nominal relaxation
`100 m⁻²` at support `0.1 m`. The original
[defaults](https://github.com/Mahkrab/Maelstrom/blob/54c5176fe0475b39e53759f11aab355c4c815583/config/defaults-v1.toml) remain byte-for-byte intact for explicit comparison.
Configuration identity records the changed value; backend arithmetic remains `v2`.

## Verification

Checks ran on 14 October 2026 in WSL2 Ubuntu 24.04.5, Rust/Cargo 1.98.1,
`x86_64-unknown-linux-gnu`, with locked, offline Cargo commands.

The new [regularisation tests](https://github.com/Mahkrab/Maelstrom/blob/54c5176fe0475b39e53759f11aab355c4c815583/tests/solver_regularisation.rs) independently derive
density, constraints, multipliers and corrections for an asymmetric six-particle snapshot in 12
configurations: three spacings, two relaxation values, and artificial pressure enabled or disabled.
The oracle uses binary64 scalar equations and independently derives lattice rest density. Tolerances
follow the units of each quantity; the multiplier allowance includes relative rounding for the
large isolated-particle multipliers under the historical setting.

Fifteen sparse-pair cases across three spacings guard against corrections larger than a quarter of
support. Two 120-step small-scene regressions require distinct positions, density below twice rest
and mean absolute relative density error below 25%. These are coarse collapse guards, not final
physical acceptance thresholds. Both regressions failed before the default changed. A separate
test preserves the historical large correction and confirms it independently.

An existing neighbour-departure fixture now explicitly selects its original weak regularisation;
its departure, independent-oracle and incorrect-variant assertions remain intact. Configuration
tests distinguish historical and current input identities. CLI tests verify the current setting in
every bundled scene and byte-identical historical-setting replay after deleting its configuration
file. Fully recorded inputs do not acquire new defaults during replay.

Full debug and release runs each passed 130 integration tests and three unit tests, plus two
doctests in each profile. Formatting, all-target/all-feature checking and Clippy with warnings
denied, strict Rustdoc, and whitespace checks in both repositories passed.

Bounded release controls used 120 steps, checkpoints `0,1,4,12,120`, timestep `1/120 s`,
four Jacobi iterations, and identical initial particles and planes. Only relaxation changed; each
process had a 20-second timeout and all six completed. Density figures below are final mean
absolute relative errors, converted to percentages. Speed is the maximum recorded post-acceleration
speed across the run, not the final speed. These observations are not performance measurements.

| Scene | Distinct positions, original → revised | Mean density error, original → revised | Peak speed, original → revised (m/s) |
| --- | --- | --- | --- |
| `falling-block-04` (64 particles) | 8 → 64 | 103.92% → 9.06% | 136.03 → 9.02 |
| `falling-block-06` (216 particles) | 9 → 216 | 603.57% → 20.32% | 160.60 → 13.19 |
| `falling-block-10` (1,000 particles) | 8 → 1,000 | 3,865.59% → 2.66% | 201.82 → 5.49 |

After reinstalling `maelstrom`, the one-second command completed all 120 steps with 56 CFL
warnings and state identical to the earlier explicit-override control. A 12-step
`falling-block-20` check retained 8,000 distinct positions, with mean density error 1.76%.
Both had 20-second process limits. Replay of the user's original one-second result reproduced
its entire JSON document under the historical settings; the original file was preserved.

To reproduce a bounded comparison from the Maelstrom directory, run each setting into a new file:

```sh
timeout 20s maelstrom run falling-block-10 --steps 120 --checkpoints 0,1,4,12,120 \
  --config ./config/defaults-v1.toml --format json --output original.json
timeout 20s maelstrom run falling-block-10 --steps 120 --checkpoints 0,1,4,12,120 \
  --config ./config/defaults-v2.toml --format json --output revised.json
```

## Remaining limits

This completes the initial regularisation repair. Smaller blocks still show large speeds and
substantial free-surface or boundary density deficits. Further work must check separation,
correction-induced energy, convergence and the interaction with artificial pressure across
resolutions and impact states before freezing numerical or performance reference outputs. CFL
warnings remain diagnostics and are not a fluid-quality measure. The 8,000-particle ten-second
run, other platforms and hosted verification were not completed for this repair.

## References used

- <a name="ref-s004"></a> **S004** — Macklin and Müller, *Position Based Fluids* (2013).
  [Research source record](/docs/research/sources/004-macklin-muller-position-based-fluids.md).
