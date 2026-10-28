# CUDA host orchestration investigation, 28 October 2026

Control is the current 190-file deferred-containment candidate, preserving all
nine retained optimisations, with exact source manifest and patch from Maelstrom
HEAD 1e0085926d05c42949bb76b55d177d42a1f8f94f. Both Git histories/gitlink
remain unchanged. Earlier task outputs are guidance, not new baseline samples.

No system-wide driver settings, registry entries or security permissions may be
modified or removed. Use existing diagnostic tools and read-only availability
checks. Keep existing profiling settings untouched. Record every environmental
change; scoped source exports, builds and process-owned CUDA allocations are
permitted. No reboot, driver reset, service or clock/security reconfiguration.

Measure on the primary PC over ssh pc. Fresh precise compute_89 release PTX must
match the executable, source hashes checked before/after collection. CUDA0,
block128, refinement4, eight Jacobi iterations,480 unpaced steps,no graphics.
8,000 bundled20-cubed block with checkpoints0/1/120/240/480;110,592 counted48-cubed
block with final observations. Also cover both sizes with XSPH.01/confinement.1.
Admission4GiBhost/2GiBGPU. Bound ordinary runs120s,traces240s,qualification600s.

First collect one warm-up plus three ordinary current-control samples per
workload. Collect full-trajectory CUDA/API and separately labelled NVTX/CPU
sampling traces of current retained source. Quantify build/trace overhead with
three alternating ordinary/diagnostic pairs. Derive interval unions and
non-overlapping wall partitions; distinguish GPU execution, required host
numerical/allocation/error/cancellation dependencies, synchronous transfer/API
latency, driver submission and post-submission idle gaps. Correlate enqueue,
copy,completion and consuming host ranges. Do not add overlapping API waits,
GPU work or queue latency. CPU samples/scheduler support attribution; absent
GPU counters do not establish memory-stall hypotheses.

Only choose an implementation after fresh profiling identifies an opportunity.
Optional same-workload process-owned Driver API diagnostics can test a specific
hypothesis, with explicit buffer lifetime/error/completion boundaries and no
system configuration. Up to three focused candidates; one warm-up and two
alternating exploratory pairs per size (effects also if affected). Preserve
all attempts. No approximate arithmetic, new accumulation order, hidden skipped
checks, fixed neighbour cap, or changed error/cancellation/acceptance boundaries.

Before primary timing, qualify focused failure/lifetime tests, full release,
CUDA hardware/boundary/execution checks,strict Clippy,formatting,nativeASan/UBSan,
and exact seven64..8000regressions. Device memory/sync/init/race checks as relevant;
unavailable diagnostics are not passes. Freeze final source,tests,docs and bind
fresh PTX; final performance one warm-up plus five alternating pairs per each
of four workloads, first measured candidate/control. Completed-step time
includes all solver preparation,checks,transfers,submission,completion,cancellation
and acceptance; solver construction/teardown,requested observation copies,output,
audits and storage separate. No other profiling/qualification GPU jobs during
primary samples. Retain warnings,failures and slow samples without replacement.

Collect matched ordinary/diagnostic post-change timelines separately from primary
timing. Record GPU idle partitions,transfer counts/bytes,stream waits,launches,
CPU work,overhead and resources; report regressions and uncertainty. Judge retention
against policy by correctness,consistent application benefit,implementation/lifetime
cost and limits. If not beneficial,revert only the new candidate changes and retain
nine optimisations. Keep raw bounded outputs,commands/exits,monotonic durations,
environment,manifests/patches,privacy-limited activities and independent readers.
Verify source reconstruction,archive integrity and both Git states before handoff.
