# S053 — NVIDIA (2026)

## Full reference:

NVIDIA (2026) *CUDA Driver API*. CUDA Toolkit v13.3.0. Last updated 17 June 2026.

#### https://docs.nvidia.com/cuda/archive/13.3.0/cuda-driver-api/index.html

## Relevance:

Defines the context, module, allocation, stream and completion operations used by Maelstrom's
Rust/C++ CUDA resource boundary. It informs explicit ownership and failure handling rather than
the fluid equations or a performance claim.

## Reliability:

NVIDIA's official, versioned API reference is authoritative for the documented interface. The
13.3 archive matches the installed toolkit family; actual driver availability and behaviour still
require hardware checks. Documentation alone cannot establish cleanup after real device loss.

## Tags

`cuda`, `driver-api`, `context`, `ownership`, `synchronisation`

## Reading notes

- Context management describes creating an isolated context, pushing/popping the calling thread's
  current context, and destroying the context with its associated resources.
- Stream management distinguishes launch submission from completion through stream synchronisation.
- Memory management supplies explicit allocation, synchronous host/device copies and release.
- Read the archived context, stream and memory sections on 18 October 2026. Maelstrom's conservative
  invalidation and retry policy is a project decision, verified separately with injected failures.
- On 22 October, checked the API and stream synchronisation sections for the compact-row experiment.
  A pageable host-to-device call can return after staging, before device DMA finishes. A non-blocking
  stream does not inherit the legacy stream's dependency; an ordinary private stream does.
  The hardware reproduction and chosen repair belong to the development record, not the API's claims.
- Also checked `cuLaunchKernel` for sort batching: launch arguments are copied from the supplied
  parameter storage, and a submission call may report an earlier asynchronous failure. Batching
  therefore retains completion checking and conservative invalidation rather than treating
  successful submission as completed work.
- For diagnostic readback, checked the synchronisation definition: a synchronous
  device-to-host copy returns only after the copy completes. Maelstrom's preceding
  private-stream wait and removal of a second wait are implementation decisions;
  their correctness and performance require separate tests and measurements.
- Checked `cuMemsetD8Async` for the diagnostic sentinel: it sets a byte range on the
  supplied stream and may report earlier asynchronous failures. Reset submission is
  therefore drained and checked under the same conservative resource policy.

- On 25 October 2026, checked the archived `CUjit_option` definition.
  `CU_JIT_OPTIMIZATION_LEVEL` defaults to 4, the highest documented level.
  Maelstrom uses ordinary `cuModuleLoadData` rather than overriding that setting.

#### Date added

18/10/26
