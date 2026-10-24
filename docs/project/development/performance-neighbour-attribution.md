# Neighbour cost attribution

On 25 October 2026 I separated neighbour traversal, row filling and identity sorting
on the primary PC. This completes the next diagnostic task in the
[optimisation plan](/docs/project/development/performance-plan.md), rather than introducing
another production optimisation. The [evidence](/docs/project/development/assets/neighbour-attribution-v1/README.md)
retains commands, source identities, results, trace data and unsuccessful setup attempts.

## Method and correctness

The control was the retained cell-cursor implementation, exported from the working
tree based on Maelstrom `8c5fc2d815f6e6c1d17b8eeed17cd7bf22b43fce`.
Its 152 source-file hashes matched that measured snapshot before export. The diagnostic
export changed only neighbour discovery, its device dispatch and the bridge's launches.
It leaves the original completion and transfer boundaries in place, but adds two launches
per step: a dry traversal and a separate heapsort after the ordinary fill.

The dry pass performs the same checked distances, support decisions and row-length
validation without writing neighbour indices. Fill writes the indices; sorting then
orders each row. It is not valid to call the difference between dry and fill times
isolated global-store latency: the paths also differ in compiler decisions and cache state.
Similarly, splitting the original combined kernel changes its resources and scheduling.

Both sizes used CUDA device 0, 128 lanes, 480 steps, timestep refinement 4 and eight
Jacobi iterations, with no checkpoint audits. Each variant received an untimed warm-up
and one full Nsight Systems capture. The PC had a Ryzen 9 7900X and RTX 4070 under WSL2.
These are exploratory device-cost measurements, not five-sample production timings.

All four traces completed and agreed exactly on physical results and ordered diagnostics;
warm-ups agreed too. Transfers and the 24,481 stream completions were unchanged. At
110,592 particles the diagnostic export added 960 launches to the control's 99,360.
All 18 explicitly enabled CUDA library tests passed, including independent discovery,
dense rows, tails, invalid offsets, diagnostic precedence and retry. Larger trajectories
retain their existing CFL warnings; exact agreement does not qualify their fluid quality.

## What consumes the neighbour time?

The following are device milliseconds per accepted step at 110,592 particles.

| Pass | Steps 1–120 | Steps 241–480 |
| --- | ---: | ---: |
| Control count | 0.705 | 2.036 |
| Control combined fill/sort | 1.932 | 4.164 |
| Diagnostic dry traversal | 0.711 | 2.032 |
| Diagnostic fill | 0.748 | 2.131 |
| Diagnostic identity sort | 1.419 | 2.322 |

Sorting is a substantial cost, while fill remains close to the dry checked traversal.
This supports investigating cooperative integer row sorting alongside traversal efficiency.
It does not support prioritising a large write cache simply because row writes exist.
The separate fill-plus-sort cost exceeds the control's combined cost; the diagnostic split
is not retained in the simulator. The 8,000-particle trace remains available separately.

## What the compiler already removes

I also compiled line-annotated PTX and an offline `sm_89` cubin with the existing precise
arithmetic flags. The multiplier has one static `sqrt.rn.f32` site per neighbour loop:
density, owner and squared gradients. Correction has one. Thus the repeated source-level
distance expressions within those loops have already been shared in this compilation.
There are eight square-root sites across the complete solver entry, including discovery
and validation; that static total is not a dynamic instruction count.

Cross-loop repetition remains: owner and squared-gradient traversals still calculate
their own geometry. The earlier ordered-prefix candidate therefore remains relevant,
while a local distance variable in correction alone has no demonstrated speed benefit.
The offline solver reports 46 registers and no local or shared allocation. Its assembly
is retained, but is not a dump of the actual driver-loaded PTX JIT, and no new hardware
counters were collected. Register usage does not establish achieved occupancy.

## Decision

Keep the existing production solver and the new attribution tooling. The next implementation
experiments are dedicated operation entry points, cooperative identity sorting, and a fresh
ordered-prefix assessment, each measured separately under the
[engineering policy](/docs/project/development/performance-assessment.md). Shared-memory staging
and component layout remain candidates requiring evidence of useful access patterns.

The first diagnostic bridge build needed a normal C++ array instead of an initializer-list
range expression. A later disassembly command used an option belonging to `nvdisasm`, not
`cuobjdump`; separate retries produced both ordinary and line-annotated assembly. Original
failures remain recorded. No failed setup or instrumented duration is counted as a speedup.
