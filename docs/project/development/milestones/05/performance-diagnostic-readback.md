# Compact CUDA diagnostic readback

The [sort-batching result](/docs/project/development/milestones/05/performance-sort-batching.md) left
136 explicit waits and 58 device-to-host copies per 8,000-particle step. Of those
copies, 53 returned complete error arrays so the CPU could find the first non-zero
entry. This experiment targets that traffic and its second completion boundary,
not the numerical checks themselves. The
[protocol](/docs/project/development/milestones/05/performance-diagnostic-protocol.md) owns the comparison.

## Implementation and the rejected approach

The first candidate added a separate integer reduction kernel after each numerical
pass. Its five paired samples gave median solver times of 2.863 s for the control
and 2.869 s for the candidate: no useful improvement. Smaller transfers alone were
not enough to justify keeping it. Its later profiles were started before the final
capacity collection finished; those profile and associated capacity timings are
excluded. Original observations and failed checks remain evidence, not qualified gains.

The revised implementation lets failing numerical lanes update one packed 64-bit
record with an integer atomic minimum. The high word is the particle index; the low
word retains that particle's first checked quantity. The all-ones sentinel means no
failure. Atomic minimum supplies an indivisible integer selection, not a floating-point
reduction or a change to the fluid equations.<sup><a href="#ref-s012">S012</a></sup>

Each numerical pass still completes and is inspected before the next begins, preserving
stage, particle and expression precedence. Successful passes leave the sentinel untouched.
The native owner resets it for the first attempt and after a numerical failure, and
rejects further checked work until that reset succeeds. A driver fault poisons the
resource; the cached clear-state flag cannot bypass that rejection. Every attempt still
reloads accepted physical state, and cancellation polls and atomic acceptance are unchanged.

One eight-byte readback follows kernel completion. A synchronous device-to-host copy
finishes before returning, so it needs no second explicit wait.<sup><a href="#ref-s053">S053</a></sup>
Reset submission is itself completed and checked. Rust rejects malformed particle or
quantity fields at the native boundary. There is no new dependency, capped neighbour
count, changed arithmetic, reduced solver work or extra reduction kernel.

## Matched PC result

Both variants used locked release CUDA builds on the primary RTX 4070/Ryzen 9 7900X
PC, with device zero and 128 lanes. The first five alternating, independent samples
retained 8,000 particles, 480 refined steps, eight iterations and the original observation
schedule. Their medians were 2.840 s for the control and 2.738 s for the candidate.
One candidate sample was slower, so a separately recorded confirmation policy declared
five further pairs before collecting them. Their medians were 2.829 and 2.707 s.

All ten samples per variant give this descriptive summary, without dropping outliers:

| Error readback | Median solver time | Minimum–maximum |
| --- | --- | --- |
| Complete per-particle arrays | 2.839 s | 2.816–3.085 s |
| Packed first error | 2.714 s | 2.658–2.959 s |

That is **1.046× faster**, or about **4.4% less solver time**: a modest improvement,
not a solution to the overall performance gap. Both batches remain separately visible;
no significance claim or comparison with earlier campaigns' timings is made.

The [retained evidence](/docs/project/development/assets/diagnostic-readback-v1/README.md)
identifies both dirty source exports from base Maelstrom
[`a21d961a27706e2aa434f20100e9cbbf8ae747e6`](https://github.com/Mahkrab/Maelstrom/tree/a21d961a27706e2aa434f20100e9cbbf8ae747e6).
The candidate fingerprint is `8a89dbe1c89c429a31c97cf3ad8a6482ccc944f97a3c001899e8885399006fbc`;
the control is `37c5d6e64e8e578700b88261754f7485eee29fd0167907044799b7f66e63da2a`.
These are source-manifest hashes, not commits. Both include the same untouched user
scene, which is not a measurement input.

Separate 8,000-particle traces retained 69,600 kernels and 27,840 device-to-host copies.
Transferred bytes fell from 1,029,123,840 to 215,247,360, about 79.1% less. Explicit
completions fell from 65,280 to 39,841: 53 fewer per step, plus one initial reset.
The tracked allocation peak increased by exactly eight bytes, to 3,069,888 bytes.
The candidate still had 1.907 s of gaps in its 2.829 s traced window; these are not
all removable overhead or primary timing. No complete driver/context-memory claim follows.

## Verification and remaining limits

New hardware cases cover single particles, warp/block/tail boundaries, all four supported
block sizes, competing quantity codes and clearing failures before retry. In particular,
an earlier particle's later expression must beat a later particle's earlier expression.
Host-independent checks reject malformed packed records. Native ASan/UBSan cases inject
allocation, reset, launch, completion, readback and context failures, including combined
reset/completion failure, forbidden reuse and skipping resets only after known success.
Existing independent equations, dense/extreme membership, whole trajectories, cancellation
and accepted-state retry checks remain enabled.

The PC release suite passed 253 checks, with the same three pre-existing automatic-
backend CLI failures still open. Strict CUDA Clippy and native sanitiser checks passed.
The local CPU release suite passed 239 checks, and the parent experiment suite passed
25. Early test-build errors were corrected rather than suppressed; their raw failures
are retained separately from the passing reruns. Neither injected faults nor ordinary
hardware tests qualify actual device-loss recovery or a passing device-memory sanitiser.

All seven regression scenes and both timing batches agreed exactly with retained serial
observations. Five fresh four-step serial/CUDA capacity pilots matched, as did all five
complete capacity trajectories against the previous implementation. At 32,768, 110,592,
262,144 and 512,000 particles the single diagnostic solver times were 5.02, 13.48, 30.36
and 60.58 s, with the same 75, 259, 300 and 304 warning steps. These are not paired
large-scene speedups or independent density qualification.

This remains implementation optimisation, not competitive-quality qualification or final
evaluation. Keep the revised implementation for its checked, modest runtime gain and
lower diagnostic traffic. Large-scene CFL warnings and absent independent density qualification are
not removed by making diagnostics cheaper. Installed applications, ordinary PC checkouts,
user scene/configuration edits, branches, commits, tags and the parent gitlink are untouched.

## References used

<a name="ref-s012"></a> **S012** — NVIDIA, *CUDA Programming Guide*, Release 13.2, §10.14.1.4.
[Source record](/docs/research/sources/012-nvidia-cuda-programming-guide-release-13-2.md).

<a name="ref-s053"></a> **S053** — NVIDIA, *CUDA Driver API* v13.3, copy synchronisation and memory initialisation.
[Source record](/docs/research/sources/053-nvidia-cuda-driver-api.md).
