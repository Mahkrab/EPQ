# Compilation attribution and CUDA block-size protocol

The [code audit](/docs/project/development/milestones/05/performance-cuda-code-audit.md) requires a
complete timing boundary before a residency or image-pipeline comparison. Keep its 180-file
source control and retained optimisations. The candidate adds export timing only: no numerical,
neighbour, rendering, publication, frame scheduling or block-size default change.

## Timing contract

Keep the three existing manifest timing fields. Add a versioned `timing_profile` with disjoint
monotonic intervals for setup, solver steps, snapshot capture, comparison, frame particle copying,
graphics/readback, PNG encoding, frame publication, frame hashing, progress work and an explicit
remainder. Its total ends before manifest construction. It cannot include its own manifest's
completed write. Whole-command wall time separately includes CLI resolution, manifest output,
catalogue publication and teardown; their remainder must not be labelled pure file-write time.

Use integer durations internally, require their partition to fit the enclosing duration, and
keep numerical work and all observation hashes unchanged. Existing bundles remain readable.
Measure candidate/control compilation to expose observation overhead rather than assuming zero cost.

## Fixed primary-PC requests

Use separate immutable control/candidate exports, Cargo targets and executables, locked offline
release builds with `cuda,render`, target 89 and precise native arithmetic. Verify identical fresh
CUDA code embedded in both binaries, and source/binary hashes before requests. Leave installed
commands and ordinary PC checkouts alone. Require 4 GiB guest RAM, 2 GiB free GPU memory and
10 GiB free workspace storage before collection. Bound headless requests to 120 seconds and
compilation to 240 seconds, each with 30 seconds cancellation grace. Retain every failure and
stop an incomplete comparison rather than silently replacing samples.

Headless requests use the same candidate executable at block sizes 32/64/128/256. All run 480
unpaced steps, refinement 4, eight iterations and CUDA device zero. Use the existing 8,000-particle
fixture with checkpoints 0/1/120/240/480, the 110,592-particle capacity scene without checkpoints,
and that large scene with XSPH 0.01 and confinement 0.1 m/s. Each setting receives one warm-up and
three measured samples. Rotate block order by round; compare exact physical results while allowing
only declared resource identity differences. Report every total and range; do not infer a default
from one fastest sample or combine these timings with earlier campaigns.

Compile the large disabled-effect scene for all 480 steps at 1280×720, a fitted camera, fixed
default colours and hardware graphics. Compare blocks 128/256 at strides 1/4 (481/121 images).
Each combination receives a warm-up and three measured requests in rotated order. Include the
control at block 128/stride 1 in those rounds for a matched timing-overhead comparison. Compile
is unpaced by design. Record the actual graphics adapter; reject CPU graphics instead of silently
substituting software. Retain the known numerical warnings as warnings, not quality approval.

Require successful bundle validation, exact accepted-diagnostic agreement, identical resolved
inputs, and matching hashes at common frame steps across blocks, strides and source variants.
Retain manifests, frame file hashes and validation outcomes; original PNGs stay in the isolated
PC workspace. Bound resource use without modifying or deleting existing user runs.

## Verification and interpretation

Run the candidate's release suite, explicit CUDA library/application checks, software export
failure/compatibility checks, strict Clippy and formatting. Add deterministic tests for malformed
timing profiles and incorrect accounting; use a separate reader to reconstruct raw totals and
reject altered physical/frame/timing summaries. Keep local parser tests distinct from PC checks.

Report solver-only block-size effects separately from complete compile time and the disjoint
export breakdown. Whole-command cost owns CLI/setup/finalisation; graphics/readback includes CPU
packing and driver waits, not isolated device rendering. Make a documented next decision from
the measurements, uncertainty and implementation cost. This stage neither implements residency
nor claims a pipeline speedup. No Git checkpoint or publication is authorised.
