# CUDA logical-stage batching protocol

Follow the [performance plan](/docs/project/development/performance-plan.md) and
[diagnostic-readback result](/docs/project/development/performance-diagnostic-readback.md).
Test one change against that complete, uncommitted implementation: submit each four-pass
Jacobi calculation and each candidate/projection pair without intermediate host waits.
Keep all kernels, numerical expressions, configured work and cancellation polls unchanged.

## Dependencies and failure policy

Give each pass a separate eight-byte first-error slot, increasing persistent diagnostic
storage from eight to 32 bytes. Kernels inspect only earlier completed passes' slots;
they skip their work after a numerical failure. Read the group's slots once and select
the first failed stage, then its first particle/expression. Do not combine those priorities
with a minimum across stages. Reset every slot on the first attempt and after failure.

Preserve whole-snapshot Jacobi dependencies, ordered planes, accepted-state ownership,
retry, context restoration and cancellation boundaries. Submit only the two fixed groups.
Stop after an immediate submission failure, drain outstanding work and poison uncertain
resources. A driver/completion/readback/context failure prevents trusting any numerical
record, including when a prior pass already failed numerically. Explicitly test this
combined-fault case: batching does not promise an earlier host observation before a later
driver fault. Such faults never publish partial state or permit resource reuse.

Use existing injected-driver tests plus hardware cases for every pass, stage-before-particle
priority, skipped writes, clearing failures and reusing the resource. Include singleton,
warp/block/tail sizes and all four supported block sizes. Run the full CUDA release suite
including opted-in hardware checks, strict Clippy and native ASan/UBSan. Keep the three
known automatic-backend CLI failures visible and reproduce them in the control; do not
suppress or repair unrelated failures. Local CPU/tooling verification remains separate.

## Frozen comparison and collection

Use separate complete source exports and locked offline release CUDA builds on the primary
PC through `ssh pc`, with explicit build revisions and source/binary/protocol/collector hashes.
Both exports retain the same unchanged custom user scene, which no benchmark selects.
Neither dirty export is a Git checkpoint. Do not change installed applications, normal PC
checkouts, branches, tags, commits, gitlinks or the user's unrelated edits.

Reuse the preceding collector's exact seven-size, 480-step, refinement-four, eight-iteration
requests and checkpoints 0/1/120/240/480. Select CUDA device zero, 128 lanes, `--unpaced`,
without rendering. Run one candidate warm-up and a separate stage profile per size against
retained independent serial observations. At 8,000 particles run one warm-up per variant,
then five total-only samples each, alternating order and reversing it on even sample numbers.
Keep all samples and report medians, spread, per-step distribution and real-time factors.
Reject incomplete, warning-bearing or physically different primary samples.

Repeat the unchanged five-size capacity ladder with fresh four-step serial/CUDA pilots.
Use the initial-lattice estimate plus 32 diagnostic bytes, at least 4 GiB available host
RAM, and a GPU ceiling of the smallest of 6 GiB, 60% total memory and free memory minus
2 GiB. This is not a bound for dense/evolved input. Admit a 480-step diagnostic only when
the pilot projects to at most 90 s; compare complete trajectories and warnings with the
preceding diagnostic implementation. Larger warning-bearing runs are not quality claims.

Bound requests to 120 s plus 30 s cooperative grace; CUDA pilots use 30/10. Retain failures,
exits and accepted prefixes. Run PC checks, collection and profiling sequentially, never
overlapping. Profile both variants separately at 8,000 particles/480 steps and 110,592/four
steps without checkpoint audits. For 8,000 particles expect the same 145 kernels per step,
explicit completions falling from 83 to 51 per step plus one initial reset, and device-to-host
copies falling from 58 to 26 per step. Bytes remain `56N + 432` per step: batching changes
the number of calls, not the diagnostics collected. Reset 32 instead of eight bytes once
per clean invocation. Measure net runtime, not only the removed waits.

## Acceptance and evidence

Retain only a clear matched runtime benefit with exact physical agreement and the tested
failure policy. Reject noise-level changes or regressions. Keep all ordinary checking,
submission, transfer and synchronisation inside the solver boundary; profiles are not primary
timings. Independently reconcile raw output hashes, physical documents, timing summaries and
trace call/byte counts. Reject a deliberately false median. Publish metadata-sanitised SQLite
only after checking analytical rows unchanged, and keep original/native profiles privately.
No numerical tuning, competitive-quality qualification, final evaluation, actual device-loss
recovery, passing device-memory sanitiser or hosted verification follows from this experiment.
