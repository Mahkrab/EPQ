# Compact CUDA neighbour rows

This is the first implementation experiment in the
[performance plan](/docs/project/development/performance-plan.md), following the retained
[diagnosis](/docs/project/development/performance-diagnosis.md). It replaces the CUDA membership
matrix without changing the numerical work. The comparison is governed by the
[experiment protocol](/docs/project/development/performance-compact-protocol.md).

## Implementation and decisions

The device now counts prediction-time neighbours before allocating contiguous index storage.
Checked 64-bit host prefixes define each row; a second device pass fills it and heapsorts its
indices into ascending identity order. This avoids scanning empty matrix words in every iteration.
Each row still excludes self. The density and squared-direction traversals insert self exactly
once at its identity-ordered position, and current-distance filtering retains the strict support
test. Prediction membership stays fixed throughout the configured Jacobi iterations.

Rows have no fixed neighbour limit. Checked allocations can fail, but dense input is never
silently truncated. Index storage grows geometrically and is reused; offsets and row contents
are rebuilt on retry and on the next timestep. Numerical expressions, precision, artificial
pressure, projection, cancellation polls and atomic acceptance are unchanged. All additional
counting, host-prefix work, transfers, filling and sorting remain inside solver/search timing.

### A correctness problem found by the larger cases

The first candidate matched all seven existing workloads, then failed counting/filling checks
in capacity runs. A new 32³/48³ lattice test reproduced the problem against independently built
CPU grid rows. Inspection found that pageable host uploads could finish staging before their
device copy completed. The private non-blocking kernel stream did not inherit that copy's
legacy-stream dependency, so it could read incomplete offsets. CUDA documents both behaviours.<sup><a href="#ref-s053">S053</a></sup>

The repair keeps an isolated context and private stream but enables legacy-copy ordering.
The reproducing test then passed. Both the bitset control and compact candidate receive this
same repair for the final storage comparison; otherwise its timing effect would be conflated
with compaction. No explicit stage completion was removed. Rejected results and the earlier
protocol remain evidence of the failed candidate, not qualified performance results.

## Measurements and verification

The [retained evidence](/docs/project/development/assets/compact-neighbours-v1/README.md) identifies
the uncommitted candidate by its complete source manifest, based on Maelstrom
`c17d8c586eba7455582ad9597cb23d7addc3c6d9`. Its tree fingerprint is
`975e6bb0b26e024314974a99b14e69bca35068eb079d35b0f64713fe631ece0e`, not a Git commit.
The evidence separately identifies a final, documentation-only Rustdoc correction; executable
source and tests are otherwise unchanged from that measured tree.
The bitset control differs from that base only in the stream flag. Both used locked release
CUDA builds on the primary RTX 4070/Ryzen 9 7900X PC, with device zero and 128 lanes.

At 8,000 particles and 480 refined steps, five alternating samples gave:

| Storage | Median solver time | Minimum–maximum |
| --- | --- | --- |
| Bitset, with copy-ordering repair | 8.058 s | 8.033–8.075 s |
| Compact rows, with the same repair | 4.057 s | 4.052–4.076 s |

That is a **1.99× solver speedup**, with unchanged observations and approximately one simulated
second of work. The candidate solver real-time factor is about 0.246, still below real time.
Every original size matched the retained serial observations in ordinary and profiled runs.
An independent reader checked all 26 observation-rich comparisons, five fresh serial/CUDA
capacity-pilot comparisons and the five finite, plane-compliant capacity endpoints.

Separate traces measured these allocation peaks, including transient growth and module constants:

| Workload | Bitset | Compact rows |
| --- | --- | --- |
| 8,000 particles, 480 steps | 8.97 MB | 3.07 MB |
| 110,592 particles, four steps | 1,542.75 MB | 26.78 MB |

These are tracked allocations, not total driver/context memory. At 110,592 particles the measured
peak is about 57.6 times smaller. Dense all-neighbour input can still require quadratic storage.

The 32,768, 110,592, 262,144 and 512,000 cases completed 480 steps in 7.26, 18.25, 39.29 and
75.57 s, respectively, but produced 75, 259, 300 and 304 CFL warnings. These single diagnostics
show that the previous allocation/time barriers moved; they are not clean-quality benchmarks,
maximum-capacity results or proof of the 100k-plus real-time ambition. Their four-step pilots
agreed exactly with independent serial execution. Larger full trajectories lack density qualification.

On the PC, 250 feature-enabled Rust checks passed, including opt-in hardware checks; three CLI
tests failed on both the original baseline and the candidate because they assume automatic
selection returns serial metadata on a CUDA-capable machine. They remain open, with raw failures
retained. The local CPU release suite passed 239 checks. Strict Clippy, formatting and native
ASan/UBSan injected-failure checks passed; the parent experiment suite passed 18 tests.
No hosted or passing device-memory-sanitiser result is claimed.

## Decision and next limit

Keep compact rows: they have independently checked numerical agreement, a measured runtime gain
and a substantial measured storage benefit. The new counting/filling transfers are included, not
hidden: each 8,000-particle step now has 145 launches and 226 explicit stream completions, versus
144 and 219 for the bitset control.

In matched 480-step traces, density/multiplier device time fell from 2.636 to 0.203 s, while
counting plus filling/sorting cost 0.299 s. GPU activity occupied 1.078 s of the candidate's
4.292 s traced window; gaps occupied 3.213 s, or 74.9%. Those gaps are not all automatically
removable. The 91 bitonic passes still account for 1.311 s of launch-to-next-launch time despite
only 0.075 s of device work. Host/device submission and round trips are the next justified target;
retain the newly established copy dependency when changing that boundary.

This completes the storage experiment, not the whole optimisation track or final evaluation.
No numerical tuning, dependency, golden, commit, tag, branch, push or parent gitlink changed.

## References used

<a name="ref-s053"></a> **S053** — NVIDIA, *CUDA Driver API* v13.3, API and stream synchronisation behaviour.
[Source record](/docs/research/sources/053-nvidia-cuda-driver-api.md).
