# Maelstrom Development Plan

## Preparation: project and experimental design

Define the documentation stages, infastructure behind the code, and api's, tools and languages used. As well as standards and templating.

## Milestone 00: serial CPU brute-force reference

Create and verify the complete single-threaded CPU reference implementation using bruteforce neighbour search.

The headless reference, local verification, evaluation and uniform-grid handoff are complete. The
[milestone record](/docs/project/development/milestones/00/serial-brute-force.md) records the
requirement assessments and accepted limits; the
[evaluation record](/docs/project/development/milestones/00/phases/phase-08-evaluation-handoff.md)
records the final local gate review and checkpoint boundary.
Matching annotated `milestone-00/phase-08/complete` and `milestone-00/complete` tags in both
repositories identify the published completion checkpoints and exact implementation gitlink.

## Milestone 01: serial CPU uniform-grid optimisation

Replace bruteforce neighbour discovery with uniform-grid spatial partitioning while retaining the serial CPU execution and numerical reference contract.

The [Milestone 01 completion plan](/docs/project/development/milestones/01/plan.md) groups the work into
implementation and verification, PC measurement, and evaluation and handoff. Existing numerical and
measurement contracts provide the comparison basis, not a ban on future revision. Evidence-led changes
must be recorded and applied to both sides of any affected comparison, with earlier results left identifiable.
Milestone records and datasets will feed one final project document rather than becoming immutable final prose.

The [evaluation and multithreading handoff](/docs/project/development/milestones/01/serial-uniform-grid.md)
assesses the implemented search and its retained evidence. The serial correctness checkpoint is
complete, and paired PC measurement and evaluation are complete. Local annotated `milestone-01/complete`
tags retain the final parent/submodule pairing; remote publication remains separate.

## Milestone 02: multithreaded CPU implementation

Parallelise the uniform grid simulation on the CPU while retaining the same inputs, numerical behaviour and observable outputs.

The [Milestone 02 completion plan](/docs/project/development/milestones/02/plan.md) groups the work into
threaded implementation and verification, PC measurement and scaling, then evaluation and CUDA handoff.
It reuses the existing infrastructure and retains explicit, evidence-led contract revision.

The [threaded CPU evaluation and CUDA handoff](/docs/project/development/milestones/02/threaded-cpu.md)
complete the local assessment. Annotated `milestone-02/complete` tags in both repositories retain
the assessed implementation and evidence; remote publication remains separate.

## Milestone 03: CUDA GPU implementation

Implement the uniform grid simulation for CUDA-capable GPUs and preserve comparability with the CPU reference implementations.

The [Milestone 03 completion plan](/docs/project/development/milestones/03/plan.md) separates device
integration, solver implementation and verification, PC measurement, then evaluation and application
handoff. It reuses the existing contracts and infrastructure while qualifying the new device boundary.

The [CUDA evaluation and application handoff](/docs/project/development/milestones/03/cuda-gpu.md)
assesses exact numerical agreement, measured gains and small-input slowdowns, device/failure limits,
and the accepted-snapshot boundary for future application work. Local annotated `milestone-03/complete`
tags retain the final implementation and evaluation; remote publication remains separate. Application integration and
the final cross-backend evaluation remain future work.

## Milestone 04: application and visualisation integration

Integrate the verified simulation backends into the interactive application, renderer and reproducible offline-output workflow without coupling rendering to simulation correctness or benchmark timing.

The [Milestone 04 completion plan](/docs/project/development/milestones/04/plan.md) separates application
contracts and lifecycle, interactive viewing, reproducible offline rendering, then evaluation and
handoff to the final project comparison. Presentation consumes accepted state without owning the physics.

The [application evaluation and final-comparison handoff](/docs/project/development/milestones/04/application-visualisation.md)
assesses interaction, numerical independence, failure retention and saved-output reproducibility
separately. It identifies supported environments, cost boundaries and retained CPU/CUDA controls.
Local annotated `milestone-04/complete` checkpoints retain the assessed implementation, verification
and exact parent/submodule pairing. Remote publication remains separate, and the final research
comparison has not begun.

## Milestone 05: comparative evaluation

Complete the controlled correctness, performance and scalability comparison across brute-force search, uniform-grid partitioning, CPU multithreading and CUDA acceleration, then evaluate the results against the research question.

The [Milestone 05 completion plan](/docs/project/development/milestones/05/plan.md) separates the
evidence audit and evaluation protocol, verified comparison evidence, then synthesis and final-project
handoff. The first decision is whether retained campaigns suffice or a matched new comparison is
needed; preparing the plan does not begin collection or establish an evaluation result.

