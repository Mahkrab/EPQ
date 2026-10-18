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

#### Date added

18/10/26
