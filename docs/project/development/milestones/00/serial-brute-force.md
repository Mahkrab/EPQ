# Serial CPU brute-force reference: implementation and evaluation

## Milestone overview

Milestone 00 provides the deterministic, headless serial CPU reference for Maelstrom's optimisation
study. It accepts explicit configurations and scenes, advances three-dimensional Position-Based
Fluids (PBF), produces replayable observations and retains correctness and performance evidence.
The numerical implementation assessed here is Maelstrom
[`d8454231255133f732a682f83ecc14f83f256831`](https://github.com/Mahkrab/Maelstrom/tree/d8454231255133f732a682f83ecc14f83f256831),
which EPQ's gitlink currently pins. New usage documentation is a local working-tree addition;
source and test links below identify the assessed committed implementation.

**Local completion decision, 15 October 2026:** requirements M00-0 through M00-5 and gates G00
through G07 are satisfied for the scope and environment below. The evaluation and handoff are
complete locally. This is not a published milestone-completion checkpoint. The existing Phase 7
tags retain their original evidence; the PC campaign was added afterwards. Phase 8 and milestone
completion commits/tags remain pending separately authorised checkpointing in both repositories.

## Implementation and revisions

The phase records preserve intention, implementation, verification and the limits of each stage.
They should be read as a development history: early implementation success did not establish
fluid stability, benchmark readiness or the final numerical settings.

| Stage | Intention and completed outcome | Evidence and observation |
| --- | --- | --- |
| Numerical design | Make equations, units, ordering and acceptance explicit | [Design contract](/docs/project/development/milestones/00/phases/phase-00-design-contract.md); subsequent repairs are recorded within it, rather than presented as original decisions |
| Mathematical foundations | Verify kernels, density, Jacobi calculations, motion, planes and lattice-derived mass independently | [Foundation record](/docs/project/development/milestones/00/phases/phase-01-numerical-foundations.md); independent binary64 expectations prevent the production path becoming its own oracle |
| Inputs | Resolve strict, versioned TOML configurations and deterministic scenes | [Input record](/docs/project/development/milestones/00/phases/phase-02-configuration-scenes.md); provenance and display labels remain distinct from numerical equivalence |
| Serial simulation | Compose a complete transactional timestep with brute-force discovery | [Solver record](/docs/project/development/milestones/00/phases/phase-03-serial-brute-force.md); failures and cancellation preserve accepted state |
| Observations | Add immutable snapshots, fresh density audits, identities, replay and safe output | [Workflow record](/docs/project/development/milestones/00/phases/phase-04-diagnostics-results.md); this initially left public CLI usability open |
| Public application | Exercise real loading, execution and publication through a discoverable CLI | [CLI record](/docs/project/development/milestones/00/phases/phase-05-cli.md); ordinary runs exposed boundary and fluid-quality defects requiring explicit revisions |
| Reference qualification | Freeze a reviewed comparison family, exact goldens and comparison budgets | [Verification record](/docs/project/development/milestones/00/phases/phase-06-reference-verification.md); numerical health is checked independently of replay agreement |
| Measurement | Instrument the existing solver body and retain controlled raw samples | [Baseline record](/docs/project/development/milestones/00/phases/phase-07-performance-baseline.md); PC and laptop results remain separate |
| Evaluation and handoff | Consolidate requirements, limitations, interface documentation and inherited contracts | [Evaluation record](/docs/project/development/milestones/00/phases/phase-08-evaluation-handoff.md); no later search or execution backend was needed |

Three material revisions qualify the initial design. Axis-aligned projection could round outside
the strict permitted half-space or lose contact through cancellation; direct assignment of its
constrained coordinate repaired this arithmetic and advanced the backend contract to `v2`.
The [first regularisation repair](/docs/project/development/milestones/00/numerical-repair-01.md)
then showed that the original relaxation allowed catastrophic sparse-neighbour corrections.
The [second repair](/docs/project/development/milestones/00/numerical-repair-02.md) found pair crossing
and excessive energy even after collapse was reduced; density error alone was an inadequate screen.
The [broader qualification](/docs/project/development/milestones/00/numerical-repair-03.md) exposed
timestep sensitivity and insufficient convergence in the large impact holdout. The final common
configuration uses eight full iterations and relaxation scale 20. Explicit matched refinement
scales both timestep and the complete correction response. Earlier configuration files and replay
identities are retained, not relabelled as the final reference.

## Final architecture and supported behaviour

The [library](https://github.com/Mahkrab/Maelstrom/blob/d8454231255133f732a682f83ecc14f83f256831/src/lib.rs)
separates checked numerical operations from input resolution, accepted-state ownership and
application observation. This is the implemented structure, not evidence that every original
design choice survived unchanged.

| Responsibility | Implemented boundary |
| --- | --- |
| Input resolution | `config` derives validated quantities and provenance; `scene` constructs ordered particles and planes without advancing state |
| Numerical operations | `math`, `kernel`, `fluid`, `integration`, `boundary` and `reference` implement shared arithmetic without CLI or output dependencies |
| Neighbour discovery | [`neighbours`](https://github.com/Mahkrab/Maelstrom/blob/d8454231255133f732a682f83ecc14f83f256831/src/neighbours.rs) builds duplicate-free interactions by strict support distance in stable identity order |
| State transaction | [`SerialSimulation`](https://github.com/Mahkrab/Maelstrom/blob/d8454231255133f732a682f83ecc14f83f256831/src/simulation/mod.rs) owns accepted particles; complete predictions and Jacobi stages use separate working storage before atomic acceptance |
| Observation and reproduction | [`workflow`](https://github.com/Mahkrab/Maelstrom/blob/d8454231255133f732a682f83ecc14f83f256831/src/workflow/mod.rs) retains CFL outcomes, copies accepted snapshots, performs fresh audits and records replay inputs |
| Process interface | [`cli`](https://github.com/Mahkrab/Maelstrom/blob/d8454231255133f732a682f83ecc14f83f256831/src/cli/mod.rs) resolves arguments, handles interruption and presents results outside solver timing |

A step validates input, applies acceleration and the warning-only CFL check, predicts all positions,
builds membership once, performs the configured complete Jacobi and ordered projection passes,
reconstructs velocity, checks finite state and half-spaces, then commits. Iterations recalculate
distances from their current snapshot but retain prediction-time membership. A newly approaching
particle enters only on the next timestep. Self contributes to density, never to interactions.
Cancellation and failure cannot install part of a candidate step.

The [usage guide](/Maelstrom/docs/usage.md) documents discovery, validation, effective inspection,
named/external execution, limits, checkpoints, replay, publication, JSON interpretation and exit
codes. The [input specification](/Maelstrom/docs/inputs.md) covers all configuration fields, units,
defaults, validation, scene construction and schema compatibility. These are live documentation
links, not immutable implementation evidence. TOML schema 1 and result/snapshot schema 1 are
distinct representations: recorded particle identities and counters use decimal strings, and full
result inputs suffice for replay after source files disappear. Warnings and incomplete outcomes
remain visible; an exit-zero warning-bearing run is not a clean baseline sample.

## Verification and retained baseline

The final local review used Rust/Cargo 1.98.1 and Python 3.12.3 on x86_64 WSL2 Ubuntu 24.04.5.
The [evaluation record](/docs/project/development/milestones/00/phases/phase-08-evaluation-handoff.md)
records the fresh checks. Each debug/release suite passed 159 integration tests, three unit tests
and two separately run doctests. Formatting, all-target checking, strict Clippy and Rustdoc passed;
15 parent tooling/Markdown tests and the milestone asset check passed. Documented CLI journeys,
input examples, reference replay, local links and retained-data provenance were checked separately.
These are local checks; no new hosted CI, browser, native Windows/macOS or cross-platform replay
result is claimed.

Verification is layered. Analytical and independent binary64 calculations check primitive quantities
and complete transitions. Focused tests check membership, snapshot ordering, plane behaviour,
empty/coincident inputs, non-finite failure, cancellation and rollback. The
[`reference_verification` suite](https://github.com/Mahkrab/Maelstrom/blob/d8454231255133f732a682f83ecc14f83f256831/tests/reference_verification.rs)
checks fixture hashes and every golden value, including signed zero and intermediate checkpoints;
the falling trajectory also has independent every-step density, separation, compression, energy
and CFL checks. The independent binary64 solver is compared per transition from the same accepted
input: accumulated cross-precision trajectory equality is not a valid oracle.

`falling-block-refined-v1` fixes `defaults-v4`, factor-four refinement, eight iterations, 480 steps
and checkpoints 0, 1, 120, 240 and 480. Its seven sizes are 64, 216, 512, 1,000, 1,728, 4,096 and
8,000 particles. The 64-particle golden and separate 27-particle unforced-lattice golden are frozen
by the [manifest](https://github.com/Mahkrab/Maelstrom/blob/d8454231255133f732a682f83ecc14f83f256831/reference/manifest.json).
The [comparison policy](/docs/project/development/milestones/00/reference-verification.md) owns exact
serial acceptance and the separate future parallel budgets.

The primary [PC report](/docs/project/development/milestones/00/assets/performance-baseline-pc-v1/report.md)
and [raw index](/docs/project/development/milestones/00/assets/performance-baseline-pc-v1/dataset.json)
retain the AMD Ryzen 9 7900X campaign under `serial-baseline-v1`: one warm-up, three total-only
samples and one separate profile per size. All 35 requests completed without warnings or timeouts.
Median 480-step totals were 0.253382 s at 64 particles, 33.599465 s at 4,096 and 86.410862 s at
8,000. At the largest size the three totals ranged from 85.730299 to 92.501003 s, with sample
standard deviation 3.728168 s. The largest tested member completed the policy; no larger limit was
established. Neighbour discovery rose from 2.99% to 48.54% of instrumented time, while Jacobi
remained the largest stage. These profiles contain clock overhead and are not primary samples.

At the golden's final checkpoint, mean/maximum absolute relative density errors were
0.09173302/0.20032573; minimum separation was 0.04117983 m, with floor contact and no CFL warnings.
Those observations qualify this request, not arbitrary flows. Earlier laptop timeouts at 8,000
describe that device and budget; they do not establish the PC's limit. The campaigns are never
pooled. This review regenerated the PC report and verified retained hashes/statistics without
running a new performance campaign.

## Requirement evaluation

The [design contract](/docs/project/development/milestones/00/phases/phase-00-design-contract.md#requirements-and-success-criteria)
owns the six requirements. “Met” below refers to their declared milestone scope, not physical
validation of arbitrary fluids or completion of the whole project objective.

| Requirement | Assessment | Evidence and practical limit |
| --- | --- | --- |
| M00-0: complete single-threaded 3D PBF simulation | Met | Transactional solver and [`serial_simulation`](https://github.com/Mahkrab/Maelstrom/blob/d8454231255133f732a682f83ecc14f83f256831/tests/serial_simulation.rs), stability and reference suites exercise complete multi-step runs; only the documented numerical envelope is qualified |
| M00-1: brute-force reference neighbour search | Met | Direct all-pairs discovery and [`serial_simulation`](https://github.com/Mahkrab/Maelstrom/blob/d8454231255133f732a682f83ecc14f83f256831/tests/serial_simulation.rs) establish strict support, ordering, duplicates, self treatment and non-finite rejection |
| M00-2: deterministic identical inputs | Met | Exact repeat/replay tests check the complete supported serial output, including intermediate states and signed zero; no cross-platform bitwise guarantee |
| M00-3: core independent of rendering, threading and CUDA | Met | Library dependency inspection and all headless tests run without display variables; the process signal handler is outside numerical execution |
| M00-4: reusable correctness and performance baselines | Met | Hashed goldens, independent health checks, PC raw samples and reproducible summaries under frozen policies; no later-backend speedup or memory claim yet |
| M00-5: stable numerical configuration for later tests | Met | Versioned defaults, scene family, manifest, resolved identities and explicit refinement fix the comparison experiment; historical settings remain separately identifiable |

## Evaluation and limitations

The strongest outcome is an inspectable reference with explicit boundaries: independently checked
numerical operations, transactional state, reproducible inputs and retained negative controls.
The failures found through the CLI and larger workloads improved the reference before goldens and
timings were frozen. Exact repeatability establishes numerical consistency with this contract; a
golden alone could still preserve a defect, which is why independent equations and health guards
remain necessary.

Visual plausibility has not been assessed by rendering. Contact, spreading, settling and bounded
health metrics provide numerical observations, not a substitute visual judgement. Engineering
computational fluid dynamics (CFD) accuracy has not been demonstrated: there is no comparison with
physical experiments or an independently validated continuum solution. The relationship to the
governing equations and source-backed modelling choices is explained in the
[design basis](/docs/project/development/milestones/00/phases/phase-00-design-contract.md#relationship-to-the-navier-stokes-equations).
No new external physical-accuracy claim is made here.

Static planes project centres without supplying boundary density, friction or restitution. Free
surfaces and walls retain density deficiency; the final absolute density errors therefore cannot
be interpreted purely as excess compression. Artificial pressure, relaxation and matched correction
refinement are empirical project choices. Fixed neighbour membership can omit newly approaching
particles within a step. Eight iterations are fixed work, not a convergence guarantee. Factors
above four, compressed dynamic releases, arbitrary geometry/configurations and the 8,000-particle
ten-second run remain outside the retained qualification envelope. A valid input or accepted step
does not extend it.

Brute-force discovery is quadratic and stores interaction lists; in dense support its storage can
also grow quadratically. Checkpoint copies and diagnostics accumulate in memory, and frequent fresh
audits can substantially increase invocation time despite being excluded from solver totals. No
peak-memory measurement was made. The PC campaign has only three samples per size; shared
WSL/Windows load, scheduling, thermal conditions and uncontrolled frequency limit causal claims.
No statistical significance, universal hardware ceiling or cross-machine speedup follows.

These are accepted limitations of the retained reference, not repair tasks silently delegated to
uniform-grid work. A modelling or numerical change requires an explicit versioned experiment and
review of affected goldens and baselines. The temporary broader qualification files mentioned in
the repair record are historical local observations; durable tests and hashed reference/baseline
assets support this completion decision.

## Handoff to uniform-grid discovery

The next objective is to **replace only brute-force neighbour discovery with serial CPU uniform-grid
spatial partitioning while preserving the completed reference behaviour**. Keep the existing serial
reference available as the oracle. The neighbour functions are currently called directly by the
solver; no grid implementation or speculative backend framework is supplied by this milestone.
Introduce the narrow replaceable boundary when that real implementation needs it.

| Inherited contract | Frozen owner and obligation |
| --- | --- |
| Configuration, scenes and physical inputs | [Input specification](/Maelstrom/docs/inputs.md), assessed `config`/`scene` implementation and manifest hashes; preserve schema handling, precedence, resolved identity, particle and plane order |
| Numerical and timestep semantics | [Design contract](/docs/project/development/milestones/00/phases/phase-00-design-contract.md); binary32 equations, complete Jacobi snapshots, eight recorded passes, refinement, projection, CFL classification and atomic acceptance remain unchanged |
| Neighbour semantics | [Neighbour-set contract](/docs/project/development/milestones/00/phases/phase-00-design-contract.md#neighbour-set-contract); discover once from the complete prediction, strict distance less than h, self excluded, no duplicates, ascending identity and identical reductions; retain a fresh independent brute-force audit |
| Requests, outputs and failure behaviour | [Usage guide](/Maelstrom/docs/usage.md) and assessed `workflow`/CLI; retain replayable inputs, schema interpretation, statuses, warning history, cancellation/rollback and publication guarantees; identify the new backend explicitly |
| Fixtures and numerical acceptance | [Reference policy](/docs/project/development/milestones/00/reference-verification.md) and manifest; grid output must match serial numerical bits exactly, including signed zero; future parallel tolerances do not relax the grid requirement |
| Measurement and baseline | [Protocol](/docs/project/development/milestones/00/measurement-protocol.md) and primary PC dataset; preserve workloads, solver work, clocks, warm-up, sampling, budgets, raw retention and device; include grid construction in neighbour-search timing |

A grid candidate must establish membership agreement on focused edge cases and the frozen workloads,
then exact checkpoint/final-state and diagnostic agreement. Preserve original candidate results and
produce the policy's machine-readable and readable disagreement report before performance claims.
Missing checkpoints, failed outcomes and unavailable metrics are failures, not omitted comparisons.
Performance comparisons must run on the primary PC under the same policy and identify both source
revisions and environments. The present profile motivates testing a grid, but establishes no grid
speedup: grid construction overhead and the still-large Jacobi share limit what discovery alone
can improve, particularly for small inputs.

## Conclusion

This milestone establishes the controlled starting point for the research question. The extent of
benefit from spatial partitioning, CPU threading and CUDA remains to be measured by the later
implementations. The interactive application and offline rendering portions of the overall project
objective also remain outside this completed headless reference.

## Phases

- [Phase 0 design contract](/docs/project/development/milestones/00/phases/phase-00-design-contract.md)
- [Phase 1 numerical foundations](/docs/project/development/milestones/00/phases/phase-01-numerical-foundations.md)
- [Phase 2 scene configuration](/docs/project/development/milestones/00/phases/phase-02-configuration-scenes.md)
- [Phase 3 serial brute-force simulation](/docs/project/development/milestones/00/phases/phase-03-serial-brute-force.md)
- [Phase 4 diagnostics and results](/docs/project/development/milestones/00/phases/phase-04-diagnostics-results.md)
- [Phase 5 public CLI](/docs/project/development/milestones/00/phases/phase-05-cli.md)
- [Phase 6 reference verification](/docs/project/development/milestones/00/phases/phase-06-reference-verification.md)
- [Phase 7 performance baseline](/docs/project/development/milestones/00/phases/phase-07-performance-baseline.md)
- [Phase 8 evaluation and handoff](/docs/project/development/milestones/00/phases/phase-08-evaluation-handoff.md)

## Related records

- [Position-Based Fluids mathematics and behaviour](/docs/project/development/milestones/00/explanations/math.md)
- [Maelstrom development roadmap](/docs/project/plan.md)
- [Frozen serial reference and backend comparison](/docs/project/development/milestones/00/reference-verification.md)
- [Serial baseline measurement protocol](/docs/project/development/milestones/00/measurement-protocol.md)
- [Primary PC performance baseline](/docs/project/development/milestones/00/assets/performance-baseline-pc-v1/README.md)
