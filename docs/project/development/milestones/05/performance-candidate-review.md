# CUDA optimisation candidate review

The subsequent [26 October code audit](/docs/project/development/milestones/05/performance-cuda-code-audit.md)
reviews the current complete CUDA path and its Rust/application boundaries, with a separate
file-by-file assessment. The earlier findings below retain their dated source and trial context.

Reviewed on 24 October 2026. This covers the device solver, neighbour builder, Rust
orchestration, driver bridge, ordered CPU equations, regression tests and compilation
boundary. The current Maelstrom files match the retained 152-file
[measured snapshot](/docs/project/development/assets/neighbour-traversal-v1/source-review.json).
No simulator implementation or benchmark was changed for this review.

Commit links below identify unchanged code at
[`8c5fc2d815f6e6c1d17b8eeed17cd7bf22b43fce`](https://github.com/Mahkrab/Maelstrom/tree/8c5fc2d815f6e6c1d17b8eeed17cd7bf22b43fce).
The current neighbour traversal is the working snapshot recorded above, not a new Git checkpoint.

## What the current measurements support

The retained 110,592-particle, 480-step CUDA trace has a 10.315 s launch-to-completion
window. Its main accumulated device costs are:

| Work | Device time |
| --- | ---: |
| Correction | 2.594 s |
| Neighbour counting and fill/sort | 2.399 s |
| Density and multipliers | 1.863 s |
| Cell keys and cell sorting | 0.521 s |
| Active-distance validation | 0.505 s |

Traced device-idle gaps total 2.195 s. These are diagnostic intervals, not primary
solver timings or proof that every gap can be removed. Cache efficiency, bandwidth
and achieved occupancy remain unmeasured because the earlier counter attempt lacked
permission. Register counts alone do not establish achieved occupancy.<sup><a href="#ref-s064">S064</a></sup>

Do not rank operations by `launch_to_next_s`. Operation 8 has 5.274 s in that column
but only 0.009 s of device time: the host waits there for the preceding queued group.
Neither value measures the checks embedded throughout the other kernels.

## Are the proposed changes already planned?

| Proposal | Previous coverage | Assessment now |
| --- | --- | --- |
| [AoS/SoA](https://en.wikipedia.org/wiki/AoS_and_SoA) layout | Generic data-layout investigation | Explicit candidate for device vector components; start with hot position buffers |
| Dedicated kernels per operation | Kernel fusion and launch tuning, not explicit specialisation | High-priority structural experiment with unchanged stage bodies and ordering |
| Shared-memory neighbour cache | Generic cache/layout work | Conditional candidate after establishing useful reuse within a block |
| Remove `Checked` in production | Conflicts with existing failure guarantees | Do not treat as a transparent optimisation; prove individual redundancies instead |
| Reuse `spiky()` and `separation()` | Explicit arithmetic work; partial reuse already trialled | High-priority local reuse and fresh assessment of the earlier prefix candidate |
| Merge operation 6 neighbour loops | Partly addressed by the prefix trial | Consider staged fusion; a naive complete single traversal is not equivalent |
| Warp shuffles | Not explicit | Useful candidate for cooperative integer row sorting and deliberate data exchange |

## Findings from the code

### Reuse geometry before adding a large cache

In [operation 6](https://github.com/Mahkrab/Maelstrom/blob/8c5fc2d815f6e6c1d17b8eeed17cd7bf22b43fce/native/solver.cu#L100),
the density, owner-gradient and squared-gradient loops repeat current-distance work.
For a non-self neighbour inside support, their source paths express six norm
evaluations; operation 7 expresses three more. These are source counts, not confirmed
executed instruction counts: inspect the generated code before assuming all remain.

Start with one directed pair inside operation 7: share its displacement and distance
between support testing, Spiky and Poly6. Keep rounding and checked error selection.
Do not assume that sharing `(i,j)` with `(j,i)` also preserves signed zeros and row order.

A distance-plus-gradient cache costs at least `16 × E` bytes for `E` directed row
entries, before metadata and traffic. Current geometry changes after projection, so
a cache must follow the position snapshot and parameters, not just fixed membership.
It cannot survive unchanged through all Jacobi iterations.

The [ordered-prefix trial](/docs/project/development/milestones/05/performance-gradient-reuse.md)
already found roughly 3.4% and 3.0% median savings at the two sizes. Its rejection
used the historical 5% criterion. Reassess that candidate under the current policy
with fresh timings against today's implementation; preserve its original outcome.

### Specialise entry points without removing required barriers

The [bridge](https://github.com/Mahkrab/Maelstrom/blob/8c5fc2d815f6e6c1d17b8eeed17cd7bf22b43fce/native/bridge.cpp#L235)
loads one `solver` function and supplies a uniform operation ID to each launch.
That branch does not itself send lanes down different operation paths. Dedicated
entry points could instead permit separate resource budgets and tuning. Measure
that hypothesis; the current entry reports 46 registers per thread.

The solver already launches distinct kernels for its passes. Host operation 13
batches bitonic launches of device operation 3; it is not a missing device kernel.
Specialisation alone does not remove launches or synchronisations. Keep grouped
diagnostics and whole-grid dependencies, particularly completed multipliers before
correction. Account for loading multiple function handles and their failure paths.

The [build](https://github.com/Mahkrab/Maelstrom/blob/8c5fc2d815f6e6c1d17b8eeed17cd7bf22b43fce/build.rs#L84)
embeds PTX. Inspect driver-loaded resources alongside generated instructions;
offline compiler reports are useful diagnostics, not automatically the executed
driver JIT result. NVCC documents resource reporting separately.<sup><a href="#ref-s045">S045</a></sup>

### Layout and cooperative access need concrete targets

The [device ABI](https://github.com/Mahkrab/Maelstrom/blob/8c5fc2d815f6e6c1d17b8eeed17cd7bf22b43fce/native/solver.h#L6)
already separates particle attributes into buffers. Each vector buffer holds
12-byte `{x,y,z}` records. Component SoA is therefore a real candidate, but not a
reason to rewrite every CPU/public structure. Compare device positions first,
including packing, transfers, gathers and output reconstruction. Memory layout must
be assessed through its access pattern, not its name.<sup><a href="#ref-s065">S065</a></sup>

Current lanes own independent, variable-length rows; consecutive owner identities
need not remain spatial neighbours. A shared cache needs a demonstrably reused tile,
staging and a memory budget. It does not make all global reads disappear.<sup><a href="#ref-s065">S065</a></sup>
The existing tail and diagnostic early returns need review before introducing block
barriers: participating threads must reach compatible synchronisation points.<sup><a href="#ref-s012">S012</a></sup>

The [row heapsort](https://github.com/Mahkrab/Maelstrom/blob/8c5fc2d815f6e6c1d17b8eeed17cd7bf22b43fce/native/neighbours.cuh#L43)
currently runs in one lane over global memory. Cooperative integer sorting is a
specific shuffle candidate, with arbitrary row lengths and overflow behaviour kept.
Shuffle sources must participate in the named mask; shuffles are not memory fences.<sup><a href="#ref-s012">S012</a></sup>
A floating-point tree reduction would change the ordered reference arithmetic.

### Loop fusion and validation have observable dependencies

The CPU [multiplier](https://github.com/Mahkrab/Maelstrom/blob/8c5fc2d815f6e6c1d17b8eeed17cd7bf22b43fce/src/fluid.rs#L438)
inserts the completed owner's squared gradient among neighbours at its identity
position. Its value is unavailable before the owner sum finishes. Density and owner
accumulation may be interleaved while preserving their separate orders, but full
fusion needs cached contributions or an ordered prefix/suffix strategy. More live
values and staged error flags are costs to measure.

`Checked` preserves the first failing expression within a particle. The bridge also
preserves stage and particle precedence. Finite inputs do not prove finite intermediates.
Removing checks or making them debug-only changes release failure handling and can
permit an invalid accepted state. An unchecked mode would need an explicitly revised
contract and separate evidence. Proven redundant checks and repeated error-buffer
writes may be investigated while preserving the production decision and diagnostic tests.

Operation 5 validates every active row before operation 6. Folding it into per-particle
arithmetic would need to preserve that global failure precedence. The existing
[regression cases](https://github.com/Mahkrab/Maelstrom/blob/8c5fc2d815f6e6c1d17b8eeed17cd7bf22b43fce/src/cuda/solver_tests.rs#L222)
also expose owner-before-squared-sum failures. Final-output agreement alone is insufficient.

## Other candidates exposed by the review

- **Device bounds and integer prefix work:** [discovery orchestration](https://github.com/Mahkrab/Maelstrom/blob/8c5fc2d815f6e6c1d17b8eeed17cd7bf22b43fce/src/cuda/solver.rs#L227)
  downloads predicted positions, computes bounds and a checked row prefix on the host,
  then uploads offsets. Device reductions/scans could remove intermediate traffic;
  retain the exact width, overflow and allocation decisions.
- **State residency and host allocation:** preparation repacks/uploads accepted state
  each step, following final downloads and host acceptance. Residency is already on
  the plan, but changing accepted-state ownership needs explicit lifecycle qualification.
- **Invariant coefficients and power cost:** inspect generated Poly6/Spiky coefficient
  work before hoisting it. Preserve when errors become visible, including unused paths.
  The binary64 power approximation remains a separate unresolved cost; native `powf`
  or fast-math would be an arithmetic variant, not equivalent reuse.
- **Compilation throughput:** the [export path](https://github.com/Mahkrab/Maelstrom/blob/8c5fc2d815f6e6c1d17b8eeed17cd7bf22b43fce/src/export/mod.rs#L286)
  copies a portable snapshot every step, even when neither rendering nor comparison
  needs it. Frame processing is synchronous. These are application-throughput candidates
  under the [compilation record](/docs/project/development/milestones/05/performance-compilation.md),
  separate from solver-only gains.

## Recommended order and evidence

First finish the planned fill/distance/sort attribution and inspect operation 6/7
instructions. Then test dedicated operation entry points and local geometry reuse
as separate changes, with prefix reassessment in the arithmetic work. Device layout
and cooperative integer sorting follow the observed costs; shared tiling follows
demonstrated block reuse. Keep device-side prefix/residency work visible alongside them.

Use the [assessment policy](/docs/project/development/milestones/05/performance-assessment.md), current
PC baselines and separate early/evolved workloads. Retain all samples and failures.
Validate per-kernel resources, whole-run effects, exact numerical/error behaviour,
dense rows and tails. Higher occupancy, fewer source expressions or a faster microbenchmark
alone is not sufficient. This review does not establish any new speedup.

## Follow-up on 25 October

The [completed attribution](/docs/project/development/milestones/05/performance-neighbour-attribution.md)
finds substantial identity-sorting cost. Its generated PTX already shares repeated distances
within individual multiplier and correction loops; repetition across the multiplier loops
remains. Read the earlier source-expression counts with that compiler evidence. The solver
itself is unchanged; the separate large-manifest playback repair changes presentation input.

The subsequent [entry-point trial](/docs/project/development/milestones/05/performance-kernel-specialisation.md)
tested both complete specialisation and a numerical-pass-only follow-up. Neither is retained;
the current plan now prioritises cooperative integer sorting and cross-loop reuse.

## Follow-up on 26 October

The [fresh prefix reassessment](/docs/project/development/milestones/05/performance-gradient-reassessment.md)
retains ordered reuse after scene usability, with exact results and consistent primary-PC gains
at the larger workloads, including both fluid effects enabled. Its disqualified initial build
comparison remains separate. The subsequent
[cooperative sorting trial](/docs/project/development/milestones/05/performance-cooperative-sort.md)
also retains its change, with a bounded warp network and unrestricted dense-row fallback.
Further trials must compare against both retained changes. The subsequent
[host-coordination attribution](/docs/project/development/milestones/05/performance-coordination.md)
measured CPU bounds, CFL and prefix calculations at about 2% of the large disabled-effect run;
their surrounding downloads, repacking, reservation and offset upload raised the bound to about 5%.
Replacement device work would consume part of that opportunity. Standalone reductions/scans are
deferred for now on measured benefit and implementation cost, without an automatic percentage veto.
A fresh full-motion trace still ranked correction highest, at 2.566 s in an 8.888 s diagnostic window.
Next inspect its generated arithmetic and invariant coefficients before introducing a pair cache
or storage rewrite. Preserve floating-point order, failure handling and the existing retained changes.

The subsequent [compilation and block-size follow-up](/docs/project/development/milestones/05/performance-compilation-profile.md)
adds disjoint export timings and fresh same-executable controls. Block 32 led the disabled-effect
requests; 256 led the large enabled-effect request. The default remains 128 in this measurement step.
For 110,592 particles, full compilation spent about 30 s in frame hashes/snapshot JSON and 11 s in
PNG encoding. Snapshot capture was below 0.1 s. Prioritise bounded CPU frame preparation overlap
over copy removal for application throughput. Solver and graphics intervals also grew with every-step
images; trace that interaction rather than assigning a cause from utilisation alone. For solver
throughput, scope residency/batched submission and neighbour indexing as the audit recommends;
bounded correction work remains useful alongside them. These are next comparisons, not measured gains.

The first [accepted-buffer residency comparison](/docs/project/development/milestones/05/performance-resident-state.md)
is retained. Warm attempts keep accepted device vectors and static planes, with promotion after final
host checks. Five pairs per workload give modest gains without changed physical results; separate
traces remove 9,580 completions and most uploads while retaining all 99,840 launches and final readbacks.
The remaining device work now makes cell-run indexing a more useful next comparison than further
upload-only tuning. Full residency, observation materialisation and larger submission segments remain
open design work; the current snapshot and cancellation contracts are preserved.

## References used

<a name="ref-s012"></a> **S012** — NVIDIA, *CUDA Programming Guide*, Release 13.2, §§10.6 and 10.22.2.
[Source record](/docs/research/sources/012-nvidia-cuda-programming-guide-release-13-2.md).

<a name="ref-s045"></a> **S045** — NVIDIA, *NVCC*, CUDA 13.3, §4.2.8.16.
[Source record](/docs/research/sources/045-nvidia-nvcc.md).

<a name="ref-s064"></a> **S064** — NVIDIA, *Nsight Compute Profiling Guide*, sets/sections and occupancy.
[Source record](/docs/research/sources/064-nsight-compute-profiling.md).

<a name="ref-s065"></a> **S065** — NVIDIA, *CUDA C++ Best Practices Guide*, Version 13.3, §§10.2.1, 10.2.3, 11.1 and 13.1.
[Source record](/docs/research/sources/065-nvidia-cuda-best-practices-13-3.md).
