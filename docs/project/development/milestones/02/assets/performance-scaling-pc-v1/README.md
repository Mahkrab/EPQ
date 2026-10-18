# Primary-PC threaded CPU scaling

This campaign measures serial uniform-grid execution followed by 1, 2, 4, 8, 12 and 24 workers on the
primary PC reached through `ssh pc`. Collection ran on 18 October 2026, from 14:53:43 to 15:46:45 UTC,
after a separate default-worker probe. The machine reports an AMD Ryzen 9 7900X under x86_64 WSL2
Ubuntu 24.04.5, twelve guest-visible cores and twenty-four logical processors. Rust's default-worker
selection returned 24; inherited affinity covers CPUs 0–23. These observations do not establish unseen
physical host configuration or guarantee simultaneous worker service.

## Results and interpretation

The [scaling report](/docs/project/development/milestones/02/assets/performance-scaling-pc-v1/report.md)
and [machine-readable results](/docs/project/development/milestones/02/assets/performance-scaling-pc-v1/scaling.json)
retain every size and execution setting, primary spread and throughput, invocation medians, speedup,
one-worker scaling and requested-worker efficiency. The
[phase record](/docs/project/development/milestones/02/phases/phase-01-performance-scaling.md)
summarises the lowest observed medians and the gate decision.

One-worker execution is slower than serial at all seven sizes. The best threaded median at 64
particles is also slower: 0.561333 s with two workers against 0.327190 s serial. Two workers give a
small median advantage at 216, but the sample ranges overlap. Four workers have the lowest medians
from 512 to 1,728. Twelve have the lowest at 4,096 and 8,000, although the eight/twelve-worker ranges
overlap at 4,096. Three samples do not establish precise crossover points or statistical significance.

At 8,000, serial takes 64.527357 s and twelve workers take 21.592798 s: **2.988×** threading speedup.
Scaling relative to one threaded worker is **3.038×**; dividing that by twelve gives **25.32%**
requested-worker efficiency. Twenty-four workers take 27.019083 s, giving 2.388× against serial.
At 64, their median is 15.896396 s. More workers therefore carry substantial overhead for small
inputs and show saturation within this family; the capacity-based default is not an optimal count.

Profiles identify costs without assigning an unmeasured cause. At 8,000, serial Jacobi/search shares
are 85.87%/11.13%; at twelve workers they are 52.05%/37.06%. Search remains serial in this source.
Dispatch and repeated allocation are inside Jacobi timing, but these profiles do not isolate their
individual costs or establish cache, bandwidth, thermal or scheduler explanations. No tuning was made.

## Retained evidence and provenance

There are **245 benchmark attempts**: seven sizes × seven settings × one warm-up, three primary
samples and one separate profile. All completed 480 steps without warnings, failures or timeouts.
Every complete attempt matches its same-size serial-grid warm-up exactly, including signed-zero
sensitive input/snapshot hashes, physical identities, checkpoint audits, every CFL diagnostic and
completion. Unequal hashes would reject acceptance; no tolerance is inferred from compact data.

Each series retains `collection.json`, `dataset.json`, full replayable `correctness.json`, its report
and all 35 raw attempts. Index hashes identify the exact retained bytes. Full correctness results
also match the frozen golden. The
[component comparisons](/docs/project/development/milestones/02/assets/performance-scaling-pc-v1/correctness-comparison.json)
record zero position/velocity maximum and RMS errors, worst components, audit values, CFL agreement
and completion for those seven results, using the identified existing component verifier.
The [replay checks](/docs/project/development/milestones/02/assets/performance-scaling-pc-v1/replay-validation.json)
record subsequent ordinary CLI replays with restored execution settings and exact numerical agreement.
Replay durations do not enter performance results.

The [independent audit](/docs/project/development/milestones/02/assets/performance-scaling-pc-v1/validation.json)
checks raw hashes, all 82 simulator source hashes, all five recorded collector/protocol hashes,
frozen inputs, exact outputs, primary statistics, invocation medians, throughput, stage sums,
proportions, residuals and both ratios without collector imports. Its source is
[the standalone checker](/tests/evidence/checks/scaling.py). It also detects a deliberately wrong
stored median after the stored hash and summary are changed to agree with that wrong value.

All settings used clean Maelstrom
[`60b9a767636428a26f39a1901e2cac4276c75c83`](https://github.com/Mahkrab/Maelstrom/tree/60b9a767636428a26f39a1901e2cac4276c75c83)
and one binary, SHA-256 `1f737d1dfd2c0d6bfe58ef2f39873287b2722f1737dbcdd75ba41fafc7320c29`.
Temporary PC checkouts came from that commit and EPQ `5d0f4d4c3bf1a3d9f85fc2df636b03ada38a7f6b`;
the existing PC checkout remained untouched. The uncommitted collector was overlaid and identified by
file hashes, which match the current collector exactly. The
[pre-collection protocol bytes](/docs/project/development/milestones/02/assets/performance-scaling-pc-v1/protocol.md)
match the [owning protocol](/docs/project/development/milestones/02/scaling-protocol.md).

Rust/Cargo 1.98.1 built once using `cargo build --release --locked --offline`, the standard release
profile and no custom flags. The PC passed 204 release Rust tests, including two doctests, and 26
collector tests before collection. No other project tests or builds ran on the PC during measurement.
Completed series were copied for local audits; final raw files and generated reports were imported
byte for byte after collection. This README, independent audit and component/replay checks were added
subsequently. No source, physical input, numerical rule, sample or timing boundary was changed.

## Reproduction and limitations

From the EPQ root on the PC, with the recorded Maelstrom source and locked dependencies available:

```sh
RUSTUP_TOOLCHAIN=1.98.1 python3 -m tools.baseline.scaling collect NEW_DIRECTORY
```

Verify and regenerate this retained campaign locally, without simulation:

```sh
python3 -m tools.baseline.scaling report \
  docs/project/development/milestones/02/assets/performance-scaling-pc-v1
python3 tests/evidence/checks/scaling.py \
  docs/project/development/milestones/02/assets/performance-scaling-pc-v1
```

`python3 -m tools.baseline.main report SERIES_DIRECTORY` regenerates an individual series report.
All seven series reports and the scaling report regenerated byte for byte both on the PC and locally.
The historical laptop/PC baseline and paired-search reports also regenerate unchanged. Collection
requires a new directory and never replaces an existing campaign.

The unchanged `serial-baseline-v1` policy uses the seven ascending sizes through 8,000, 480 steps,
factor-four refinement, eight Jacobi iterations, checkpoints 0/1/120/240/480 and a 120-second budget
plus 30-second cancellation grace. Solver totals include dispatch, barriers, synchronisation,
validation, repeated allocation and required setup within each step. One-time pool construction and
teardown, observations and publication are outside those totals; invocation wall time is separate.
Profiles contain extra clocks and never supply primary ratios. No fresh brute-force series was
collected, so historical ratios are context and no overall original-method gain is claimed.

Two UTC timestamps move backwards between successive invocation pairs in the twenty-four-worker
series: 0.546788 s before the 1,000-particle profile, and 0.408254 s before the 8,000-particle warm-up.
The cause was not established. The collector waits synchronously for each child to exit and records
order explicitly; solver and invocation durations use monotonic clocks. These UTC anomalies do not
supply duration or overlap estimates.

Fixed order, host activity, scheduling and thermals remain confounders; no affinity, priority or
frequency control was applied. No larger-size campaign, memory-use measurement, practical maximum,
physical-accuracy or universal scaling claim follows. The assessed source and parent gitlink are
unchanged, and this evidence has no separately authorised completion commit, tag or publication yet.
