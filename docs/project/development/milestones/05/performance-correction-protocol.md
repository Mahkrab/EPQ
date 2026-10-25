# CUDA correction diagnosis and power-table protocol

Historical collection protocol. Its automatic retention criteria describe this completed
trial only. Future decisions follow the [assessment policy](/docs/project/development/milestones/05/performance-assessment.md).

Follow the [performance plan](/docs/project/development/milestones/05/performance-plan.md) after the
[rejected reservation trial](/docs/project/development/milestones/05/performance-reservation-reuse.md).
Diagnose substantial correction and coordination costs before selecting one implementation
change. Keep precision, powers, expression order, support, neighbours, eight iterations,
timesteps, cancellation and transactional acceptance unchanged.

## Diagnosis before selecting the candidate

Use the primary PC through `ssh pc`. Verify the existing control's complete source and
executable hashes; it contains the original implementation and the retained numerical tests.
Keep its installed application and normal checkouts untouched. Copy the existing counted
110,592-particle input and numerical configuration without changing them.

Collect a separate full 480-step Nsight Systems CUDA timeline without checkpoint audits,
using refinement four, device zero/128 lanes and `--unpaced`. Check physical output against
the retained control. Attribute steps 1–120, 121–240 and 241–480 separately, including
kernel durations, copies, API waits and the union of device activity. Kernel-boundary
windows include host work between launches; they are not exact solver-timer boundaries.
Call the last window evolved/post-contact, not proof of a fully settled fluid.

Check installed Nsight Compute versions, sections and actual counter access. Request
launch, occupancy, compute, instruction, memory and warp-state sections for the first
and last correction iteration at steps 1 and 241. Derive each launch index from the
unchanged kernel sequence, and verify that sequence against the full timeline. Keep
cache and clock control disabled. Bound each collection to 120 s plus 30 s grace.
Retain any permission, debugger or unsupported-counter failure; do not change security,
drivers or system settings. Stop further counter attempts after an access failure.

Collect a separate bounded user-space CPU sampling run if the installed profiler permits
it. Keep failure or lost-sample information. Host packing/allocation attribution remains
unresolved when samples cannot support it; a timeline gap alone does not identify its cause.
Inspect generated PTX alongside source. Static instruction counts are not runtime cost.
No diagnostic configuration, counter replay or instrumented run enters primary timings.

The bounded implementation candidate is changing only the two immutable power tables
from constant memory to read-only global storage. Consider it only if correction remains
a material cost and generated code confirms a different table access path. Preserve all
table bits and the entire power approximation. Counter evidence should distinguish
arithmetic and memory pressure where available; missing counters prevent claiming that
power alone or constant-memory serialisation explains the kernel's cost. A matched trial
can establish the benefit of placement without establishing either broader explanation.

## Candidate verification and comparison

Freeze separate complete source exports, executable hashes, this protocol and collector
before timing. Dirty exports are not Git checkpoints. Retain the unchanged custom scene
in both exports without selecting it. No commits, tags, branches, gitlinks or installed
applications are changed by this experiment.

Add an opt-in hardware correction check with divergent neighbour distances and varied
positive exponents, inactive fixed neighbours and all four block sizes. Derive expected
corrections through the independent ordered CPU path; keep binary64 equation checks and
the complete existing failure, retry and cancellation suite. Run the full CUDA release
suite with hardware cases, strict Clippy, formatting and native ASan/UBSan. Reproduce the
three known automatic-backend CLI failures in the control without suppressing them.

Retain the seven-size, 480-step regression family with checkpoints 0/1/120/240/480,
one candidate warm-up and separate stage profile per size. At 8,000 particles collect
one warm-up and five alternating total-only samples per variant. Also collect a warm-up
and five alternating samples each at 110,592/480 without checkpoint audits. Keep its
existing CFL warnings exactly. Reverse pair order on even samples and keep every sample.

Retain only a median speedup of at least 1.05× with non-overlapping five-sample ranges
at one declared size, with neither median regressing by more than 3%. Otherwise restore
the original implementation and preserve the rejected patch and evidence. This is an
engineering admission rule, not a statistical-significance claim.

Repeat the five-size capacity ladder with fresh four-step serial/CUDA pilots. Keep the
initial-lattice estimate plus 32 diagnostic bytes, at least 4 GiB available host memory,
and a GPU ceiling of the smallest of 6 GiB, 60% total and free minus 2 GiB. Admit complete
480-step diagnostics only below a 90 s pilot projection. Requests use 120/30 s bounds;
CUDA pilots use 30/10. Larger warning-bearing runs remain capacity diagnostics.

Run PC tests, measurements and profiles sequentially. Profile both variants separately
at 8,000/480 and 110,592/four, plus full 110,592/480 timelines for early/evolved comparison.
Kernel, completion, copy and scratch-allocation models should remain unchanged. Account
separately for any table-storage difference; do not silently present an old estimate as
measured total device memory. Check exact physical outputs, independently recompute
timings and the retention decision, and reject false summaries.

Retain raw commands, outcomes, environment and integrity records, including failed tools.
Keep native profiler reports privately. Publish sanitised analytical exports only with
their integrity and scope checked. No hosted, device-loss, passing device-memory-sanitiser,
other-platform or independently qualified large-fluid result follows.
