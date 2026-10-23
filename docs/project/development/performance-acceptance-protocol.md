# Host acceptance investigation protocol

Historical collection protocol. Its automatic retention criteria describe the original
decision only; the [reassessment](/docs/project/development/assets/acceptance-review-v1/README.md)
retains the change under the current [assessment policy](/docs/project/development/performance-assessment.md).

Follow the [performance plan](/docs/project/development/performance-plan.md) and
[correction investigation](/docs/project/development/performance-correction-profile.md).
Measure the acceptance components before choosing a runtime change. Preserve every
finite-state, identity and plane check, expression order, error priority, cancellation
boundary and atomic acceptance. Keep GPU kernels and numerical work unchanged.

## Bound the cost first

Use the primary PC through `ssh pc`, isolated source exports and locked offline release
CUDA builds. The starting source includes the retained correction tests and original
power tables. Record complete source, executable, toolchain, input and protocol hashes.
Leave ordinary PC checkouts, installed applications and both repositories' Git state alone.

Build a separately identified diagnostic overlay with monotonic probes around velocity
reconstruction, each final download, particle reconstruction, final particle validation,
ordered plane validation and atomic replacement. Probe once per component per step,
never once per particle. Emit diagnostic records after the measured sections; do not add
these probes or fields to the public measurement format. Preserve the exact overlay patch.

At 8,000 and 110,592 particles run a warm-up and three diagnostic samples each, with
480 steps, refinement four, eight iterations, CUDA device zero/128 lanes, no rendering,
no checkpoint audits and `--unpaced`. Keep ordinary checks inside the solver. Verify
exact physical results and warning schedules against retained controls. Aggregate every
component and solver total separately, including early and evolved windows. These are
instrumented diagnostics, not primary performance samples or interchangeable timings.

Only select a plane-validation candidate if that component occupies at least 10% of the
diagnostic solver median at one size. Inspect generated host code before and after the
change. The bounded candidate is making the existing small `Plane::contains` helper
available for inlining at its callers; keep its body and all subsidiary checks unchanged.
Prefer `#[inline]`; consider stronger guidance only if generated code shows the hot call
boundary remains. Do not specialise for benchmark planes, skip validation, reorder
particles/planes or substitute different floating-point arithmetic.

## Screen before full qualification

Once source identities are frozen, build the uninstrumented control and candidate.
At 110,592/480 without checkpoints, run one warm-up and three alternating samples each,
reversing order on even pairs. Keep all samples. Proceed to the full campaign only for
at least 1.05× median speedup with non-overlapping three-sample ranges and exact physical
agreement. Otherwise retain the diagnostic conclusion without expanding a negligible trial.
The screen does not replace final qualification or enter its five-sample statistics.

## Qualification and retention

Run the full CUDA release suite with opted-in hardware checks, strict Clippy, formatting
and native ASan/UBSan. Reproduce the three known automatic-backend CLI failures in the
control; do not suppress tests. Use existing independent plane, overflow, rollback,
ordering and cancellation checks, adding a case only where a real coverage gap exists.
Run CPU and parent checks separately. Confirm unchanged generated device code.

Keep the seven-size, 480-step regression family, checkpoints 0/1/120/240/480, warm-ups
and separate stage profiles. Collect fresh warm-ups and five alternating total-only
samples each at 8,000 particles and at 110,592 without checkpoints. Retain existing large
CFL warnings exactly. Admit the change only for at least 1.05× median speedup with
non-overlapping five-sample ranges at one size, with neither median regressing by more
than 3%. This is an engineering policy, not a statistical-significance test.

Repeat the five-size capacity ladder with fresh four-step serial/CUDA pilots. Keep the
initial-lattice estimate plus 32 diagnostic bytes, 4 GiB host minimum, and GPU ceiling
of the smallest of 6 GiB, 60% total and free minus 2 GiB. Admit 480-step diagnostics only
below a 90 s pilot projection. Ordinary requests use 120 s plus 30 s grace; CUDA pilots
use 30/10. Run PC profiling, checks and samples sequentially. Keep all failures and skips.

Use separate before/after CUDA timelines and acceptance probes to explain a retained gain.
Never add overlapping GPU and host intervals or claim an isolated function cost from
broken stack samples. Independently reconcile original output hashes, physical results,
timing summaries, the admission decision and unchanged GPU work. Reject false summaries.
Keep native reports private and check sanitised analytical exports. Record source identity
and actual final verification. No hosted, other-platform, device-loss, passing device-memory
sanitiser or independent large-fluid-quality qualification follows from this experiment.
