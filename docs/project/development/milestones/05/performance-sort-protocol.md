# Batched CUDA sort protocol

This experiment follows the [compact-row result](/docs/project/development/milestones/05/performance-compact-neighbours.md)
and the [performance plan](/docs/project/development/milestones/05/performance-plan.md). It tests one change:
submit the existing integer bitonic passes on the same ordered private stream, then complete
the whole sort once. Do not change kernels, pass order, arithmetic, numerical checks,
cancellation polls, copy ordering, membership, observations or timestep work.

## Comparison and verification

Identify both dirty source trees by full file manifests and fingerprints, separately from
their base commit. Build both on the primary PC through `ssh pc`, using locked, offline
release CUDA builds, no custom compiler flags and distinct recorded build revisions.
The control is the reviewed compact-row implementation before batching, not the older bitset.
Record hardware, driver, toolchain, binary, protocol and collector hashes before collection.
Leave ordinary installations, repositories, branches, tags and the parent gitlink untouched.

Before accepting timings, run the complete CUDA-enabled release suite including hardware
checks, strict Clippy, formatting and native ASan/UBSan injected-failure checks. Keep the
three baseline-reproduced automatic-backend CLI failures visible. Test exact integer-key
ordering and padded sentinels against an independent oracle and individually completed passes,
at all four block sizes. Inject a middle-pass submission failure, completion failure and
context-binding failure; check drain, error precedence, poisoning and forbidden reuse.
Existing independent equations, compact rows, dense/extreme inputs, cancellation and retry
tests remain required. Local CPU and parent tooling checks are separate evidence.

## Collection

Use device zero, 128 lanes, eight iterations and factor-four refinement. All work runs
sequentially on the PC; profiling is separate from primary timing. Keep the existing
completed-step timing boundary, including every required check, transfer and synchronisation.

- Run all seven original sizes for 480 steps, with checkpoints 0, 1, 120, 240 and 480:
  one ordinary warm-up and one stage profile of the candidate. Compare every physical
  component exactly, including signed zero, with retained independent serial observations.
- At 8,000 particles run one complete warm-up per variant, then five independent
  observation-rich total-only samples per variant. Alternate control/candidate order,
  reversing the order on even sample numbers. Reject incomplete, warning-bearing or
  numerically different primary samples. Report median, range, sample standard deviation,
  solver and invocation real-time factors, and unchanged per-step distributions.
- Repeat four-step capacity pilots at 8,000, 32,768, 110,592, 262,144 and 512,000 particles
  against fresh serial execution. Use the unchanged counted capacity scenes. Admit using
  the compact protocol's initial-lattice estimate and memory ceilings, not a dense-input
  guarantee. Admit a 480-step diagnostic only when pilot solver time projects to at most
  90 s. Compare its complete physical result, warnings included, with the retained compact
  trajectory. Larger warning-bearing results remain diagnostics, not quality qualification.
- Bound ordinary/long invocations to 120 s plus 30 s cooperative grace; use 30 s plus
  10 s for CUDA pilots. Retain raw output, failures, accepted prefixes and actual exits.
- Collect separate Nsight Systems traces of both variants at 8,000 particles/480 steps,
  without checkpoint audits, and 110,592 particles/four steps. Reconcile launches,
  stream completions, copies/bytes, GPU activity and gaps against each source version.
  At 8,000 particles the expected kernel count stays 145 per step; stream completions
  fall from 226 to 136. Copies and allocation behaviour should not change.

## Decision and retention

Keep batching only with exact agreement, preserved failure semantics and a clear matched
gain. No changed numerical work, final-quality campaign or competitive-PBF claim is included.
An independent reader must recompute primary totals and physical comparisons from raw output;
a deliberately false median must be rejected. Preserve the old evidence unchanged.
Retain commands, monotonic durations, raw failures and the original source/binary identities.
Native profiler reports and unsanitised SQLite remain private; publish only metadata-sanitised
exports with original hashes and analytical-table integrity checks.
