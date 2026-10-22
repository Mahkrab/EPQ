# S063 — NVIDIA (n.d.)

## Full reference:

NVIDIA (n.d.) *Nsight Systems User Guide*. Live documentation, accessed 22 October 2026.
Sections on focused profiling, CLI collection and CUDA tracing overhead.

#### https://docs.nvidia.com/nsight-systems/UserGuide/index.html

## Relevance:

Supports tracing CPU submission, CUDA execution, transfers and waits before selecting optimisations.

## Reliability:

Official tool documentation. The live page may change; installed versions, WSL support and
available tracing permissions must be recorded when collecting evidence.

## Tags

`profiling`, `cuda`, `measurement`

## Reading notes

- Read focused profiling, region labelling, CLI collection and CUDA tracing overhead guidance.
- Focused regions reduce irrelevant collection. Memory tracking and extensive API tracing can
  introduce overhead; profile durations must not replace ordinary benchmark samples.
- No profiler installation, PC capability check or profile collection was performed for this plan.

#### Date added

22/10/26
