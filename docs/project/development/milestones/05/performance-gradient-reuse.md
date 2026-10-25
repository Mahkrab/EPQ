# Reusing the multiplier's ordered gradient prefix

The [performance plan](/docs/project/development/milestones/05/performance-plan.md) next calls for
measured arithmetic reuse. Inspection found that the CUDA multiplier pass calculated
each active pair's Spiky direction while building the owner vector, then recalculated
it while summing squared neighbour gradients. Positions do not change between those
loops. The [protocol](/docs/project/development/milestones/05/performance-gradient-protocol.md) fixes
the experiment and its keep/reject criteria before measurement.

**Outcome: the trial was not retained.** It improved the multiplier kernel, but the
whole-solver medians missed the prospective admission criterion. The original CUDA
multiplier loop is restored; new regression tests and the rejected trial remain evidence.

## Candidate and trade-off

A full per-pair cache would remove more recalculation but introduce storage and memory
traffic. This trial instead reuses the lower-identity prefix in registers. It accumulates
those squared contributions in precisely their original order, finishes the owner vector,
inserts the owner's square, then processes higher-identity neighbours. There is no
reassociation of independently summed halves. The suffix still recalculates its gradients;
this is partial reuse, not a claim that every repeated Spiky evaluation has disappeared.

Earlier evaluation must not mean earlier failure reporting. Prefix square/sum checks use
a separate error flag, which becomes visible only after all owner checks have finished.
That preserves owner-before-squared-sum precedence. Current support is still checked for
the unchanged prediction membership. No result survives into another position snapshot,
and no new allocation, transfer, kernel or cancellation boundary is introduced.

## Matched PC result and decision

Each variant received a warm-up and five alternating samples at each declared size.
Both used 480 refined steps, eight iterations, device zero/128 lanes and no rendering.
The 8,000-particle case retained its observation schedule; the larger paired case had
no checkpoint audits and retained the control's 259 CFL-warning steps.

| Particles | Original median | Trial median | Original range | Trial range |
| --- | --- | --- | --- | --- |
| 8,000 | 2.023 s | 1.954 s | 1.936–2.040 s | 1.873–2.074 s |
| 110,592 | 13.194 s | 12.800 s | 13.093–13.434 s | 12.537–13.045 s |

That is about 3.4% and 3.0% less solver time. The smaller ranges overlap. The larger
ranges do not, but neither median reaches the predeclared 1.05× gain criterion.
The independent reader reaches the same reject decision without trusting the collector.
This is a decision under the recorded engineering policy, not proof that a 3% gain can
never be worthwhile or that all gradient reuse is unhelpful. No sample was removed.

Separate traces show the multiplier kernel's accumulated device time falling from
0.1762 to 0.1569 s at 8,000/480, and from 0.01024 to 0.00799 s at 110,592/four.
Those are not primary timings or a large-scene speedup estimate. Entry-kernel registers
rose from 44 to 48 per thread; allocation, launch, completion and transfer models were
unchanged. These observations explain why source-level duplicated arithmetic deserves
measurement, but do not isolate register pressure as the cause of the modest overall gain.

The [evidence bundle](/docs/project/development/assets/gradient-prefix-v1/README.md)
retains the original samples, precise source/binary identities and a focused candidate
patch against Maelstrom
[`5120acfbcb07e94ebefd5957ad8f9afa47888be7`](https://github.com/Mahkrab/Maelstrom/tree/5120acfbcb07e94ebefd5957ad8f9afa47888be7).
Reconstruction matches all 149 assessed tracked files. The unrelated untracked custom
scene is excluded from that patch and was not a measurement input.

## Verification and remaining limits

The PC candidate passed 257 Rust checks, with the same three existing automatic-backend
CLI failures reproduced in the control. Strict CUDA Clippy, formatting and native
ASan/UBSan checks passed. New hardware cases check owner-overflow precedence, prefix-sum
and suffix-square overflow, owner ordering, inactive prediction neighbours and repeated
changed-position inputs across 32/64/128/256 lanes. Independent scalar cases and the
existing ordered CPU/component comparisons remain enabled.

The PC's previous temporary datasets were no longer available. Preparation stopped before
measurement; its raw failure is retained. Saved inputs and PC-produced controls were
restored byte-for-byte from retained evidence into the isolated workspace. No replacement
baseline was measured on the laptop. An SSH disconnect followed successful main collection;
detached continuation ran only the remaining comparison, report and traces, preserving all
completed samples. Neither incident is presented as a numerical failure.

The independent audit passed 26 observation-rich comparisons, five fresh serial/CUDA
pilots, five complete capacity trajectories and 12 larger paired observations. Warnings
and physical results matched exactly. False timing and retention summaries were rejected.
The local CPU suite passed 239 tests and the parent experiment suite passed 29. Original
profiler reports remain private; sanitised analytical tables and archive members are checked.

This completes the bounded arithmetic experiment, not the optimisation plan or physical
qualification. Larger trajectories still warn, and no final-quality, real-time, other-platform,
device-loss or passing device-memory-sanitiser claim follows. The original multiplier
implementation remains active. A full gradient cache and other arithmetic changes remain
untested alternatives, not work declared complete. User files, installed applications,
ordinary PC repositories, branches, commits, tags and the parent gitlink are untouched.

After restoration, the full PC release suite again passed 257 checks with the same
three CLI failures; strict Clippy and formatting passed. Only the new Rust regression
tests differ from the starting Maelstrom commit. The final verification is recorded
separately from the trial's benchmark source, so the rejected gain is not assigned to
the restored implementation.
