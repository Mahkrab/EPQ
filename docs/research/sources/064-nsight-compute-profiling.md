# S064 — NVIDIA (n.d.)

## Full reference:

NVIDIA (n.d.) *Nsight Compute Profiling Guide*. Live documentation, accessed 22 October 2026.
Introduction and metric collection, including sets, sections and collection overhead.

#### https://docs.nvidia.com/nsight-compute/ProfilingGuide/index.html

## Relevance:

Supports targeted investigation of expensive kernels after the whole-run timeline identifies them.

## Reliability:

Official tool documentation. Metric availability depends on the actual device, driver, permissions
and tool version; documentation alone does not establish access on the project's PC.

## Tags

`profiling`, `cuda`, `kernels`, `measurement`

## Reading notes

- Read the profiling introduction and metric-collection sections.
- Selected sections collect kernel metrics; broader metric sets increase collection overhead.
  The guide distinguishes profiled execution from normal application execution.
- Instruction, memory and occupancy evidence may inform a kernel hypothesis, but utilisation
  alone is not an optimisation result. No counters were collected for this plan.

#### Date added

22/10/26
