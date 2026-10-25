# Measuring host acceptance before changing it

The [performance plan](/docs/project/development/milestones/05/performance-plan.md) left host acceptance
open after the [correction investigation](/docs/project/development/milestones/05/performance-correction-profile.md).
This investigation measured its components before selecting a change. The
[protocol](/docs/project/development/milestones/05/performance-acceptance-protocol.md) required a material
cost, a short screen and then a complete matched PC campaign.

**Current outcome: retain the inlining change after an engineering reassessment.**
The original rule caused a reversion because the overall timing ranges overlapped. That
historical outcome remains recorded. The [reassessment](/docs/project/development/assets/acceptance-review-v1/README.md)
weighs the paired results, component saving, correctness evidence and one-annotation cost
under the revised [policy](/docs/project/development/milestones/05/performance-assessment.md).

## What the probes found

A separate diagnostic build timed the final velocity operation and its wait, position and velocity
downloads, particle reconstruction, particle validation, plane validation and state
replacement. Each received one pair of monotonic readings per step, with records emitted
afterwards. These probes were never added to the production source or public output schema.

| Particles | Control plane-validation median | Share of instrumented solver median | Candidate plane-validation median |
| --- | --- | --- | --- |
| 8,000 | 0.196 s | 9.3% | 0.022 s |
| 110,592 | 2.714 s | 18.8% | 0.304 s |

Each component result uses a warm-up and three diagnostic samples over 480 steps.
The larger case exceeded the prospective 10% opportunity threshold. These instrumented
results locate work; they are not interchangeable with ordinary performance samples.

## The bounded change

Generated host code kept `Plane::contains` as a separate call inside the acceptance loop.
The candidate added only `#[inline(always)]`, making that existing checked body
available to the optimiser at its callers. Every expression and source check remained,
including non-finite handling, overflow, plane order and error priority. Particle identity,
cancellation and atomic acceptance were unchanged. Generated device code was identical.

An ordinary `#[inline]` hint still left calls in the stepping code. Stronger guidance
removed them. Inspection also needed ELF relocation information: searching only for
named calls missed indirect control calls. The corrected reader and a focused
regression test were in place before screening samples were collected.

The three-pair uninstrumented screen at 110,592 particles improved from 12.730 to
10.363 s at the median, with separate ranges. That admitted full qualification; it
was not the final result.

## Whole-run results and the failed admission

Both collections used fresh warm-ups and five alternating pairs per size, 480 steps,
refinement four, eight iterations and CUDA device zero/128 lanes on the primary PC.
The 8,000-particle case retained checkpoints 0/1/120/240/480; the larger case had none.
The PC used an RTX 4070 and Ryzen 9 7900X under WSL2, Rust 1.96.0, CUDA 13.3.73
and driver 610.88. Exact commands and environment outputs are retained with the data.

| Collection | Particles | Control median and range | Candidate median and range |
| --- | --- | --- | --- |
| Initial campaign | 8,000 | 1.961 s; 1.949–2.392 s | 1.827 s; 1.770–2.402 s |
| Initial campaign | 110,592 | 13.640 s; 12.815–15.790 s | 13.249 s; 10.331–13.361 s |
| Separate confirmation | 8,000 | 2.099 s; 1.949–2.301 s | 1.897 s; 1.818–1.993 s |
| Separate confirmation | 110,592 | 13.537 s; 12.631–15.546 s | 10.209 s; 10.196–13.061 s |

The rule required at least 1.05× median speedup with non-overlapping five-sample ranges
at one size, and neither median more than 3% slower. Both collections failed the range
condition. No slow sample was removed and the two datasets were not pooled.
All five confirmation pairs favoured the candidate at both sizes. The historical rule
ignored that pairing: the slowest candidate was compared with the fastest control from
another pair. Its failed outcome remains intact, but it no longer decides retention.

The initial large samples changed abruptly partway through collection. Subsequent full
traces returned to shorter durations: 12.918 versus 10.514 s from first launch to final
completion. GPU busy time was almost unchanged, 8.344 versus 8.368 s; recorded idle gaps
fell from 4.574 to 2.146 s. Together with the probes, this supports a host saving without
adding overlapping intervals or claiming the trace boundary is the complete solver timer.

The separately specified [confirmation](/docs/project/development/milestones/05/performance-acceptance-confirmation.md)
kept the same thresholds and recorded machine state
outside each invocation. It still failed. The PC was reported to be used only for browsing;
the readings do not establish the cause or exclude unobserved Windows activity. The
original range rule was subsequently identified as unsuitable for the retention decision.

## Original verification and remaining limits

Both source exports passed 258 CUDA release tests, with the same three automatic-backend
CLI failures reproduced in the control. The candidate also passed strict Clippy, formatting
and native ASan/UBSan. The local candidate and restored source each passed 239 CPU tests; the updated parent tools
passed 44 tests and Python compilation. Tests were neither weakened nor skipped.

All five capacity sizes, through 512,000 particles, completed and matched retained
physical outputs and warning schedules. Larger CFL warnings remain; matching them does
not independently qualify fluid quality. The confirmation reused the exact source,
executables, correctness tests and capacity evidence rather than claiming fresh tests.

The [evidence bundle](/docs/project/development/assets/acceptance-inline-v1/README.md)
identifies the source exports, raw results, source reconstruction and independent audits.
It keeps the initial failed campaign as well as the confirmation. No hosted, other-platform,
actual device-loss or passing device-memory-sanitiser result follows.

## Final assessment

Retain the change. Every confirmation pair improved at both sizes; the larger pairs saved
2.355–3.862 s, and their workload median fell from 13.537 to 10.209 s. Probes and traces
support the host-cost explanation. The change is one annotation, with unchanged expressions,
checked behaviour and device code. That benefit justifies its small maintenance cost.

The reinstated source exactly matches the previously PC-qualified candidate. Its numerical,
capacity and timing evidence is reused explicitly; no new benchmark is claimed. New report
code summarises paired effects and requires a written assessment. Historical data and automatic
decisions remain unchanged in the original bundle, whose restoration statements describe the
earlier outcome. Fresh verification is recorded with the reassessment.
The reinstated source passes 239 CPU tests, strict local Clippy and formatting; the
updated evidence tools pass 53 tests and Python compilation.

The scope of the performance claim remains these PC workloads. Variation is unresolved;
larger CFL warnings and independent quality qualification remain open. Evolved neighbour
construction is the next measured implementation priority. Git state and earlier work are preserved.

The published implementation is [Maelstrom `8c5fc2d815f6e6c1d17b8eeed17cd7bf22b43fce`](https://github.com/Mahkrab/Maelstrom/tree/8c5fc2d815f6e6c1d17b8eeed17cd7bf22b43fce).
Its 150 committed files match the assessed implementation; the unrelated custom scene in
the measured 151-file local catalogue remains untracked. The exact committed snapshot
passed 239 CPU tests before publication. Earlier measurements retain their original identities.
