# Host acceptance confirmation protocol

Historical collection protocol. Its automatic retention criteria describe the original
decision only; the [reassessment](/docs/project/development/assets/acceptance-review-v1/README.md)
retains the change under the current [assessment policy](/docs/project/development/performance-assessment.md).

The first campaign under the [acceptance protocol](/docs/project/development/performance-acceptance-protocol.md)
failed its retention rule: both five-sample ranges overlapped. Preserve that result and
every original sample. Do not relabel it as a pass or pool it with this confirmation.

The larger candidate's first two samples took 10.375 and 10.331 s; its remaining three
took 13.251, 13.249 and 13.361 s. The control also changed from roughly 12.8–13.6 s
to 15.7–15.8 s. Separate subsequent traces returned to 12.918 and 10.514 s over their
declared launch-to-completion boundary. Their GPU busy intervals were 8.344 and 8.368 s.
Instrumented plane validation fell from 2.714 to 0.304 s. These observations justify
checking reproducibility; they do not identify the cause of the changing run times.

Make **one** additional complete paired collection on the primary PC. Freeze this
protocol and collector before starting. Reuse the identical, already qualified source
exports and release executables; verify all their hashes before and after collection.
Do not change PC settings, clocks, security, drivers, application defaults or solver work.
Do not claim the PC was otherwise idle without evidence.

Keep the original two workloads: 8,000 particles with checkpoints 0/1/120/240/480,
and 110,592 without checkpoints. Both use 480 refined steps, eight iterations, CUDA
device zero/128 lanes and `--unpaced`. Run one warm-up then five fresh alternating
pairs per size, reversing order on even pairs. Run nothing else from this investigation
on the PC during collection. Keep the existing 120 s timeout and 30 s grace.

Outside each simulation invocation, retain GPU utilisation, temperature, performance
state, clock, power and reported clock-event reasons, plus Linux CPU counters and load.
These snapshots may reveal a change; they cannot exclude unobserved Windows activity
or establish a cause retrospectively. Keep unavailable readings as failures, never passes.
Telemetry processes must finish before a simulation starts.

Independently verify physical outputs and warnings against the same controls. Use all
five samples per variant. Apply the original rule unchanged: at least 1.05× median
speedup with non-overlapping five-sample ranges at one size, and neither median more
than 3% slower. Report the initial failed campaign and the confirmation separately.
If the confirmation fails, stop this candidate and restore the original helper.
If it passes, retain the change with the first campaign's variability as an explicit
limitation; do not claim that every invocation will achieve its median gain.

Reuse the completed numerical, failure-path, capacity and trace qualification because
source and executables are unchanged. Record that reuse explicitly rather than claiming
fresh tests. The [performance plan](/docs/project/development/performance-plan.md) remains open.
