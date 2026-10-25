# CUDA multiplier-prefix reuse protocol

Historical collection protocol. Its automatic retention criteria describe this completed
trial only. Future decisions follow the [assessment policy](/docs/project/development/milestones/05/performance-assessment.md).

This implements the next arithmetic investigation in the
[performance plan](/docs/project/development/milestones/05/performance-plan.md), following
[logical-stage batching](/docs/project/development/milestones/05/performance-stage-batching.md).
Test reuse within one unchanged multiplier snapshot, not stale gradients across iterations.

## Candidate and invariants

While computing the owner gradient, accumulate squared neighbour contributions whose
identities precede self. Retain precisely their original additions starting from zero.
Finish all owner checks before publishing any prefix failure, insert self at its original
position, then process higher-identity neighbours in order. Do not combine independently
summed halves or change floating-point association. The suffix still recalculates its
gradients. This partial reuse needs no per-pair cache, allocation, extra kernel or transfer.

Preserve strict current support, fixed prediction membership, self contribution, binary32
expressions, all solver work, cancellation, grouped failure precedence and transactional
acceptance. Verify empty/singleton and warp/block/tail cases, owner-first/middle/last ordering,
inactive prediction neighbours and repeated changed-position snapshots. Independently
constructed overflow cases must distinguish owner failure from earlier-computed prefix
squares, prefix-sum overflow and suffix-square overflow. Use all four supported block sizes.

Run the complete CUDA release suite with opt-in hardware tests and no fail-fast, strict
Clippy, formatting and native ASan/UBSan. Reproduce the known three automatic-backend CLI
failures in the control; do not suppress tests or repair unrelated behaviour. Local CPU and
parent tooling checks remain separate.

## Comparison, before observing results

Freeze complete control/candidate exports, protocol and collector hashes before measurement.
Both retain the same unchanged untracked custom scene, which no request selects. These
exports are not commits. Leave branches, commits, tags, gitlinks, installed applications,
ordinary PC repositories and user edits untouched. Use locked offline release CUDA builds
on the primary PC through `ssh pc`, with explicit source-derived build revisions.

Reuse the preceding collector's exact seven regression sizes, 480 refined steps, eight
iterations, checkpoints 0/1/120/240/480, explicit device zero/128 lanes and `--unpaced`.
Run one warm-up and separate stage profile per size against retained independent serial
observations. Run one untimed warm-up per variant and five alternating total-only samples
each at 8,000 particles, reversing order on even sample numbers. Keep all samples.

Also predeclare a paired 110,592-particle, 480-step, no-checkpoint workload, with one
warm-up per variant and five alternating samples each. Its known CFL warnings must match
the preceding complete trajectory exactly. It is a warning-bearing runtime comparison,
not an independent physical-quality qualification. It prevents a coordination-heavy small
case alone deciding whether a kernel-local improvement is useful.

Retain only if at least one declared size is at least 1.05× faster by median, with
non-overlapping five-sample ranges, and neither median regresses by more than 3%.
Otherwise reject the candidate rather than interpreting noise as a benefit. These are
engineering admission criteria, not a statistical-significance test. No sample is removed.

Repeat the five-size capacity ladder using fresh four-step serial/CUDA pilots and the
unchanged initial-lattice allocation estimate plus 32 diagnostic bytes. Require 4 GiB
available host RAM; GPU ceiling is the smallest of 6 GiB, 60% total and free minus 2 GiB.
Admit complete 480-step diagnostics only below the 90 s pilot projection. Retain original
warnings and exact physical comparisons. This estimate does not bound dense/evolved input.

Bound ordinary requests to 120 s plus 30 s cancellation grace; CUDA pilots use 30/10.
Run all PC checks, measurements and traces sequentially. Profile both variants separately
at 8,000/480 and 110,592/four without observation audits. Both should retain 145 kernels
per 8,000-particle step, 51 completions per step plus one initial reset, 26 device-to-host
copies per step and `56N + 432` copied bytes. Allocation and reset models are unchanged.
Measure the multiplier kernel and whole solver, not just source-level expression counts.

## Evidence and decision

Independently verify raw hashes, exact observations/warnings, timing sums, paired summaries,
admission criteria and trace models. Reject a deliberately false timing summary and decision.
Keep failed attempts and rejected candidates. Publish only sanitised SQLite with analytical
rows verified unchanged; native reports and process environments stay private. Neither
profiles nor warning-bearing capacity results are final-quality benchmarks. No hosted,
other-platform, actual device-loss or passing device-memory-sanitiser claim follows.
