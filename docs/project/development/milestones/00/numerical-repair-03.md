# Broader numerical qualification and timestep refinement

## Scope and outcome

The [second repair](/docs/project/development/milestones/00/numerical-repair-02.md) established small
stability fixtures. This work adds longer bounded runs, lateral
and spreading flows, and a controlled timestep-refinement path through `maelstrom`.
The [numerical contract](/docs/project/development/milestones/00/phases/phase-00-design-contract.md)
owns the changed correction equation and operating bounds. The revised reference is `defaults-v4`:
eight full Jacobi corrections with `relaxation_scale = 20.0` (nominally `2000 m⁻²`).

Evidence applies to the uncommitted Maelstrom working tree over
`a126ac215ca51384f330b3c4f3357b5c148b89ce`, with EPQ based on
`40b1703e5f3f8c99ae67174a8040c8fa2734ce35`. Working-file links below are not immutable checkpoints.
No commits, pushes, tags or gitlink changes were made.

## Defect and correction

Reducing the timestep alone left the same positional correction divided by a smaller time during
velocity reconstruction. For the 64-particle block over three simulated seconds, changing `1/120 s`
to `1/480 s` raised peak recorded speed from `3.06` to `8.17 m/s` and changed settled mean height
from `0.01959` to `0.06557 m`. This exposed a real sensitivity hidden by energy budgets that grew
as inverse timestep squared.

An initial control scaled relaxation and artificial pressure separately. It improved the final shape
but failed the strict energy check because the whole multiplier denominator was not scaled. The
implemented [correction scale](/Maelstrom/src/fluid.rs) instead multiplies each complete Jacobi
correction. `--refine-timestep N` divides timestep by `N` and this scale by `N²`, after ordinary
overrides. Relaxation, artificial pressure, precision, support membership, configured fixed iteration count and plane
ordering retain their meanings. This is an explicit project variant, not adaptive timestep selection.
The PBF paper itself identifies timestep dependence in its empirical artificial-pressure term; it
does not prescribe this refinement law.<sup><a href="#ref-s004">S004</a></sup>

The resolved timestep and scale are recorded with provenance and comparison identity. The recipe is
not replayed. Unit scale skips the extra multiplication and retains the historical comparison key;
old records imply unit scale when the field is absent. Non-unit records require a supporting build.
No earlier default file or saved result was rewritten.

The 8,000-particle impact holdout then exposed insufficient solver convergence: four passes
left a minimum separation of `0.00158 m` at step 60. Refinement alone preserved separation
but exceeded the compression guard. Eight full passes with the previous relaxation passed that impact case but exceeded
the unchanged small-case motion budget. Eight half corrections passed the small guards but
produced coincident particles during the large impact. Eight full corrections with relaxation
scale 20 pass both; `defaults-v4` selects that common scheme for every bundled scene. The solver now honours
its configured count from 1–64; result identity includes the count, and four-pass replay
retains its historical backend identity. Historical arithmetic fixtures explicitly retain
their earlier work counts and correction scale; their assertions were not loosened.

## Verification approach

The [Rust stability suite](/Maelstrom/tests/fluid_stability.rs) retains the reference-only energy
guards and adds lateral wall contact, spreading, an independent refined-step position/velocity oracle,
and matched-time shape convergence. Every small dynamic step is checked. The original timestep-only
negative control still fails even the extended refinement allowance.

The refinement screen includes independently calculated initial scalar soft-constraint energy
`U₀ = mean(C²) × correction_scale / (2 × epsilon × dt²)` alongside the fixed reference-displacement
budget. This allowance stays constant under matched refinement. It accounts for initial constraint
work omitted by a purely kinetic budget, but is not an exact pressure potential or conservation law:
the gradients are substituted and artificial pressure is empirical. The original reference-only
regressions were not loosened. A compressed initial spreading trial exceeded that reference-only
screen; the qualified spreading fixture starts at nominal spacing, while compression remains a
separate stage study. Compressed dynamic releases are outside this envelope.

For an explicit refined run:

```sh
maelstrom run falling-block-04 --duration 3 --refine-timestep 2 \
  --checkpoints 0,240,720 --format json --output refined.json
```

## Local evidence

Checks ran on 14 October 2026 in WSL2 Ubuntu 24.04.5, Rust/Cargo 1.98.1, using locked/offline
Cargo verification. Both debug and release suites passed 148 integration tests, three unit tests and
two doctests per profile. Formatting, all-target checking, strict Clippy and Rustdoc passed.

The final 12-case release qualification passed with no audit failures. Full results and hashes are
retained locally in `/tmp/maelstrom-qualification-convergence/report.json`; the report also records
executable SHA-256 `529d75b48dc002ded8ab1ec213e4d42979fc34a08d519c5f30b31c29a0670099`.
These temporary files are local evidence, not a durable repository checkpoint.
The installed `~/.local/bin/maelstrom` has the same executable hash. Outside the checkout, the
1,000-particle one-second command completed all 120 steps with 37 CFL warnings; a refined run
replayed byte for byte. Both pre-existing saved results replayed as identical complete JSON
documents, and their original files were unchanged.

| Checked workload | Simulated duration | Observed result |
| --- | --- | --- |
| 64-, 216- and 1,000-particle blocks | 10 s each | Separation, compression, energy and final settling passed |
| 512-particle block | 1 s | Checkpoint guards passed |
| 1,728- and 8,000-particle blocks | 0.5 s each | Impact checkpoint guards passed |
| 4,096-particle block | 0.4 s | Impact checkpoint guards passed |
| 64-particle matched-time study, factors 1, 2 and 4 | 3 s each | Energy and shape convergence passed |
| 64-particle lateral and spreading flows | 3 s each | Wall/floor contact and settling guards passed |

The largest block's minimum checked separation was `0.03228 m`, above the `0.025 m` guard;
maximum checked compression was `30.04%`, below `35%`. Settled shape changes in the refinement
study decreased from `1.278 mm` to `0.264 mm`. Several unrefined cases still reported CFL
warnings; accepted completion with these guards does not establish a warning-free canonical baseline.
Refinement factors 2 and 4 in the small study reported no CFL warnings.

## Limits and stopping point

Qualification is local and bounded. It does not freeze a golden result or qualify all configurations,
all initial states, factors above four, other platforms or performance. Static-plane density deficiency
and empirical artificial pressure remain limitations. The 8,000-particle ten-second request remains
outside the verified duration envelope. No Gate G05 or durable completion checkpoint is claimed.

## References used

- <a name="ref-s004"></a> **S004** — Macklin and Müller, *Position Based Fluids* (2013).
  [Research source record](/docs/research/sources/004-macklin-muller-position-based-fluids.md).
