# S012 — NVIDIA (2026)

## Full reference:

NVIDIA Corporation (2026) *CUDA Programming Guide*, Release 13.2.

#### https://docs.nvidia.com/cuda/archive/13.2.0/pdf/CUDA_C_Programming_Guide.pdf

## Relevance:

Supports Maelstrom’s CUDA backend design, including the execution model, memory hierarchy, kernel launches, synchronisation and host-device data management.

## Reliability:

Official NVIDIA documentation for a specific CUDA Toolkit release.

## Tags

`core`, `cuda`, `gpu-implementation`

## Reading notes

- On 22 October 2026, checked §10.14.1.4, `atomicMin()`: the unsigned 64-bit overload
  atomically selects a minimum and requires compute capability 5.0 or above. This
  supports Maelstrom's packed integer error selection, not a change to floating-point
  reductions or a performance claim. The source is Release 13.2; the measured PC uses
  toolkit 13.3, so actual compilation and hardware behaviour are verified separately.
- Also checked §6.2.8.5 and §6.2.8.5.3: commands within a stream execute in order,
  and stream synchronisation waits for its preceding commands. This supports whole-kernel
  dependencies without an intervening host wait, not communication between lanes within
  a running kernel or a measured speedup.

- On 24 October 2026, read §10.6 and §10.22.2: block barriers require compatible
  participation; warp shuffle masks name participating lanes and do not provide memory ordering.
  These requirements inform cooperative-kernel candidates, not measured gains.

#### Date added

05/07/26
