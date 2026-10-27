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
- Re-read memory, execution-configuration and arithmetic guidance in §§10–12 on 26 October 2026
  for the code audit. Block-size and layout choices require workload measurements; source structure
  alone does not establish occupancy, achieved bandwidth or remaining arithmetic cost.

#### Date added

24/10/26
