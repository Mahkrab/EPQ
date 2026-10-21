# Milestone 04 Completion Plan

## Purpose and starting point

Turn the verified simulator into an interactive 3D application with reproducible offline rendering.
Reuse the existing scenes, configuration, backends, diagnostics, replay and output safety. Presentation
must make accepted simulation state useful to a person without becoming part of its numerical method.

The local `milestone-04/start` checkpoints identify EPQ
`87ec0e4d673751c3756a30b10085ec251e9c6372` and Maelstrom
[`afb8ffbf6482d7d70fe01d03d6c32ce2277ad96b`](https://github.com/Mahkrab/Maelstrom/tree/afb8ffbf6482d7d70fe01d03d6c32ce2277ad96b).
The [CUDA evaluation and application handoff](/docs/project/development/milestones/03/cuda-gpu.md)
owns the accepted-snapshot, thread-ownership and timing obligations. No windowing, renderer or
graphics interoperability is implied by these checkpoints.

There are four phases: application contracts and lifecycle, interactive viewing, offline rendering,
then verification, evaluation and handoff. Follow the applicable `AGENTS.md` instructions and choose
internal structure and dependencies from the real responsibilities. This plan specifies outcomes
and evidence, not a graphics library, module layout or command sequence.

## Contracts and scope

Preserve the [numerical contract](/docs/project/development/milestones/00/phases/phase-00-design-contract.md),
[comparison policy](/docs/project/development/milestones/00/reference-verification.md) and
[measurement boundaries](/docs/project/development/milestones/00/measurement-protocol.md). Keep the
solver core headless and independently usable. Windows, controls, rendering and export consume
accepted observations; they cannot mutate solver scratch or determine whether a timestep succeeded.

Retain brute force, serial grid, threaded grid and optional CUDA with explicit effective settings.
Existing CLI journeys, historical result replay and CPU-only builds must keep working without a
display, graphics initialisation, CUDA toolkit or device where those features are not selected.
New application/render settings must not change physical input identity or add EPQ-specific scene roles
to the simulator. A reference experiment remains an external scene and documented run selection.

Numerical and measurement contracts can evolve deliberately. Explain the evidence and rationale,
update the owning decision and version affected semantics or experiments. Requalify affected backends,
reference outputs and comparisons under common revised conditions. Keep historical checkpoints and
findings identifiable; do not move published tags or silently reinterpret old evidence. A changed
workload, numerical repair or reduced solver work is not an application optimisation.

The final project document will synthesise these development records, code and datasets. Keep records
concise and traceable, not immutable final chapters or copied implementations. This plan changes no
numerical values or acceptance limits by itself.

This milestone delivers a usable particle-fluid viewer, controls and a reproducible image-output
workflow. Photorealistic surface reconstruction, a general scene editor, arbitrary live numerical
editing, multi-GPU execution and zero-copy CUDA/graphics interoperability are not prerequisites.
Do not add them without a concrete need and separate justification. The final cross-backend research
evaluation remains distinct from verifying this application.

| Gate | Required outcome |
| --- | --- |
| G00 | Application ownership, control, observation and frame/output contracts are decided and their non-visual lifecycle is independently tested |
| G01 | A usable interactive viewer controls supported backends without changing solver results or blocking reliable shutdown |
| G02 | Offline rendering produces a reproducible, easily playable saved frame sequence with explicit provenance, safe publication and verified numerical independence |
| G03 | Application verification, supported environments, limitations and final-evaluation handoff are documented and checkpointed |

Gate labels belong to this milestone. A compiling window, screenshot or successful graphics probe
does not establish solver correctness, complete interaction or reproducible offline rendering.

## Phase 0: define application contracts and implement the lifecycle boundary

### Objective

Establish how a presentation layer controls a run and observes accepted state, with independently
testable behaviour before graphics integration.

### Work

- [x] Review the definition, backend interfaces and CUDA handoff. Decide a focused user journey:
      select/validate inputs and execution, start a run, inspect/control it, and produce offline frames.
      Define the minimum controls and visible diagnostics rather than building a general editor.
- [x] Choose the intended windowing/rendering and offscreen-output approach, supported platform and
      dependency/feature boundaries. Justify maintenance, portability, build and licence costs. Verify
      actual display/offscreen availability where necessary; prior CUDA access does not qualify graphics.
- [x] Specify construction, running, pause, single-step, reset/restart, completion, cancellation and failure
      states, including invalid transitions. Decide when scene/backend changes take effect and how queued
      commands or observations are discarded on restart so an old run cannot overwrite a new one.
- [x] Implement the non-visual controller and observation boundary using existing solver responsibilities.
      If simulation uses a worker thread, construct, use and destroy its CUDA solver there. Pass owned
      accepted snapshots to presentation; never introduce unsafe thread sharing to bypass context ownership.
- [x] Define bounded command/snapshot transport, backpressure and shutdown. Decide which intermediate
      display observations may be dropped or coalesced while retaining final accepted state and failures.
      Keep cancellation latched and allow synchronous stages to finish; do not promise an untested deadline.
- [x] Define simulation pacing independently of display cadence: fixed timesteps, pause semantics,
      catch-up/lag policy and interpolation, if any. Dropping a displayed frame must not drop numerical work,
      change timestep size or conceal an incomplete run. Label interpolated display state as presentation.
- [x] Specify coordinate/length conventions, particle size/colour interpretation, camera/projection,
      boundary depiction and frame-to-step mapping. Choose a clear particle representation first; visual
      smoothing must not be presented as a new physical surface or numerical validation.
- [x] Specify versioned render/export settings and precedence using existing configuration conventions.
      Resolve paths deliberately. Define authoritative frame count, first/last frame, simulation-step
      sampling, image format, dimensions, camera state, filenames and metadata without relying on wall time.
      Distinguish rendering saved observations from rerunning recorded inputs; replay is not resumption.
- [x] Define what reproducibility means for simulation inputs, accepted snapshots, frame schedule and
      renderer settings. Decide the supported image-comparison guarantee and record any environment
      dependence; do not promise cross-device pixel equality without evidence.
- [x] Independently test control transitions, exact single-step counts, pause, reset generation, cancellation,
      failure retention, bounded transport and teardown without a renderer. Compare accepted results with
      direct headless execution, using controlled clocks and deliberate stale/delayed consumer cases.

### Gate G00 evidence

The controller can be exercised without a window. Tests establish state transitions, owned observations,
fixed solver work, restart isolation and failure/shutdown behaviour. The interaction and offline frame
contracts are complete enough to implement without guessing; no full viewer or exporter is implied yet.

The [implementation and verification record](/docs/project/development/milestones/04/phases/phase-00-application-lifecycle.md)
records the satisfied gate and its hardware limitations. The
[application contract](/docs/project/development/milestones/04/application-contract.md) owns the agreed
interaction, lifecycle and frame/output behaviour. Local annotated `milestone-04/phase-00/complete`
checkpoints retain the assessed implementation and exact parent/submodule pairing. Fresh CUDA-worker
and graphics checks were unverified at that checkpoint; the viewer record below owns subsequent
evidence. Remote publication is separate.

## Phase 1: integrate the interactive 3D viewer

### Objective

Provide a usable view of the simulation while keeping controls, rendering and numerical ownership separate.

### Work

- [x] Integrate the selected optional graphics path through a thin application entry point. Keep the
      existing headless CLI and tests independent of display setup. Report unsupported graphics/device
      combinations clearly; an explicit CUDA request must not silently become CPU execution.
- [x] Render accepted particle positions and useful static boundaries with a clear camera and sensible
      framing. Handle empty/single-particle scenes, large/small extents, occlusion and clipping deliberately.
      Keep display conversion from metres separate from the authoritative particle data.
- [x] Expose the agreed scene/configuration and backend settings, start/pause/resume/single-step/reset,
      camera controls and cancellation/close behaviour. Validate external inputs before replacing an
      accepted run. Failed setup or switching must not hide the old outcome or present stale frames as new.
- [x] Display completed steps/simulated time, effective backend/resources, completion/failure and meaningful
      warnings. Distinguish display frame rate, simulation throughput and solver timing; a fast redraw of
      unchanged state is not a fast simulation. Keep personal paths out of public diagnostics.
- [x] Keep interaction responsive during stepping and slow presentation. Exercise resize/minimise,
      zero drawable extent, surface recreation, unavailable resources and window close during work.
      Graphics failure must not corrupt accepted solver state or strand a worker/context.
- [x] Test numerical independence under varied display cadence, camera movement, dropped observations,
      pause/step and reset. Retain exact serial checks and the applicable backend comparison policy.
      Verify all four execution choices where available, including CPU-only operation without CUDA.
- [x] Obtain real interactive evidence on the supported display environment: controls, warnings, failure,
      resize and shutdown, with source/build/device context. Keep rendered/hardware evidence separate from
      mocked event tests; SSH access alone does not establish that an interactive journey was exercised.

### Gate G01 evidence

A person can select and control a run, understand its state and inspect its particles in 3D. Real
display checks and deterministic integration tests support that judgement. Visual changes do not
alter accepted numerical results, and resource or graphics failures have explicit, safe outcomes.

The [interactive viewer record](/docs/project/development/milestones/04/phases/phase-01-interactive-viewer.md)
records the local G01 decision, retained display checks, exact CPU/CUDA comparisons and graphics
limits. Local annotated `milestone-04/phase-01/complete` checkpoints retain the assessed implementation
and exact parent/submodule pairing. Remote publication is separate. Offline sequence export remains
outside this gate.

## Phase 2: implement reproducible offline rendering and output

### Objective

Produce an explicit, repeatable image sequence independently of interactive display speed, then
play it without recomputing the simulation or rendering the particles again.

### Work

- [x] Implement the agreed offline entry point and frame schedule. Drive observations by accepted step
      indices, not the wall clock. Define initial/final frames, repeated observations, interpolation and
      unsupported sampling requests consistently with the contract; do not invent unstored intermediate state.
- [x] Reuse rendering responsibilities without requiring an interactive window where offscreen support is
      claimed. Identify the actual graphics device separately from the simulation backend. A CPU simulation
      may still require graphics capability to render; do not confuse that with headless solver portability.
- [x] Preserve ordinary result/replay behaviour. For saved-result rendering, validate available checkpoints
      and inputs; reject an impossible schedule or explicitly rerun identified inputs as a separate operation.
      Any rerun must retain its numerical comparison and execution provenance.
- [x] Record full input/source identities, effective backend, accepted-step/frame mapping, render schema,
      camera, dimensions, image format and relevant graphics/build context. Retain selected image hashes
      and a completion manifest so an incomplete sequence cannot masquerade as a complete export.
- [x] Extend existing non-clobbering publication deliberately for multi-file output. Validate destinations,
      preserve prior files, report partial progress and write final completion metadata only after success.
      Exercise cancellation, disk/encoding/readback failure and interruption without deleting user data.
- [x] Independently check frame counts, endpoints, ordering, names and step mappings, including zero-step,
      empty, sparse-checkpoint and partial-run cases. Repeated rendering must satisfy the declared image
      guarantee. Test orientation, scale and camera projection with simple known geometry, not visual guesswork.
- [x] Compare exported observations against direct headless execution under the same physical request.
      Retain evidence from at least a small deterministic fixture and the existing falling-block request;
      do not replace the benchmark scene or goldens merely to make presentation easier.
- [x] Open a completed image sequence through a saved-playback command without numerical execution
      or particle rendering. Support pause, seeking, speed, endpoints and repetition, preserve aspect
      ratio and report missing/corrupt images without recomputation or writes.

### Gate G02 evidence

Saved-image playback is also required: independently check timing, pause, seeking, speed changes,
endpoints, fixed-camera resizing and malformed/missing images, then exercise a real window. A
completed export alone does not satisfy the complete viewing journey.

Another agent can reconstruct the numerical observations and frame schedule from the manifest and
identified inputs, and render under the documented environment. Image checks, publication failures
and numerical comparisons establish reproducibility within the stated guarantee. Screenshots alone
do not establish a complete offline-output workflow.

The [offline rendering record](/docs/project/development/milestones/04/phases/phase-02-offline-rendering.md)
records the local G02 decision and the
[retained evidence](/docs/project/development/milestones/04/assets/offline-v1/README.md).
[Saved-playback evidence](/docs/project/development/milestones/04/assets/playback-v1/README.md)
extends that assessment to the completed viewing journey. Qualification covers windowless software
Vulkan and WSLg playback on the recorded WSL2 environment, with exact CPU observation checks and
saved CUDA observations. The [primary-PC capture](/docs/project/development/milestones/04/assets/pc-export-v1/README.md)
adds 8,000 particles, 480 CUDA steps and 481 images transferred to laptop playback, with zero CFL
warnings and matching image hashes. It does not add an independent numerical comparison or timing
claim. Hardware Vulkan export remains unqualified. Local annotated `milestone-04/phase-02/complete`
checkpoints retain the final implementation and exact EPQ gitlink; remote publication is separate.

## Phase 3: verify, evaluate and prepare final project comparison

### Objective

Establish that the application is usable and reproducible without invalidating the backend evidence.

### Work

- [ ] Review the implementation against the interaction, lifecycle, frame and publication contracts.
      Assess usability, numerical independence, failure safety and offline reproducibility separately.
      Record important decisions and actual defects without inventing retrospective alternatives.
- [ ] Run the appropriate CPU/headless regression and renderer/controller checks. Exercise CUDA integration
      and real display/offscreen paths on supported hardware, retaining commands or manual actions,
      observed outcomes, source/build context and limitations. Missing hardware checks remain unverified.
- [ ] Keep solver, snapshot transport/copies, audits, graphics, encoding and total application costs
      distinct. Use `ssh pc` for important measurements or performance claims; declare the workload and
      timing boundary before collection. Do not reinterpret existing solver speedups as interactive FPS.
- [ ] Document supported launch/build paths, controls, settings, output/replay semantics and recovery.
      State unsupported environments, visual/model limitations and any unverified graphics interoperability.
      Keep the summary useful for the final project document rather than duplicating implementation detail.
- [ ] Define the final comparative-evaluation handoff: retain all CPU/CUDA controls, exact scene families,
      numerical policies, raw campaigns, accepted-state and output contracts, device provenance and
      known threats to validity. Identify any genuine remaining evidence gap without starting a new
      unrestricted optimisation or comparative campaign here.
- [ ] When separately authorised, checkpoint implementation first, then EPQ's exact gitlink and evidence,
      and establish annotated completion tags in both histories. Treat publication as a separate action.

### Gate G03 evidence

The application and offline workflow have an evidence-backed evaluation, reproducible usage guidance
and an explicit final-comparison handoff. The completion checkpoint retains assessed code, tests,
records and exact parent/submodule pairing. It does not itself complete the final research evaluation.

## Records and checkpoints

Keep the full phase sequence here. Add concise implementation records as each phase actually begins,
following the existing template and citation conventions. Individual records identify only their own
phase/gate; source, tests and public documentation describe enduring responsibilities instead.

Use `milestone/04-application-visualisation` integration branches and the established phase-branch
and annotated-tag conventions. Preparing the plan and local start checkpoints does not by itself
authorise implementation, completion tags, remote publication or PC changes.
Local tests, real display/device checks, committed evidence and published checkpoints remain distinct.
