# CUDA reused-reservation protocol

Historical collection protocol. Its automatic retention criteria describe this completed
trial only. Future decisions follow the [assessment policy](/docs/project/development/milestones/05/performance-assessment.md).

Follow the [performance plan](/docs/project/development/milestones/05/performance-plan.md) after the
[rejected gradient-prefix trial](/docs/project/development/milestones/05/performance-gradient-reuse.md).
Test one host-coordination change: return immediately when an already validated device
reservation fits its retained capacity. Keep the original multiplier implementation.

## Boundary and verification

Check poisoned handles, slot/action validity, addressable sizes and transfer arguments
before the fast path. A fitting reservation must not allocate, free, transfer, push/pop
a context or wait on a stream. Actual growth and all transfers, including empty transfers,
retain their existing driver completion, error precedence and poisoning behaviour.

Every driver operation already drains its stream before returning. A host-only reservation
therefore introduces no unfinished work. It ceases to be an additional device-health probe:
a fault that becomes observable after the preceding completed call is detected by the next
real driver operation, rather than an otherwise redundant reservation. Already poisoned
resources must still fail immediately. Do not claim recovery from actual device loss.
Preserve numerical expressions, stage order, cancellation and accepted-state ownership.

Use injected-driver cases for zero/subcapacity/exact reservations across all 14 slots,
unchanged pointers and contents, invalid inputs, poisoned handles, allocation exhaustion
and retry, real growth, and unchanged transfer faults. Prove the no-driver-call assertion
fails against the original bridge. Run native ASan/UBSan, the complete CUDA release suite
with hardware cases, strict Clippy and formatting. Retain and reproduce the three known
automatic-backend CLI failures in the control. Run CPU and parent checks separately.

## Comparison fixed before collection

Use isolated source exports and locked offline release CUDA builds on the primary PC
through `ssh pc`. Freeze source, binary, collector and this protocol before measurements.
Keep the same unrelated custom scene in both exports without selecting it. Dirty exports
are not Git checkpoints; ordinary checkouts, installed applications and Git state stay put.

Reuse the seven regression sizes, 480 refined steps, eight iterations, device zero/128
lanes, `--unpaced` and checkpoints 0/1/120/240/480. Warm up and stage-profile the candidate
against retained independent serial observations. At 8,000 particles, warm up both variants
and collect five total-only samples each, alternating order and reversing it on even pairs.
Also collect one warm-up and five alternating samples each at 110,592 particles/480 steps
without checkpoints. Retain its existing CFL warnings exactly; this larger timing case
is not independent physical-quality qualification. Keep every sample.

Apply the preceding trial's prospective policy: retain only a median gain of at least
1.05× with non-overlapping five-sample ranges at one declared size, with neither median
regressing by more than 3%. Otherwise restore the original runtime implementation and
retain the rejected candidate and evidence. This engineering rule is not a significance test.

Repeat the five-size capacity ladder with fresh four-step serial/CUDA pilots. Preserve
the initial-lattice allocation estimate plus 32 diagnostic bytes, 4 GiB host minimum,
and GPU ceiling of the smallest of 6 GiB, 60% total and free minus 2 GiB. Admit complete
480-step diagnostics only below the 90 s pilot projection. Compare complete physical
results and warnings with retained PC controls. Bounds do not cover dense/evolved input.
Ordinary requests remain bounded to 120 s plus 30 s grace; CUDA pilots use 30/10.

Run PC verification, measurements and profiling sequentially. Collect separate Nsight
Systems traces for both variants at 8,000/480 and 110,592/four without checkpoint audits.
Kernels, copies, bytes and allocation sizes should be unchanged. There are 19 reservation
requests per step in these nonempty box scenes; each real growth still needs completion.
Predict candidate waits from the control model minus `19 × steps`, plus actual growth
calls. The initial diagnostic allocation is not a reservation. Reconcile the trace rather
than treating an estimated wait reduction as measured speedup.

Independently check raw output hashes, physical results, warnings, timing sums and the
retention decision; reject false timing and decision summaries. Publish sanitised SQLite
only with analytical rows verified unchanged. Keep original reports and private process
metadata outside the repository. Missing PC access leaves qualification pending; local
tests or laptop timings cannot replace these measurements. No hosted, other-platform,
final-quality or passing device-memory-sanitiser claim follows.
