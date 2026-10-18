# Milestone 02 Completion Plan

## Purpose and starting point

Parallelise the uniform-grid simulation on the CPU, then measure whether distributing its work
improves performance over the serial grid. Reuse the existing application, scenes, CLI, diagnostics,
verification and measurement tools rather than developing that infrastructure again.

The local `milestone-02/start` checkpoints identify EPQ
`b98287c775c258c9215ee18772d94c23cfd0122d` and Maelstrom
[`2156bdca7f6702cea18030a8b0c603dfa393e036`](https://github.com/Mahkrab/Maelstrom/tree/2156bdca7f6702cea18030a8b0c603dfa393e036).
The [uniform-grid evaluation and handoff](/docs/project/development/milestones/01/serial-uniform-grid.md)
owns the starting findings and limitations. Its PC profiles identify Jacobi work as the main remaining
solver cost at the largest measured size; they do not establish a threading speedup in advance.

There are three phases: implementation and verification, PC measurement, then evaluation and handoff.
Follow the applicable `AGENTS.md` instructions and choose the internal design from the actual workload.
This plan specifies outcomes and evidence, not a file layout, threading library or command sequence.

## Contracts and scope

The inherited [numerical contract](/docs/project/development/milestones/00/phases/phase-00-design-contract.md),
[comparison policy](/docs/project/development/milestones/00/reference-verification.md) and
[measurement protocol](/docs/project/development/milestones/00/measurement-protocol.md) provide the current
comparison basis. Retain brute force and the serial grid as independent controls. Introduce threaded
execution without replacing the numerical model, changing the comparison scene or concealing work.

These contracts can evolve. A frozen experiment has identifiable inputs and rules; it is not a ban
on fixing defects or making better-supported decisions. A revision must explain its rationale, update
the owning contract and version affected semantics or experiments. Check all affected backends under
the revised common conditions, regenerate affected reference outputs and rerun affected measurements
before making a new comparison. Keep earlier checkpoints and results identifiable, including findings
that are superseded or no longer comparable. Never silently reinterpret an old result or move a
published tag. A common numerical repair is not a threading speedup.

The development records will feed one final project document. Keep them concise and traceable rather
than treating them as untouchable final chapters or duplicating source code. This plan does not change
any numerical value, tolerance or measurement setting by itself.

CUDA, rendering, distributed execution, new fluid models and a general application redesign are outside
this milestone. Supporting changes belong here only where threaded execution or its verification needs
them. Do not parallelise every operation merely to make the implementation appear complete.

| Gate | Required outcome |
| --- | --- |
| G00 | Threaded grid execution is usable, independently verified and preserves the agreed numerical and transactional contract |
| G01 | Correctness-qualified PC measurements establish scaling and comparison with fresh serial controls |
| G02 | The results, limitations and CUDA handoff are evaluated and retained in a reproducible completion checkpoint |

Gate labels belong to this milestone. Passing a gate requires evidence, not just types, files or a
successful run. A measured slowdown is an acceptable result; a speedup is not a completion requirement.

## Phase 0: implement and verify threaded CPU execution

### Objective

Make threaded uniform-grid execution a supported alternative while retaining one numerical contract,
independently owned simulation state and reliable failure behaviour.

### Work

- [x] Review the serial grid handoff, stage dependencies and measured bottlenecks. Decide which work
      to distribute and which to retain serially, with a reason for each important boundary.
- [x] Choose task granularity, scheduling, worker ownership and lifetime. Justify any dependency and
      avoid creating workers repeatedly where a reusable execution resource fits the actual workflow.
      Record whether any small-workload fallback runs serially; do not hide it in performance claims.
- [x] Define explicit thread-count selection, its default, valid domain and effective count. Decide
      how unavailable capacity, invalid values and incompatible backend options are reported. Keep
      execution settings separate from physical configuration and record enough information for replay.
- [x] Preserve immutable Jacobi inputs, complete-stage barriers, ordered per-particle plane projection
      and whole-step acceptance. Workers must not observe partially updated positions or multipliers.
- [x] Build membership from complete prediction once per timestep, retaining strict support, stable
      identities, duplicate/self exclusion and current-distance filtering. Parallel discovery must
      preserve the grid's rounded-arithmetic coverage and reference validation, not just real geometry.
- [x] Prefer distributing independent particle work while retaining each particle's reduction order.
      Require exact agreement where arithmetic is unchanged. Any changed reduction order must be
      explicit and qualified under the existing parallel policy, not excused by a blanket tolerance.
- [x] Keep cancellation and error collection coordinated. Failed or cancelled work must leave accepted
      state unchanged, workers must finish or stop safely, and retry must not inherit partial buffers.
      Preserve the contract's failure classification and error precedence rather than exposing whichever
      worker happens to report first. Do not call a caller-owned cancellation predicate concurrently.
- [x] Integrate selection into the library, public CLI, recorded execution identity and backend-preserving
      replay. Keep existing serial defaults and historical records working. Separate execution mode from
      discovery method where needed; do not force a threaded solver into a search-only abstraction.
- [x] Keep diagnostics independent of threaded membership and accepted snapshots read-only to observers.
      Record any shared-resource policy and avoid hidden global settings that let one run alter another.
- [x] Extend independent geometry, stage and full-run tests across one worker, several worker counts,
      uneven work partitions, empty input and fewer particles than workers. Exercise repeated runs,
      independent simultaneous solver instances where supported, and worker-resource lifecycle.
- [x] Cover dense/coincident and sparse inputs, negative/cell/support boundaries, extreme coordinates,
      invalid inputs, numerical failures, cancellation, rollback and retry. Use deliberate controls that
      expose missing barriers, stale buffers, lost work, changed ordering and nondeterministic errors.
- [x] Compare ordinary, measured, profiled and replayed results with both serial controls and retained
      goldens. Check every required component, checkpoint, audit, CFL outcome and completion classification.
      Preserve exact structural and membership obligations even where numerical budgets apply.
- [x] Establish repeatability for each supported execution setting and compare across tested worker
      counts. Record the actual guarantee and any permitted differences; a single successful run cannot
      establish independence from scheduling. Retain the policy's disagreement reports and worst cases.

### Gate G00 evidence

The application and library can select and replay threaded execution with explicit resource settings.
Independent tests establish stage isolation, coverage and transactional behaviour; complete comparisons
qualify numerical results under the declared policy. Serial controls still pass their exact checks.
Record implementation decisions, actual verification and limits before accepting comparative timings.

Local implementation and verification satisfy G00. The
[implementation record](/docs/project/development/milestones/02/phases/phase-00-threaded-cpu.md)
records the execution contract, exact comparison evidence and limits. Local annotated
`milestone-02/phase-00/complete` checkpoints retain the committed work and exact parent/submodule
pairing. Comparative PC measurements and remote publication remain separate.

## Phase 1: measure scaling and compare on the primary PC

### Objective

Separate the benefit of threading from grid search, changed arithmetic, different machines and hidden
setup costs. Establish which workloads and worker counts benefit, including overhead and saturation.

### Work

- [x] Identify the correctness-qualified source, inputs, policies and execution settings before collection.
      Extend the existing collector and reports only where thread-count selection, provenance or acceptance
      needs it; keep existing serial datasets and exact comparison behaviour reproducible.
- [x] Implement the declared parallel comparison policy where required. Compact snapshot hashes establish
      exact equality, not numerical tolerance: retain or independently compare the component-level evidence
      needed for every required observation. Do not accept unequal hashes without checking the underlying
      values, and do not drop exact identity, membership, warning or failure requirements.
- [x] Use the primary PC through `ssh pc`. Record toolchain, build flags, CPU topology visible to the
      process, available parallelism, affinity and controls actually applied. Select and record a practical
      worker-count sequence including one worker, intermediate counts and the intended default. Distinguish
      physical cores, logical processors and guest-visible capacity; do not infer unavailable host details.
- [x] Begin with the existing seven sizes through 8,000 particles, 480-step requests and checkpoint sequence.
      Keep matched numerical work, one warm-up, three primary samples, separate profiles and timeout/grace
      rules common to all execution settings. Record collection order and run campaigns sequentially without
      concurrent project checks; any deliberate protocol revision must precede the affected collection.
- [x] Collect fresh serial-grid controls using the same source, binary and PC conditions. Use these as the
      denominator for threading benefit. Retain a fresh brute-force series where claiming an overall gain
      from the original method; historical campaign ratios are context, not interchangeable denominators.
- [x] Include dispatch, barriers, required synchronisation, allocation, validation and repeated setup in
      the existing timestep boundary. Declare one-time worker-pool setup and teardown outside that boundary
      where applicable, and retain invocation wall time so solver gains are not whole-application claims.
- [x] Measure stage intervals as coordinated elapsed wall time, not the sum of overlapping worker clocks.
      Preserve stage partitioning and residuals, and keep extra profiling overhead out of primary ratios.
- [x] Qualify each execution setting before accepting timings. Retain raw attempts, warnings, failures,
      timeouts and partial runs; missing or incomplete controls cannot supply a speedup ratio.
- [x] Report time, spread, throughput, stage costs, speedup against the serial grid, and scaling relative
      to the same threaded implementation at one worker. Define any efficiency calculation and distinguish
      requested workers from effective capacity. Investigate overhead, crossover and saturation honestly.
- [x] Profile representative bottlenecks before tuning. Retain before/after evidence for useful neutral
      changes and repeat correctness checks; never remove validation or solver work to improve a result.
      Label any larger-size series separately, with no ratio against an absent serial result.
- [x] If the PC is unavailable, continue routine verification or explicitly provisional exploration locally.
      Do not pool devices or substitute laptop measurements for the primary comparison without a recorded
      revision. Make no memory-use claim without a declared measurement method and actual results.

### Gate G01 evidence

Raw PC results, component-level acceptance evidence where needed and independently checked summaries
support same-device comparisons and a worker-count scaling assessment. All required execution costs
are accounted for. Explain overhead and incomplete sizes as well as improvements; no universal speedup,
physical accuracy or statistical significance follows from three samples.

G01 is satisfied by the [primary-PC scaling record](/docs/project/development/milestones/02/phases/phase-01-performance-scaling.md)
and its retained raw campaign. All 245 benchmark attempts agree exactly; twelve workers achieve
the fastest observed 8,000-particle median, with a 2.988× gain against fresh serial-grid controls.
Small-input overhead, diminishing returns and the slower twenty-four-worker result remain visible.
No solver tuning, larger-size series or memory measurement is included. Local annotated
`milestone-02/phase-01/complete` checkpoints retain the campaign, collector and exact assessed
parent/submodule pairing; remote publication remains separate.

## Phase 2: evaluate, document and hand off

### Objective

Explain what threading achieved, what it cost and what the CUDA implementation must inherit.

### Work

- [ ] Assess numerical agreement, repeatability, transactional safety, public usability and performance
      separately. Link conclusions to exact implementation revisions, tests and retained results.
- [ ] Explain work distribution, barriers, reduction order, resource ownership and important diagnosed
      defects. Record any contract revisions without rewriting the serial history as though they always
      applied. Distinguish actual measurements from explanations inferred from profiles.
- [ ] Evaluate results across particle counts and workers, the useful tested range, overhead and saturation.
      Address relevant limits such as dense storage, load imbalance, shared-memory bandwidth, serial work,
      independent audit cost and host variability without claiming an unmeasured cause as established fact.
- [ ] Document supported execution options, defaults, effective worker counts, replay and failure behaviour.
      Keep the milestone summary concise and suitable for the final project synthesis.
- [ ] Define the CUDA handoff: preserve serial and threaded controls, fixtures, comparison reports, physical
      identities, stage snapshots, membership rules, diagnostics and atomic acceptance. Identify CPU-specific
      choices that need not become GPU requirements. Do not implement GPU infrastructure early.
- [ ] When separately authorised, complete the implementation-first checkpoint sequence in both repositories,
      pin the final Maelstrom commit through EPQ's gitlink and evidence, and create the annotated completion
      boundary. Treat remote publication as a separate authorised action.

### Gate G02 evidence

The evaluation states supported findings, accepted limits and a concrete CUDA handoff. Another agent
can identify the assessed source and settings, reproduce the verification and interpret the measurements.
The final checkpoint retains code, tests, documentation and the exact parent/submodule pairing; it does
not imply completion of the wider project or the final cross-backend evaluation.

## Records and checkpoints

Keep the full phase sequence here. Add concise implementation records only as each phase begins,
following the existing template and source/evidence conventions. A record names only its own phase
and gate; source, tests and public documentation describe enduring responsibilities instead.

Use `milestone/02-multithreaded-cpu` integration branches and the established temporary phase-branch
and annotated-tag conventions. This planning task does not authorise commits, branch changes, tags,
pushes or gitlink updates. Local verification, committed work, published checkpoints and completed
PC measurements remain distinct evidence.
