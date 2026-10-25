# CUDA diagnostic-readback protocol

This follows the [sort-batching result](/docs/project/development/milestones/05/performance-sort-batching.md)
under the [performance plan](/docs/project/development/milestones/05/performance-plan.md). Test one bounded
change: select the first checked particle error on the device and copy one packed 64-bit
record. Failing numerical lanes apply an integer atomic minimum; successful lanes leave
the success sentinel untouched. Keep numerical expressions,
per-particle checks, stage/identity/expression precedence, copy ordering, cancellation,
Jacobi dependencies, failure isolation, retry and atomic acceptance unchanged.

## Implementations and verification

Use separate frozen source exports and locked, offline release CUDA builds on the primary
PC through `ssh pc`. Record complete source manifests, binary/build identities, compiler,
toolkit, driver, hardware, protocol and collector hashes. Both exports include the same
unchanged, uncommitted user scene; it is not a measurement input. Preserve that scene and
the user's parent `.gitignore` edit. Neither export is a historical Git checkpoint.
Do not change installed applications, ordinary PC repositories, branches, tags or gitlinks.

Run the complete CUDA release suite including opt-in hardware cases, strict Clippy,
formatting and native ASan/UBSan injected-failure checks. Keep the known three automatic-
backend CLI failures visible and reproduce them in the control. Local CPU/tooling tests
remain separate. Check empty/singleton input, warp/block/tail boundaries, all four block
sizes, competing particle/quantity errors, stale-failure clearing and malformed packed
records. Inject numerical-launch, reset-submission, completion, readback, allocation and
context failures, including combined reset/completion failure. Verify drain, error
precedence, poisoning, no forbidden reuse and existing cancellation/numerical retry behaviour.

## Matched collection

Reuse the sort protocol's exact seven-size, 480-step, refinement-four, eight-iteration
regression requests with checkpoints 0/1/120/240/480. Use explicit CUDA device zero,
128 lanes, `--unpaced` and no rendering. Run one ordinary candidate warm-up and one
separate stage profile per size against retained independent serial observations.

At 8,000 particles, run one complete warm-up per variant and five independent total-only
samples each, alternating order and reversing it on even sample numbers. Reject incomplete,
warning-bearing or physically different primary samples. Retain all samples, variability,
per-step distributions, construction/teardown, invocation and real-time factors. Keep
all required reduction work, transfer and synchronisation inside solver/search timing.
Do not pool historical timing samples into the fresh comparison.

Repeat the five unchanged capacity sizes with fresh four-step serial/CUDA pilots. Use
the compact initial-lattice memory estimate plus eight bytes for the persistent result,
at least 4 GiB available guest RAM, and the smallest GPU ceiling of 6 GiB, 60% total
memory and free memory minus 2 GiB. This is not a dense-input guarantee. Admit a 480-step
diagnostic only if the pilot projects to at most 90 s. Compare complete physical results
and warnings with the retained batched-sort trajectories. Larger warning-bearing cases
remain diagnostics without independent density qualification.

Bound ordinary/long requests to 120 s plus 30 s cooperative grace; CUDA pilots use 30/10.
Retain failures, partial output, accepted prefixes and actual exits. Run measurements
sequentially on the PC. Collect separate Nsight CUDA/memory traces of both variants at
8,000 particles/480 steps and 110,592 particles/four steps, without checkpoint audits.
For 8,000 particles, expect 53 fewer explicit completions (136 to 83), unchanged copy counts, and device-to-host
bytes falling from `268N + 8` to `56N + 432` per step. The revised candidate adds no
reduction launches: kernel count stays 145 per step. Reset the record once at the first
attempt and after a numerical failure, not between successful passes. A clean trace
therefore has one additional reset/completion per invocation. Measure the net cost,
including that reset, and the eight-byte construction-time allocation separately.

## Revision before the final comparison

The first candidate used a separate reduction kernel after each numerical pass. Its
five sequential 8,000-particle samples gave medians of 2.863 s for the control and
2.869 s for the candidate: no meaningful improvement. Retain that failed experiment
and its original protocol separately. Its later profiling overlapped the final capacity
collection and is not admitted timing evidence. The revised `diagnostic-atomic-v1`
comparison uses fresh samples of both variants; do not pool the earlier timings.

## Acceptance and evidence

Keep the change only with exact physical agreement, preserved tested failure policy and
a clear matched runtime benefit. Reject or revise it if extra kernel cost cancels the
saving. Numerical tuning and competitive-quality/final-evaluation claims remain out of scope.
An independent raw reader must reconcile timing totals, exact physical documents and
capacity decisions; reject a deliberately false median. Reconcile profiles with their
source-specific launch/completion/copy models. Retain original commands, hashes, failures
and source identities. Publish only metadata-sanitised SQLite; keep native profiles and
original exports private and verify all analytical rows unchanged after sanitisation.
