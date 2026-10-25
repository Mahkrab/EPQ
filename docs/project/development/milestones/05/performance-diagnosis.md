# Performance diagnosis

The first investigation is complete; the performance problem is not solved. Measurements on the
primary PC on 22 October 2026 identify quadratic CUDA neighbour storage and repeated host/device
transactions as the first implementation targets. No simulator code, numerical settings or old
results were changed. The [protocol](/docs/project/development/milestones/05/performance-protocol.md),
[comparator specification](/docs/project/development/milestones/05/performance-comparators.md) and
[retained evidence](/docs/project/development/assets/performance-diagnosis-v1/README.md) own the details.

## Starting point and controls

I measured unchanged Maelstrom
[`c17d8c586eba7455582ad9597cb23d7addc3c6d9`](https://github.com/Mahkrab/Maelstrom/tree/c17d8c586eba7455582ad9597cb23d7addc3c6d9),
using a locked release build with CUDA enabled. The PC has a Ryzen 9 7900X, RTX 4070 with
12,282 MiB, driver 610.88, CUDA 13.3 and Ubuntu 24.04 under WSL2. CPU controls used the same
binary, with explicit serial grid or twelve-worker grid; CUDA used device zero and 128 lanes.

The seven original sizes retained 480 steps, refinement by four, eight iterations and checkpoints
0/1/120/240/480. Each had a warm-up, three total-only samples and a separate stage profile.
All 105 baseline attempts agreed exactly with the serial physical observations, including signed
zero; small frozen goldens also agreed on all three backends. An independent reader verified the
105 attempts and all 21 primary sample sets directly from hashed output.

At 8,000 particles, approximately one simulated second required:

| Backend | Median solver time, three samples | Sample range | Median invocation |
| --- | --- | --- | --- |
| Serial grid | 65.944 s | 65.909–65.969 s | 66.666 s |
| Twelve-worker grid | 22.778 s | 22.747–22.809 s | 23.534 s |
| CUDA | 8.086 s | 8.057–8.126 s | 9.062 s |

CUDA's solver real-time factor was 0.124, not real-time operation. These are fresh baseline
measurements, not an optimisation benefit or replacements for the older campaign. Construction,
shutdown, per-step times and early/post-impact windows remain separately recorded. A no-audit core
case produced exactly the same final state and step diagnostics; its different observation policy
is explicit, and its single timing is not a new three-sample baseline.

## Ranked diagnosis

1. **Neighbour representation limits capacity and repeated work.** The solver reserves
   `4 × N × ceil(N/32)` membership bytes and repeatedly scans row words. Total modelled solver
   slots grow from 8.97 MB at 8,000 particles to 1.44 GiB at 110,592 and 30.58 GiB at 512,000.
   Independent geometric reconstruction found initial mean neighbour counts of 25.49 and 26.10
   at 8,000 and 32,768; final means were 29.37 and 31.26. Those are reconstructed counts, not
   device-buffer observations. The eight iterations perform forty full membership traversals,
   or 80 million logical word visits per 8,000-particle step—not measured DRAM traffic.
   In the full CUDA trace, density/multiplier work consumed 55.3% of kernel time and active-distance
   validation 17.9%. Compact, identity-ordered local neighbour storage is the first justified experiment.
2. **Submission and round trips are substantial.** The 480-step trace contains 69,120 launches,
   105,120 stream completions and 983 MB of device-to-host copies. Per step that is 144 launches,
   219 completions and 56 downloads, including 52 error arrays. GPU activity covered 4.856 s of an
   8.346 s traced core window; gaps covered 3.489 s, or 41.8%. These gaps are not all automatically
   removable. The 91 bitonic passes per step took only 1.4% of kernel time but 16.4% of the
   launch-to-next-launch window. Reduce measured round trips and tiny submissions after, or alongside,
   the storage experiment; do not add inclusive host waits to overlapping GPU time.
3. **Arithmetic needs targeted evidence, not a blanket rewrite.** Correction, which contains the
   binary64 compatibility power function, used 21.1% of kernel time. Even deleting that entire
   device kernel would bound improvement of this traced window at about 1.14×; this is an ideal
   bound, not an available optimisation. Power alone cannot explain the larger density/multiplier
   cost or quadratic memory. Its individual cost, achieved occupancy and bandwidth remain unmeasured:
   Nsight Compute was unavailable. CPU sampling suggests gradient work deserves attention, but
   substantial lost samples prevent precise cost shares. Threaded stage timings still locate
   11.97 s in Jacobi work and 8.38 s in neighbour search; packing and allocation lack isolated timers.

## Capacity and external context

The 32,768-particle CUDA request completed 480 steps in 42.34 s, but produced 75 CFL warnings,
starting at step 189. It is diagnostic evidence, not an admitted clean benchmark. At 110,592,
four steps took 2.434 s; the projected 292 s exceeded the predeclared 90 s admission ceiling,
so no full run was attempted. The 262,144 and 512,000 requests were skipped before allocation
under the memory rule. Neither is a measured exhaustion limit.

Pinned SPlisHSPlasH PBF was built and run on the same PC with verified identical initial fluid
coordinates, single precision, twelve OpenMP workers, fixed timestep and eight iterations. Each
case reported 3,840 iterations. Its internal `SimStep` totals were 3.864 s at 8,000 particles and
44.808 s at 110,592, with 9,712 and 35,706 additional boundary particles respectively. These are
single contextual runs: the mass, density constraint, stabilisation, sampled boundary physics,
arithmetic and timer differ. Upstream neighbour counts and equivalent physical quality remain
unmeasured. Its timer excludes boundary-simulator work; no cross-solver speedup ratio is justified.
Those differences follow the inspected implementation.<sup><a href="#ref-s060">S060</a></sup>

## Decision and limits

Proceed with the implementation track in the [performance plan](/docs/project/development/milestones/05/performance-plan.md):
first test compact neighbour storage, then reprofile before choosing the next change. Preserve exact
arithmetic order, numerical work, failure handling and acceptance boundaries. The 100k-plus real-time
ambition remains unmet; quality tuning and final evaluation have not begun.

The evidence includes failed setup attempts, warning-bearing runs, resource skips and profiler
limitations. Process-environment metadata was removed from shareable timeline exports without changing
analytical rows; private originals and their hashes were retained. Local tests and evidence audits
passed as recorded in the evidence index. No hosted checks, new commits, tags or branch changes are claimed.

## References used

<a name="ref-s060"></a> **S060** — Bender and contributors, *SPlisHSPlasH*, pinned PBF, fluid model and simulator implementation.
[Source record](/docs/research/sources/060-splishsplash-pbf-implementation.md).
