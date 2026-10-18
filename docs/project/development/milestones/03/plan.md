# Milestone 03 Completion Plan

## Purpose and starting point

Implement the uniform-grid simulation for a CUDA-capable GPU and compare it fairly with the existing
CPU implementations. Reuse the application, input contracts, CLI, diagnostics, fixtures and evidence
tools. The new work is device execution and its qualification, not another application framework.

The local `milestone-03/start` checkpoints identify EPQ
`3752255d22b76c4a117cd6bf74d7410d91d4fd22` and Maelstrom
[`60b9a767636428a26f39a1901e2cac4276c75c83`](https://github.com/Mahkrab/Maelstrom/tree/60b9a767636428a26f39a1901e2cac4276c75c83).
The [threaded CPU evaluation and CUDA handoff](/docs/project/development/milestones/02/threaded-cpu.md)
owns the inherited findings and limits. Keep brute force, serial grid and threaded grid available
as independently owned controls; none is replaced by introducing CUDA.

There are four phases: device integration, solver implementation and verification, PC measurement,
then evaluation and handoff. Separating the device boundary from the solver gives the new build and
resource lifecycle a useful checkpoint without repeating the infrastructure phases of Milestone 00.
Follow the applicable `AGENTS.md` instructions. Agents choose internal structure, libraries, storage
and launch design; this plan defines outcomes and evidence rather than prescribing files or commands.

## Contracts and scope

The [numerical contract](/docs/project/development/milestones/00/phases/phase-00-design-contract.md),
[comparison policy](/docs/project/development/milestones/00/reference-verification.md) and
[measurement protocol](/docs/project/development/milestones/00/measurement-protocol.md) are the current
comparison basis. Preserve physical identities, binary32 equations, configured work, stage snapshots,
strict support, ordered planes, diagnostics and atomic acceptance. CPU scheduling and host storage
are implementation choices, not requirements to reproduce on the GPU.

Contracts can evolve through evidence-led decisions. Frozen means stable and identifiable for an
experiment, not permanently unchangeable. Explain a proposed revision, update its owning contract
and version affected semantics or experiments. Qualify all affected backends under the revised common
conditions, regenerate affected reference outputs and rerun affected comparisons. Keep older code,
inputs and findings identifiable, including superseded results; never silently reinterpret them or
move published tags. A common numerical repair or altered workload is not a GPU acceleration result.

The existing parallel budgets are acceptance limits, not permission to change physics or an automatic
allowance for any GPU discrepancy. Require exact results where arithmetic is unchanged. Diagnose and
identify arithmetic differences explicitly before applying the appropriate quantity-specific policy;
do not relax limits to admit a failing implementation. Preserve exact structural obligations.

Development records will feed one final project document. Keep their decisions and provenance useful
and concise rather than duplicating code or treating their prose as untouchable final chapters.
This plan itself changes no numerical value, tolerance, workload or measurement setting.

Rendering, graphics interoperability, multi-GPU execution, distributed execution and new fluid models
are outside scope. The GPU backend must execute the uniform-grid discovery and iterative solver work;
a CPU simulation behind a CUDA option is not completion. Supporting host work is allowed where its
responsibility and cost are explicit. Do not build speculative renderer or multi-device abstractions.

| Gate | Required outcome |
| --- | --- |
| G00 | Reproducible optional CUDA integration with verified device/resource handling and unaffected CPU builds |
| G01 | A usable GPU solver passes independent numerical, geometry, workflow and failure qualification on hardware |
| G02 | Correctness-qualified primary-PC measurements compare completed GPU work with fresh CPU controls |
| G03 | Results, limitations and application-integration handoff are evaluated and retained in a completion checkpoint |

Gate labels belong to this milestone. A compiler success, smoke kernel or faster isolated kernel is
not a completed simulator. A slowdown is a valid finding; speedup is not a gate requirement.

## Phase 0: establish CUDA integration and resource ownership

### Objective

Make device execution reproducible and safe to own without coupling ordinary CPU use to CUDA.

### Work

- [x] Recheck the primary PC through `ssh pc`: device availability, driver/toolkit/compiler, supported
      target, memory and WSL environment. The [CUDA infrastructure record](/docs/project/infastructure/CUDA/README.md)
      is historical smoke-test evidence, not proof of the current environment or simulator readiness.
- [x] Decide the host/kernel interface and reproducible Cargo build path, using the recorded Rust-host
      and CUDA C++ approach as the starting design. Explain any justified alternative. Record dependencies,
      enabled capability, target and compiler flags; avoid undocumented local downloads or machine paths.
- [x] Keep CUDA optional. Ordinary CPU builds and tests must work without the toolkit or device. Define
      clear build-time and runtime errors for unavailable or incompatible CUDA, with no silent CPU fallback
      for an explicitly selected GPU run. Do not install drivers or alter the PC's system setup implicitly.
- [x] Define device selection, context and stream ownership, allocation lifetime, transfer layouts and
      synchronisation. Check sizes, alignment, indices and capacity at the Rust/native/device boundaries.
      Keep any unsafe or foreign-function interface small, documented and covered by a safe public boundary.
- [x] Establish typed error translation and cleanup for allocation, transfer, launch and completion failures.
      Separate immediate submission errors from failures found when work completes. Define which failures
      permit retry and which invalidate the device execution resource; never reuse unknown partial state.
- [x] Verify a small round trip from the real Rust application boundary, including independent expected
      values, repeated construction/destruction and meaningful rejection paths. Record actual hardware
      results separately from host-only tests and injected failures. Do not introduce the full solver yet.

### Gate G00 evidence

Another checkout can build CPU-only operation and the optional CUDA path using recorded prerequisites.
The real host/device boundary executes on the selected hardware with verified data layout, ownership
and failure handling. A missing GPU may leave useful host-only work, but cannot satisfy this gate.

The [implementation and verification record](/docs/project/development/milestones/03/phases/phase-00-cuda-integration.md)
records G00 passing on the primary PC for the assessed implementation, with retained evidence
and explicit diagnostic limits. Local annotated `milestone-03/phase-00/complete` checkpoints retain
the implementation and exact parent/submodule pairing. The record discloses the documentation-only
source-manifest difference. This is not a GPU solver qualification or remote publication.

## Phase 1: implement and independently verify the GPU solver

### Objective

Run the agreed timestep on the GPU while preserving observable numerical and transactional behaviour.

### Work

- [ ] Decide device data layout, persistent buffers, cell construction, neighbour storage, launch geometry
      and stage dependencies. Keep state resident where the workflow permits, but account for every
      required transfer. Explain important choices from concrete responsibilities rather than theoretical speed.
- [ ] Implement uniform-grid discovery with complete coverage of the supported rounded-arithmetic domain.
      Preserve negative/cell/support boundaries, overflow validation, strict membership, stable identity,
      self exclusion and duplicate prevention. Define ordering independently of concurrent insertion order.
- [ ] Handle dense occupancy and interaction capacity explicitly. No fixed cell/row limit may silently
      discard neighbours. Check count/offset arithmetic, allocation limits and failure paths before using
      buffers; resource failure must not publish truncated or partially accepted output.
- [ ] Implement acceleration and CFL checks, prediction, fixed membership, every configured Jacobi pass,
      ordered projection, velocity reconstruction and acceptance. Complete position and multiplier snapshots
      must precede dependent work; local block coordination alone must not stand in for a whole-stage barrier.
- [ ] Record floating-point choices, reduction order, contraction, denormal and device-math behaviour.
      Do not use unlabelled fast-math, altered support or approximate physics as a transparent optimisation.
      Preserve exact CPU controls and qualify every declared device arithmetic difference independently.
- [ ] Retain whole-step acceptance across host and device state. Define how snapshots expose the last
      accepted step and how cancellation, delayed device errors, device loss and retry are represented.
      Pending work must finish or be safely abandoned before its storage is reused or released. Preserve
      numerical error precedence/classification rather than reporting whichever thread wins a race.
- [ ] Integrate explicit GPU selection into the library, CLI, execution metadata and replay. Separate
      physical identity from device/build/launch settings. Keep historical CPU records working and reject
      incompatible worker or device options. Rendering must not determine solver correctness.
- [ ] Retain fresh independent density audits outside solver timing and independently owned CPU controls.
      Extend component comparison only where needed: compact hashes prove equality, not tolerance acceptance.
      Check every required component, checkpoint, audit, CFL value and status under the declared policy.
- [ ] Test kernels and complete stages against independent small geometry/equation cases and CPU oracles.
      Cover empty/single/coincident particles, dense/sparse distributions, negative and extreme coordinates,
      exact boundaries, uneven launches and fewer particles than execution lanes. Deliberate incorrect controls
      should expose missing barriers, ordering changes, lost neighbours and stale buffers.
- [ ] Exercise invalid requests, capacity/transfer/launch/completion failures, cancellation, rollback,
      retry and independent solver lifetimes. Use available device memory/race diagnostics and retain their
      observed results; injected failure tests do not establish recovery from actual hardware loss.
- [ ] Verify both complete goldens, repeated ordinary/measured/profiled execution and public replay on
      hardware. Check the larger family against fresh CPU controls and state the tested duration at each
      size. Test supported launch settings for repeatability and numerical sensitivity, with full disagreement
      reports and worst components. Passing means every required value passes, not just an average error.

### Gate G01 evidence

The public application executes and replays a complete CUDA simulation on hardware. Independent tests
qualify membership, stages, numerical acceptance, diagnostics and rollback, while CPU regression checks
still pass. Retained results name device, source, build flags, request and comparison policy. Unavailable
hardware tests and unsupported recovery paths remain explicit limits, not passes or silent skips.

## Phase 2: measure GPU performance on the primary PC

### Objective

Measure completed GPU solver work and its host costs under a declared comparison, not submission speed.

### Work

- [ ] Write the GPU measurement extension before collection. Retain the current seven sizes through
      8,000 particles, 480 steps, refinement, checkpoints, warm-up, three primary samples, separate profiles
      and timeout/grace rules unless an explicit evidence-led revision is agreed and recorded first.
- [ ] Define the primary completed-step elapsed boundary, including required transfers, validation,
      allocation, launch, synchronisation and atomic acceptance. Align CPU denominators with equivalent
      work. Account for work deferred beyond a return and any cross-step batching; do not omit completion
      or alter acceptance solely to improve timings. Keep invocation wall time separately.
- [ ] Declare one-time context, module/kernel compilation, device-buffer setup and teardown costs separately
      where outside solver timing. Report synchronised device-stage timings only as profiles, not substitutes
      for comparable solver totals. Overlapping work must not be double-counted or turned into fictitious stages.
- [ ] Run the important campaign through `ssh pc`. Record CPU and GPU identities, visible memory, driver,
      toolkit, target, build flags, launch settings and controls actually applied. Retain source/kernel/binary
      hashes and collection order. Do not run concurrent project checks on the measurement device.
- [ ] Collect fresh serial-grid and explicitly selected threaded-grid controls under matching conditions.
      Declare worker/launch settings before collection; do not select the most favourable result afterwards
      and present it as a fixed comparison. Retain brute-force controls if claiming original-method speedup.
      Historical ratios cannot supply current denominators or be multiplied into an overall speedup.
- [ ] Extend the existing collectors and acceptance reports without weakening serial exact checks.
      Qualify each required GPU observation against the appropriate CPU reference before admitting timings;
      retain component-level evidence where tolerances are used. Backend/build/device metadata are context,
      not permission to omit physical identity, warning, membership or failure checks.
- [ ] Preserve raw samples, spreads, throughput, profiles, invocation times, failed attempts and timeouts.
      Define cancellation behaviour for outstanding device work and ensure no orphaned GPU work contaminates
      later samples. Missing or incomplete controls yield no ratio; preserve warnings and partial accepted state.
- [ ] Explain small-input overhead, crossover, remaining serial work and tested scaling. Profile before
      neutral tuning, retain before/after evidence and repeat correctness checks. Additional sizes or launch
      studies must be labelled separately. Do not infer memory use, bandwidth limits or utilisation from timings
      alone; make such claims only with a declared measurement method and actual observations.
- [ ] If the PC or GPU is unavailable, continue host-only verification or clearly provisional exploration.
      Do not replace primary results with laptop/device-mixed samples or mark the hardware campaign complete.

### Gate G02 evidence

Retained primary-PC results, independently checked summaries and numerical qualification support an
honest same-device comparison. Timers measure completed work, setup and transfer costs are visible,
and isolated kernel gains are not described as whole-solver or whole-application speedups. Mixed or
negative performance is acceptable when the experiment and its limitations are reproducible.

## Phase 3: evaluate, document and hand off

### Objective

Explain GPU correctness and measured benefit, then prepare application integration without implementing it.

### Work

- [ ] Assess numerical agreement, repeatability, failure safety, public usability and performance separately.
      Link findings to full source revisions, tests and retained hardware results. Explain important design
      decisions, diagnosed defects and contract revisions without rewriting CPU history.
- [ ] Evaluate the tested range, arithmetic differences, storage/capacity limits, cancellation latency,
      transfer/setup overhead and relevant device variability. Distinguish observed bottlenecks from hypotheses;
      faster execution or agreement within a budget does not establish improved physical fluid accuracy.
- [ ] Document optional builds, device selection, execution/replay identity, unsupported environments and
      actionable failure behaviour. Keep the milestone summary suitable for the final project synthesis.
- [ ] Define the application-integration handoff: read-only accepted snapshots, ownership and synchronisation
      obligations, independent rendering, CPU/GPU controls, fixtures, comparison evidence and measurement
      boundaries. Describe any future graphics interoperability as future work, not an implemented guarantee.
- [ ] When separately authorised, complete the implementation-first checkpoint sequence, pin the final
      Maelstrom commit through EPQ's gitlink and evidence, and establish annotated completion tags in both
      repositories. Remote publication remains a separate authorised action.

### Gate G03 evidence

The evaluation explains what is supported, what remains unverified and what application integration
must preserve. Another agent can identify the current contracts, reproduce the qualified build and
interpret the comparison. The final checkpoint retains code, tests, records and exact parent/submodule
pairing; it does not imply completion of rendering or the final cross-backend project evaluation.

## Records and checkpoints

Keep the full phase sequence here. Add concise records as work actually begins, following the existing
template and source/evidence conventions. Each record names only its own phase and gate; simulator
source, tests and public documentation describe enduring technical responsibilities instead.

Use `milestone/03-cuda-gpu` integration branches and the established temporary phase-branch and
annotated-tag conventions. This planning task does not authorise commits, tags, branch changes,
pushes or gitlink updates. Historical toolchain notes, fresh hardware checks, local verification,
committed work and published checkpoints are distinct evidence.
