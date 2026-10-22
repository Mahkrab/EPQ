# Batched CUDA cell sorting

The [compact-neighbour experiment](/docs/project/development/performance-compact-neighbours.md)
removed the first storage limit, but its trace still showed 91 small [bitonic](https://en.wikipedia.org/wiki/Bitonic_sorter) passes per
8,000-particle step. They used 0.075 s of device work across 480 steps, yet occupied
1.311 s of launch-to-next-launch intervals. That justified testing submission overhead
before changing either the sorting algorithm or the fluid arithmetic. The
[protocol](/docs/project/development/performance-sort-protocol.md) defines this experiment.

## What changed

The native bridge now submits the complete existing sort network on its private stream,
then waits once. It launches the same kernels, in the same span/stride order, with the
same padding, comparison rule and stable identity tie-break. There is no new dependency,
graph, fused kernel, floating-point expression or storage layout.

Stream ordering supplies the dependency between passes. Launch parameters are copied
from their host storage, rather than borrowed until kernel execution. Submission can
also report earlier asynchronous errors, so it cannot establish successful completion.<sup><a href="#ref-s053">S053</a></sup>
The bridge stops at an immediate submission failure, drains outstanding work, preserves
completion/context-error precedence and poisons uncertain resources. Accepted host state
remains untouched. Integer sort passes had no numerical error inspection or cancellation
poll between them; all existing numerical checks and cooperative cancellation boundaries
remain where they were. The preceding pageable-copy ordering repair is retained.

## Matched PC results

Both variants were built separately on the primary RTX 4070/Ryzen 9 7900X PC with locked,
offline release CUDA builds, device zero and 128 lanes. Five alternating samples retained
8,000 particles, 480 refined timesteps, eight iterations and the original observation schedule:

| Submission | Median solver time | Minimum–maximum |
| --- | --- | --- |
| Individually completed passes | 4.719 s | 4.716–4.946 s |
| Batched passes | 3.256 s | 3.225–3.521 s |

This is a **1.45× speedup**, or about 31% less solver time, without reducing solver work.
These are fresh paired samples; the previous experiment's 4.057 s median is not their
control. Variability and all original samples are retained, not filtered as outliers.

The [evidence collection](/docs/project/development/assets/sort-batch-v1/README.md) identifies
both uncommitted trees from Maelstrom base `c17d8c586eba7455582ad9597cb23d7addc3c6d9`.
The control fingerprint is `c65cf1720cbb125f70528eed460f1f63f904dada8480369adf43080ef7fd6b4f`;
the candidate is `90d5223aa255e904b95363afaf023b191cbfea1b01276841ad34bf5520fd2d90`.
These are source-manifest SHA-256 values, not commits. Only the host bridge, Rust sort
orchestration, their tests and the CUDA guide differ. Device source is unchanged, and
both builds produced byte-identical PTX device code.

Four separate traces checked both variants at 8,000 particles/480 steps and 110,592
particles/four steps. They are profiling evidence, not primary timing samples.
At 8,000 particles, both retained 69,600 kernel launches; explicit stream completions
fell from 108,480 to 65,280, exactly 90 fewer per step. Copy counts/bytes and the
3,069,880-byte tracked allocation peak were unchanged. The candidate trace contained
1.000 s of GPU activity in a 3.368 s window, leaving 2.368 s of gaps. These gaps are
not all automatically removable, but submission/diagnostic overhead remains worth
investigating. At 110,592 particles the four-step tracked peak stayed 26,781,000 bytes.
The sort's launch-to-next-launch intervals fell from 1.528 to 0.193 s in the matched
480-step traces; asynchronous submission did not remove any of its 43,680 passes.

## Verification and limits

All seven original scenes matched retained independent serial observations in ordinary
and stage-profiled runs. The paired samples also matched exactly, including signed zero,
warnings, audits and accepted snapshots. A new hardware test checked integral cell keys,
duplicate-key identity order and padded sentinels against an independent oracle and the
individually completed passes, at 32, 64, 128 and 256 lanes. Existing dense/extreme rows,
large lattices, equation, cancellation and retry checks remained enabled.

Five fresh four-step serial/CUDA capacity pilots agreed exactly. All five 480-step
capacity diagnostics also matched the previous compact trajectories, including 75, 259,
300 and 304 warning steps at 32,768, 110,592, 262,144 and 512,000 particles. Their
respective single solver times were 6.17, 18.23, 39.36 and 76.30 s; these are not paired
large-scene speedup measurements or independent density qualification.

The local CPU release suite passed 239 checks; the parent experiment suite passed 21.
On the PC, 251 CUDA-enabled Rust checks passed, while the same three previously recorded
automatic-backend CLI tests failed. They remain open; the complete suite is not reported
as passing. A fresh control-only CLI suite reproduced all three. Strict CUDA Clippy,
formatting and native ASan/UBSan checks passed. Injected
middle-pass submission, completion and context failures checked draining, precedence,
poisoning and forbidden reuse. They do not qualify real device-loss recovery.

Keep batching: it preserves tested behaviour and produces a clear matched gain. This is
not final evaluation or proof of competitive PBF performance. The 100k-plus real-time/quality
ambition remains open. Numerical tuning,
device-error reductions, accepted-state residency and further arithmetic investigation
are separate decisions. No installed application, ordinary PC checkout, branch, commit,
tag, golden or parent gitlink was changed. No hosted or passing device-memory-sanitiser
result is claimed.

## Subsequent Git checkpoint

After measurement, the candidate was committed as Maelstrom
[`a21d961a27706e2aa434f20100e9cbbf8ae747e6`](https://github.com/Mahkrab/Maelstrom/tree/a21d961a27706e2aa434f20100e9cbbf8ae747e6)
on `phase/05-01-optimisation`. Every file in the measured candidate manifest matches
that commit, which the EPQ gitlink now pins. Original evidence and its working-tree
provenance remain unchanged. This is a local checkpoint, not a completion tag, final
evaluation or hosted verification; the GitHub link requires publication.

## References used

<a name="ref-s053"></a> **S053** — NVIDIA, *CUDA Driver API* v13.3, execution control and stream behaviour.
[Source record](/docs/research/sources/053-nvidia-cuda-driver-api.md).
