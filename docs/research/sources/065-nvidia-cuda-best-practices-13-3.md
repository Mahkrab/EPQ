# S065 — NVIDIA (n.d.)

## Full reference:

NVIDIA Corporation (n.d.) *CUDA C++ Best Practices Guide*. Version 13.3.
Accessed 24 October 2026.

#### https://docs.nvidia.com/cuda/archive/13.3.0/cuda-c-best-practices-guide/index.html

## Relevance:

Supports assessment of GPU memory layout, shared-memory reuse and kernel resource trade-offs.

## Reliability:

Official, versioned implementation guidance. Its examples do not establish a Maelstrom speedup;
the project's workloads and generated code need separate measurement.

## Tags

`cuda`, `memory-layout`, `shared-memory`, `performance`

## Reading notes

- Read §§10.2.1, 10.2.3, 11.1 and 13.1 on 24 October 2026. Access patterns, data reuse,
  resource limits and control flow inform the candidate review; higher occupancy alone is not a result.

#### Date added

24/10/26
