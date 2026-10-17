# Milestone 01 Completion Plan

## Purpose and starting point

Replace brute-force neighbour discovery with a serial CPU uniform grid, then establish whether it
improves the performance and scalability of the same simulation. The existing application, input
formats, CLI, diagnostics, verification and measurement tooling are already available; this milestone
extends them rather than repeating their development.

The `milestone-01/start` checkpoints identify EPQ
`2f5ad7a63a2960dd71a4367cfb77c3b33c39002c` and Maelstrom
[`2d05b4b9c35e7679156bf29fd34535ca35e9dd26`](https://github.com/Mahkrab/Maelstrom/tree/2d05b4b9c35e7679156bf29fd34535ca35e9dd26).
The [completed reference and handoff](/docs/project/development/milestones/00/serial-brute-force.md)
provide the starting behaviour and its accepted limitations. No grid implementation or milestone
completion is implied by this plan.

There are three phases: implementation and verification, measurement, then evaluation and handoff.
Agents should follow the applicable `AGENTS.md` instructions and choose suitable internal designs.
This plan defines outcomes and evidence, not a prescribed file layout, dependency list or command sequence.

## Contracts can evolve

The inherited [numerical contract](/docs/project/development/milestones/00/phases/phase-00-design-contract.md),
[comparison policy](/docs/project/development/milestones/00/reference-verification.md) and
[measurement protocol](/docs/project/development/milestones/00/measurement-protocol.md) are the current
working basis. Preserving them makes it possible to attribute a measured difference to neighbour search.
They are not permanent restrictions on improving the project. “Frozen” means identifiable and stable
for a particular experiment, not that a decision can never be reconsidered.

If a defect, new evidence or a better justified method requires a revision:

- Explain the reason and update the document that owns the affected decision.
- Identify the changed numerical behaviour, inputs, interface, comparison rule or measurement policy.
  Version the affected contract or experiment where existing results would otherwise be reinterpreted.
- Check both brute-force and grid execution against the revised common basis. Regenerate affected
  reference outputs and rerun affected measurements before making a new comparative claim.
- Keep earlier source checkpoints, inputs and results identifiable. State which findings are superseded
  or no longer directly comparable; never silently overwrite their meaning or move published tags.

A shared numerical repair is not a grid speedup. A change of hardware, workload, solver work or timing
boundary is not evidence of a search improvement by itself. Revisions can be handled within the current
phase without adding another phase merely to accommodate them, but correctness and comparability still
need evidence. This plan does not itself change any existing numerical values or measurement settings.

At the end of the project, the code, data, decisions and milestone findings will be synthesised into
one final document. These development records are a concise evidence trail for that document, not
untouchable final chapters. They should retain enough provenance to explain how and why the project
changed without duplicating every implementation detail.

## Scope and completion gates

Keep brute force available as a reference and introduce the grid through the smallest useful replaceable
search boundary. Reuse the existing solver, input resolution, run workflow, output safety and measurements.
Both searches must be exercisable through the public application with explicit execution identity.
Backend selection must not change physical configuration identity or introduce EPQ-specific scene roles
into the numerical library.

This milestone does not implement multithreading, CUDA, rendering or a general application redesign.
Small supporting changes are appropriate where the real grid implementation needs them. Unrelated
numerical tuning or infrastructure expansion is not part of the search optimisation.

| Gate | Required outcome |
| --- | --- |
| G00 | The serial grid is implemented, integrated and independently verified against the agreed contract |
| G01 | Correctness-qualified, same-device measurements support an honest brute-force/grid comparison |
| G02 | The requirements, results, limitations and multithreading handoff are evaluated and checkpointed |

Gate labels belong to this milestone. A phase is not complete merely because its files exist, its tests
compile or its implementation appears faster. There is no requirement to produce a speedup at every size.

## Phase 0: implement and verify serial uniform-grid discovery

### Objective

Make the grid a usable alternative to brute-force search while preserving the agreed simulation behaviour.

### Work

- [x] Review the inherited contracts and existing search call sites. Record the grid's responsibilities
      and any contract issue that needs resolving before implementation.
- [x] Decide cell width, position-to-cell mapping, storage and candidate traversal from the supported
      coordinate and support-radius domains. Explain how the searched cells cover every possible neighbour.
- [x] Define deterministic behaviour for negative coordinates, cell faces/edges/corners, sparse space,
      dense cells, coincident particles, empty input and extreme representable values.
- [x] Implement checked indexing and resource handling. Invalid or unrepresentable operations must fail
      clearly, without overflow, lost particles, uncontrolled allocation or partial accepted state.
- [x] Build search membership from the complete prediction snapshot once per timestep. Retain the existing
      within-step membership and current-distance rules rather than rebuilding during Jacobi iterations.
- [x] Produce exactly the same strict-support neighbour sets, self exclusion, duplicate prevention and
      ascending particle-identity order as brute force. Cell or container iteration must not change reductions.
- [x] Integrate explicit backend selection into the existing workflow, CLI, replay and result metadata.
      Retain existing brute-force use and historical replay behaviour; do not duplicate timestep orchestration.
- [x] Keep correctness audits independent of grid-owned membership. Grid and reference runs must own their
      state separately, including during cancellation and failure.
- [x] Test cell mapping and candidate coverage with independently derived small cases, then compare complete
      neighbour rows against brute force across deterministic generated and adversarial inputs.
- [x] Exercise unsupported/invalid inputs, exact support boundaries, cell crossings, repeated construction
      and next-step rebuilding. Include cases that would expose a missed adjacent cell or changed ordering.
- [x] Compare complete simulation outputs, checkpoints, CFL outcomes, failure handling and accepted-state
      preservation using the existing small fixtures and goldens. Cover both ordinary and measured execution.
- [x] For the current serial contract, require exact numerical agreement, including signed zero, after
      accounting only for intentional backend/build/timing metadata differences. Do not borrow parallel
      tolerances to excuse a serial ordering defect.

### Gate G00 evidence

The public application can select either search and reproduce equivalent physical inputs. Independent
geometry cases and brute-force comparisons establish membership correctness; full-run tests establish
that the grid has not changed the timestep, diagnostics or failure semantics. Record actual verification,
important implementation decisions and remaining limitations before performance claims begin.

G00 is satisfied locally as recorded in the [implementation and verification record](/docs/project/development/milestones/01/phases/phase-00-serial-uniform-grid.md). The grid and supporting tests remain unstaged; no completion checkpoint or PC performance comparison is implied. The retained exact CLI comparison is linked from that record.

## Phase 1: measure and compare on the primary PC

### Objective

Measure the effect of replacing discovery, including its overhead, without changing the experiment to
favour either implementation.

### Work

- [ ] Confirm that the candidate passes the correctness gate and that the selected source revisions,
      inputs, comparison policy and measurement protocol are identifiable before collection.
- [ ] Extend the existing collector only as needed to select and identify both backends. Include grid
      construction, clearing/rebuilding, candidate enumeration and neighbour ordering in the appropriate
      search and total timings; do not move grid setup outside the measured timestep to hide its cost.
- [ ] Use the primary PC through `ssh pc` for the important campaign. Verify its checkout and toolchain,
      build optimised binaries consistently, and record the environment and controls actually applied.
- [ ] Begin with the existing seven-size family, 480-step requests and checkpoint sequence. Keep the
      agreed warm-up, primary-sample, separate-profile and timeout policies common to both searches.
- [ ] Retain the current [PC baseline](/docs/project/development/milestones/00/assets/performance-baseline-pc-v1/README.md).
      Review its compatibility and collect paired brute-force controls on the same PC rather than relying
      only on an older campaign under potentially different load or build conditions.
- [ ] Check exact numerical agreement before accepting timings. Retain warnings, failed attempts, timeouts
      and incomplete sizes visibly; none may become a clean completed sample.
- [ ] Report raw timings, spread, throughput, search cost, total-step cost and speedup or slowdown at each
      shared size. Keep stage-profile overhead separate from primary samples and identify the crossover,
      if one is observed, rather than assuming the grid helps the smallest scenes.
- [ ] Investigate measured bottlenecks and any useful neutral optimisation. Retain before/after evidence
      for material changes and repeat correctness checks; do not optimise merely to produce a positive result.
- [ ] If larger workloads are practical, label them as an additional series with explicit inputs and policy.
      A grid-only completed size can demonstrate reach, but cannot supply a speedup ratio against an absent
      or incomplete brute-force result.
- [ ] If the PC is unreachable, continue ordinary verification or clearly provisional local exploration.
      Do not mix devices or replace the primary comparison with laptop timings without an explicit revision.

### Gate G01 evidence

Retained raw results, correctness checks and independently checked summaries support a reproducible
same-device comparison. The timing boundaries include all required search work, and the observations
separate algorithmic benefit from changed settings, noise, profiling overhead and incomplete workloads.
An unfavourable or mixed performance result is still a valid outcome when supported by evidence.

## Phase 2: evaluate, document and hand off

### Objective

Explain what the grid changed, what the evidence supports and what the multithreaded implementation must inherit.

### Work

- [ ] Record the main design decisions, diagnosed defects and any revisions to inherited contracts without
      rewriting the original reference as though those changes had always been present.
- [ ] Assess search correctness, deterministic simulation equivalence, public usability and measured
      performance individually. Link each judgement to implementation, tests or retained results.
- [ ] Explain results across particle counts, the observed crossover and bottlenecks, and the practical
      tested range. Do not equate faster execution with improved physical fluid accuracy.
- [ ] Evaluate limitations such as occupancy, clustering, sparse domains, ordering cost, retained storage
      and measurement variability where the implementation or evidence makes them relevant. Do not claim
      measured memory use unless it was actually measured under a declared method.
- [ ] Update the supported backend, replay and usage documentation and any affected project records.
      Keep the milestone summary concise enough to feed the final project document.
- [ ] State the next objective: parallelise the established grid-based execution without silently changing
      inputs, solver work, acceptance, diagnostics or the agreed comparison and measurement policies.
- [ ] Preserve the serial grid and brute-force reference, reusable fixtures, exact outputs, tolerance
      policies and datasets so later work can be assessed without inventing a new experiment.
- [ ] When separately authorised, complete the implementation-first EPQ/Maelstrom checkpoint sequence,
      pin evidence to full revisions and publish the milestone completion boundary.

### Gate G02 evidence

The milestone record contains an evidence-backed conclusion, accepted limitations and a concrete
multithreading handoff. Another agent can identify the current contracts and reproduce the comparison.
The final checkpoint retains the assessed code, tests, documentation and exact parent/submodule pairing;
it does not imply that the wider project or final comparative evaluation is complete.

## Working records and checkpoints

Keep the full phase sequence in this plan. Add concise records as work actually begins; implementation
records describe only their current phase and gate. Reuse the established record style and source/evidence
conventions rather than copying code or creating another layer of planning documents.

Use the existing milestone integration branches and the authorised phase/checkpoint workflow. Creating
this plan does not authorise commits, tags, pushes, branch changes or gitlink updates. A useful local test
result, a committed implementation, a published checkpoint and a completed PC campaign are distinct evidence.
