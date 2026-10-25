# Milestone 05 Completion Plan

## Entry condition

The [pre-evaluation review](/docs/project/development/pre-evaluation-review.md) identified usability
and performance concerns after this plan was prepared. Complete the
[usability revision](/docs/project/development/usability-plan.md), then follow the
[performance investigation plan](/docs/project/development/performance-plan.md) before final
measurement and synthesis. This evaluation plan does not authorise that implementation work;
existing start tags retain the original planning point.

## Purpose and starting point

Answer the [research question](/docs/project/definition.md): to what extent do uniform-grid spatial
partitioning, CPU multithreading and CUDA acceleration improve the performance and scalability of
the 3D Position-Based Fluids simulator? Distinguish demonstrated gains, small-workload costs and
practical limits from explanations that the measurements cannot establish.

Work follows the completed application milestone, retained by `milestone-04/complete` in EPQ
`b861a3a5a07e8b227a4b15caea2c5d662460481c` and Maelstrom
[`a881145a373fe2a4c9a25b0ca10f3b89c2b1db9e`](https://github.com/Mahkrab/Maelstrom/tree/a881145a373fe2a4c9a25b0ca10f3b89c2b1db9e).
The [application evaluation and handoff](/docs/project/development/milestones/04/application-visualisation.md)
identifies the retained controls, historical campaigns and remaining evidence gap: whether those
campaigns support the final synthesis or a common-build four-way comparison is needed.

There are three phases: audit the evidence and decide the evaluation protocol, obtain and verify the
necessary comparisons, then synthesise the findings. Reuse the existing collection, qualification,
analysis and checkpoint infrastructure. This plan specifies outcomes, not a new tool architecture,
file layout or command checklist. Preparation does not mean that the audit or campaign has begun.

## Contracts and scope

The [numerical contract](/docs/project/development/milestones/00/phases/phase-00-design-contract.md),
[comparison policy](/docs/project/development/milestones/00/reference-verification.md) and
[measurement protocol](/docs/project/development/milestones/00/measurement-protocol.md) remain the
starting authorities. Preserve brute force, serial grid, threaded grid and CUDA as distinct controls.
Use the backend records to establish what was actually qualified and measured, not merely what the
latest executable supports.

These contracts are not permanent prohibitions on change. An evidence-led revision must explain its
reason, update the owning decision, identify affected inputs or semantics and requalify affected
comparisons under equivalent conditions. Keep old results and checkpoints identifiable; never silently
reinterpret historical evidence. This plan itself changes no numerical setting or acceptance limit.

Important new measurements belong on the PC reached through `ssh pc`. Retain source and binary
identities, device/toolchain context, commands, failures and raw samples. Laptop fallback results are
provisional and separate. Renderer, encoding and display costs cannot become solver costs by accident;
solver steps per second are not displayed frames per second.

This is an evaluation milestone, not an unrestricted optimisation campaign. New numerical models,
backend redesigns, rendering features and unsupported physical-accuracy claims are outside scope.
Any repair genuinely required for trustworthy evaluation needs an explicit decision and renewed
verification. The final project document will summarise the development and evidence; these records
remain concise supporting material rather than fixed final chapters.

| Gate | Required outcome |
| --- | --- |
| G00 | Evidence coverage and comparability are audited, and a bounded evaluation protocol is decided before new collection |
| G01 | Required correctness and measurement evidence is independently checked, with reproducible comparisons and explicit missing or disqualified results |
| G02 | The research question is answered within the evidence, limitations and reproducibility boundaries, with a checkpointed final-evaluation handoff |

## Phase 0: audit evidence and decide the evaluation protocol

### Objective

Establish what can fairly be concluded from the retained campaigns and what, if anything, must still
be measured. Do not assume that a new campaign is necessary or that historical ratios are comparable.

### Work

- [ ] Map the research question to correctness, runtime, scaling, overhead and practical-limit claims.
      Identify the exact dataset and comparison needed to support each claim.
- [ ] Audit historical evidence and build a comparability matrix covering revisions, numerical inputs,
      timestep/iteration work, execution settings, device, build, timers, sampling and qualification.
      Separate hash retention from independent reconstruction of statistics and correctness results.
- [ ] Decide whether bounded reanalysis is sufficient or a fresh matched four-backend campaign is
      needed. Explain gaps and the value of any new collection rather than repeating old experiments
      automatically. Do not multiply speedups from different campaigns into an unmeasured result.
- [ ] Decide the exact workloads, controls, thread selections, correctness checks and timing boundaries.
      Start from the retained refined falling-block family and small lattice; justify any additions.
      A fixed twelve-worker control is not evidence of the best thread count at every particle count.
- [ ] Before collection, specify warm-ups, repetitions, execution order, resource/time limits,
      timeout and warning treatment, aggregation, variability and comparison formulae. Separate primary
      solver totals, construction/teardown, instrumented profiles and application costs.
- [ ] Record the bounded protocol, acceptance criteria and remaining threats to validity. Identify any
      required tooling change without introducing unnecessary infrastructure or starting measurement.

### Gate G00 evidence

Every intended conclusion has an identified evidence route. Reanalysis-only and new-collection choices
are justified, common conditions are explicit, and missing evidence cannot be mistaken for a pass.
Another agent can carry out the protocol without choosing the experiment after seeing its results.

## Phase 1: obtain and independently verify the comparison evidence

### Objective

Produce the evidence required by the decided protocol, using retained data wherever it is sufficient.

### Work

- [ ] Reconstruct historical summaries from raw samples and check input, correctness and provenance
      links. Retain disagreements and explain exclusions; do not overwrite the original campaigns.
- [ ] If collection is required, verify the exact common implementation and inputs before timing on
      the primary PC. Retain all controls, warm-ups, samples, profiles, failures and environment context.
      Record protocol deviations rather than silently changing workloads or retrying away failures.
- [ ] Independently verify numerical comparisons and calculate runtime, speedup, throughput, scaling
      and variability under the declared boundaries. Distinguish measured results from labelled models.
      Do not infer unmeasured memory behaviour or a particular substage bottleneck from aggregate time.
- [ ] Produce traceable comparison tables or figures that expose small-input overhead, incomplete work,
      warning-bearing runs and practical limits as well as successful gains. Check units, denominators
      and plotted values against raw data and preserve the analysis inputs.

### Gate G01 evidence

The required comparisons are reproducible and independently checked. Each result identifies its
controls, source, workload, device, timer and variability. Unavailable or disqualified evidence stays
visible and limits the claims; a successful collection command alone does not satisfy the gate.

## Phase 2: evaluate findings and prepare the final project synthesis

### Objective

Give a clear, bounded answer to the research question and make the evidence usable in the final report.

### Work

- [ ] Evaluate each optimisation and the complete backend comparison against the question. Explain
      where gains appear, where overhead dominates and how the observed scaling changes with size.
      Keep measured findings separate from algorithmic expectations and causal hypotheses.
- [ ] Assess internal and external validity: unequal historical builds, repetition count, execution
      order, shared-host load, thermal/scheduling uncertainty, one primary device and scene-family
      coverage. Explain what correctness agreement establishes and what physical validity remains untested.
- [ ] Connect the application outcome to the project objective without turning solver timing into
      interactive-performance evidence. Identify genuine future work without implementing it here.
- [ ] Prepare a concise final-evaluation record and an evidence map for the final project document.
      Trace substantive claims to exact datasets, methods and source checkpoints; preserve negative results.
- [ ] When separately authorised, checkpoint Maelstrom first if changed, then EPQ's exact gitlink and
      evidence, and establish the local completion tags. Treat remote publication as a separate action.

### Gate G02 evidence

The evaluation answers the research question without exceeding its measurements. Its tables, figures,
limitations and interpretation are traceable and reproducible. The handoff supports the eventual
project synthesis; it does not claim that the final submitted document has already been written.

## Records and checkpoints

Keep the full phase sequence here and add a concise phase record only when that work begins. Follow
the existing template, source conventions and applicable `AGENTS.md`; individual records name only
their current phase and gate. Keep simulator source and public documentation phase-agnostic.

Use `milestone/05-comparative-evaluation` integration branches and the established temporary phase
branches and annotated tags in both histories. Local start checkpoints identify committed inputs,
not completed research or hosted verification. No evaluation gate is satisfied by this plan alone.
