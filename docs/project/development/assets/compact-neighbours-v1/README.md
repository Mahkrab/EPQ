# Compact-neighbour experiment evidence

This supports the [implementation record](/docs/project/development/performance-compact-neighbours.md).
Measurements ran sequentially on the primary PC through `ssh pc` on 22 October 2026.
The implementation is uncommitted working evidence, not a Git checkpoint or final evaluation.

## Identity and contents

`campaign.tar.xz` contains the frozen protocol, complete source/hash manifests, raw hashed process
output, independent serial controls, ordinary/profiled regression runs, five paired samples per
implementation, capacity decisions, five separate CUDA traces and verification output. It also
retains the failed candidate's 32,768-particle accepted prefix and 110,592-particle failure.
The complete rejected campaign remains private; its timings are not admitted evidence.

The assessed base is Maelstrom `c17d8c586eba7455582ad9597cb23d7addc3c6d9`.
The candidate tree fingerprint is `975e6bb0b26e024314974a99b14e69bca35068eb079d35b0f64713fe631ece0e`;
the copy-ordered bitset control is `a34dff7890b21cb04caa35bb21db0d3f5f52ab55eef15921cdcfcc3f405afac3`.
These SHA-256 tree fingerprints are not commit IDs. The control changes only the stream flag
from the base. Both have complete file manifests and distinct executable/build identities in
`campaign/campaign.json`. The original baseline executable and old evidence were not replaced.
After measurement, one stale Rustdoc sentence was corrected to describe the ordered private
stream. `reviewed-source.json` identifies the resulting worktree; verification confirms that
all executable source and tests are otherwise byte-identical to the measured candidate.

Both used `cargo build --release --locked --offline --features cuda`, toolkit
`/usr/local/cuda`, architecture 89 and explicit build-revision identities. Build logs and fresh
GPU/CPU/compiler/toolkit/profiler outputs are included. The platform/build-environment snapshot
was collected after measurement and labelled accordingly. No global package, driver, security,
affinity, frequency, installed application or normal PC checkout was changed.

Readable derived files alongside the archive are:

- `summary.json`: independently regenerated timing summaries, stage profiles and capacity outcomes;
- `traces/`: counts, bytes, operation timings, non-overlapping activity coverage and allocation peaks;
- `independent-audit.json`: exact comparisons, primary medians and finite/plane-compliant endpoints;
- `verification.json`: observed test outcomes, negative controls, source identity checks and limitations;
- `analysis-identity.json`: current analysis/test hashes, separate from the collector frozen before collection;
- `document-checks.json`: local link/citation checks, not hosted rendering;
- `manifest.json`: size/SHA-256 inventory of every retained public file except itself.

The archive contains observations and small input fixtures, not simulator source trees, Git data,
executables or build caches. Native Nsight reports are excluded because they include process
environments. `campaign/privacy.json` maps original SQLite/native hashes to sanitised exports;
environment/private-path strings were removed and every analytical table checked unchanged.
The original CUDA file inventories remain as `original-files.json`. Private originals and source
exports were retained outside Git. The collector is unchanged; the analyser was subsequently
extended to reconcile both layouts.

## Checks and interpretation

The local CPU release suite passed 239 checks; 18 parent experiment tests passed. On the PC,
250 Rust checks passed with opt-in CUDA tests enabled. The full PC suite still exits 101 because
three CLI tests assume automatic selection produces serial metadata. The untouched baseline
reproduced the same three failures. Full logs are retained: no tests were skipped, weakened or
silently reported as passing. Strict Clippy and native ASan/UBSan injected-failure checks passed.
The native tests establish ownership/ordering policy under injected faults, not real device-loss recovery.

The new large-lattice test failed before the copy-ordering repair and passed after it. The initial
candidate's small-workload success was insufficient; rejected large-case output remains evidence
of that gap. An attempted all-target test used an unsupported `--keep-going` argument; its failure
is retained, followed by the actual `--no-fail-fast` suite. Some interactive diagnostic commands
were observed only in the session; do not claim an exhaustive raw command diary.

Five total-only samples per variant retain the original 480-step, refinement-four, eight-iteration,
observation-rich request. Their old/new ordering alternates. Seven separate candidate stage profiles
do not enter primary medians. No historical sample is pooled into the paired comparison.
All count/prefix/fill/sort work and ordinary checks stay inside solver timing; construction,
teardown, audits, output and whole invocation have separate boundaries.

Each capacity pilot is checked against fresh serial-grid execution. Full trajectories at 32,768
particles and above contain CFL warnings and have no independent density qualification. Their
finite, plane-compliant endpoints do not prove competitive quality, long-run stability, real time
or a universal maximum particle count. Memory figures are traced allocation peaks, including
transient geometric growth and module constants, not complete driver/context or host-memory peaks.

## Reproduce the analysis without starting a simulation

From the EPQ root:

```sh
compact_dir=$(mktemp -d)
tar -xJf docs/project/development/assets/compact-neighbours-v1/campaign.tar.xz -C "$compact_dir"
python3 -m tools.performance.compact report "$compact_dir/campaign"
python3 -m tests.performance.audit_compact "$compact_dir/campaign" "$compact_dir/campaign/summary.json"
python3 -m tools.performance.compact_trace "$compact_dir/campaign/timelines/compact-8000-480" --particles 8000 --steps 480
python3 -m tools.performance.compact_trace "$compact_dir/campaign/timelines/bitset-110592-4" --particles 110592 --steps 4 --layout bitset
```

These read retained observations; they do not run, rerun or resume a simulation. Fresh collection
requires the declared PC, source manifests and protocol. No hosted check, passing device-memory
sanitiser, other platform, physical-quality target or final evaluation is claimed.
