# Primary-PC performance diagnosis evidence

This supports the [diagnosis](/docs/project/development/milestones/05/performance-diagnosis.md), not a new
optimised solver or final evaluation. Collection ran on 22 October 2026 through `ssh pc`,
sequentially, against unchanged Maelstrom `c17d8c586eba7455582ad9597cb23d7addc3c6d9`.
EPQ started at `86e4c0ee0a2c1ce3ca312870f9a752127b455e69`; parent tools and records are
uncommitted working evidence. No branch, tag, commit, remote or gitlink was changed.

## Inventory and provenance

| File | Responsibility |
| --- | --- |
| `campaign.tar.xz` | Original hashed process output, frozen inputs/protocol, source identity, environment, qualification, 105 baseline attempts, capacity decisions, shareable timelines and external runs |
| `setup-failure.tar.gz` | Earlier preparation/qualification and first baseline warm-up, before the collector's serial-execution omission was fixed |
| `baseline.json` | Recomputed 21-row baseline, separate stage windows and capacity outcomes |
| `cuda-4.json`, `cuda-480.json` | Launch/copy/completion reconciliation, operation attribution and non-overlapping device coverage |
| `context.json` | External-run counters, independent geometric counts and qualified CPU sampling observations |
| `analysis-identity.json` | SHA-256 identities of the current uncommitted tools/tests; not a Git checkpoint |
| `verification/` | Actual local check commands, original stdout/stderr, exits and audit results |
| `verification.json`, `document-checks.json`, `archive-checks.json` | Completion criteria, environments, checks, limitations and link/archive validation |
| `manifest.json` | Size and SHA-256 inventory of retained files, excluding itself |

Archives contain observations and small input fixtures, not source trees, Git data, binaries,
build products or caches. `campaign/campaign.json` names every assessed Maelstrom source-file hash,
the release executable hash, original collector hashes, compiler/toolkit/driver outputs and input
identities. Full commands and monotonic elapsed times live beside each attempt. All public files
are covered by the outer manifest, including process metadata and derived reports.
Local verification command paths are normalised relative to the EPQ root; original metadata hashes
are in `verification-privacy.json` and private originals are retained. Their stdout/stderr are unchanged.

The private Nsight native reports capture process environments. They were deliberately excluded
from publication. `campaign/privacy.json` retains their original hashes and maps original SQLite
hashes to shareable export hashes. Exports redact process environments, hostname and private-path
strings, then vacuum the database; all analytical tables retain identical typed-row hashes.
`original-files.json` preserves the original CUDA report inventory; `files.json` checks the shareable
derivative. No timing, launch, copy, allocation or sampling row was edited. Private originals also
remain in the operator's local state directory, outside Git. They are not published evidence.

## Collection boundaries and exceptions

The release build used `cargo build --release --locked --features cuda`,
`CUDA_HOME=/usr/local/cuda`, `MAELSTROM_CUDA_ARCH=89` and the full assessed revision through
`MAELSTROM_BUILD_REVISION`. The first offline build could not resolve an uncached locked
dependency; a locked online build succeeded. That Maelstrom build transcript and the initial SSH
timeouts were observed in the session but were not retained as raw files. The executable and
source hashes, compiler/environment, successful CUDA probe and exact golden comparisons are retained;
do not pretend these replace a missing build transcript.

The first collector stopped after a successful serial warm-up because serial JSON omits the
default execution field. Its output was retained, a regression test was added, and collection
restarted in a fresh directory. No attempt was overwritten or silently added to the successful
sample sets. A first CPU profile used a wrong relative executable path and failed before simulation;
both it and the corrected attempt remain under `campaign/timelines/`.

The initial source model predicted 216 stream completions per step. Trace reconciliation found
three additional reservations inside uploads, making 219. `source-models.json` is the original
derivation, not a measurement. It was not rewritten: current tools and `cuda-*.json` explicitly
correct it. Allocation, requests, measured timings and admission decisions are unaffected.

The frozen protocol in the archive is the pre-collection version. The live protocol subsequently
received an S060 citation/footer only; no rule or threshold changed after measurements.

The baseline has one ordinary warm-up, three total-only samples and a separate stage profile
for each backend/size. Profiles never enter medians. Solver time includes transactional step
work and ordinary checks; checkpoint audits, JSON encoding and process startup are outside it.
Construction, teardown, first step, remaining-step median and whole invocation are separate.
Core capacity cases omit checkpoint audits but retain initial/final state and ordinary diagnostics.
Their 8,000-particle physical equivalence is checked explicitly; they are not a relabelled baseline.

## External build and interpretation

SPlisHSPlasH revision `7586ffa25948c6ce3bc6c238cda30ad8d35f60a0` was downloaded from its pinned
upstream archive. `external/build-identity.json` retains archive/binary hashes, effective build flags,
compiler and dependency revisions; configure/build commands and logs are retained. Release used
single precision, OpenMP, AVX/performance optimisation and CompactNSearch, without Python bindings
or third-party methods. No global packages or normal installations were changed.

The two fixtures import the exact retained 8,000/110,592 Maelstrom initial positions. The authored
Partio checker verifies actual binary32 readback and ordering before launch, compensating for the
PTS reader's Y/Z swap. Both runs used twelve workers, fixed timestep, eight iterations and a
time-based stop; iteration totals establish 480 steps. Printed times and simulated totals are rounded.
Fluid mass is approximately 0.125 kg upstream versus 0.123789966 kg in the Maelstrom input.
Boundary samples, clamping, stabilisation and timers also differ. Read the
[mismatch specification](/docs/project/development/milestones/05/performance-comparators.md), not a speedup ratio.
The mass, parser and timer distinctions follow the inspected upstream code.<sup><a href="#ref-s060">S060</a></sup>
External neighbour counts, density/escape audits and matched quality remain unmeasured.

## Rechecking without running a simulation

From the EPQ root, with the assessed Maelstrom revision available as `Maelstrom`:

```sh
diagnosis_dir=$(mktemp -d)
tar -xJf docs/project/development/assets/performance-diagnosis-v1/campaign.tar.xz -C "$diagnosis_dir"
python3 -m tools.performance.report "$diagnosis_dir/campaign" Maelstrom --output "$diagnosis_dir/baseline.json"
python3 -m tests.performance.audit "$diagnosis_dir/campaign" "$diagnosis_dir/baseline.json"
python3 -m tools.performance.timeline "$diagnosis_dir/campaign/timelines/cuda-8000-480" --steps 480 --output "$diagnosis_dir/cuda-480.json"
python3 -m tools.performance.context "$diagnosis_dir/campaign" --output "$diagnosis_dir/context.json"
```

These inspect retained observations; they do not start, replay or resume a simulation.
The source verifier rejects a different checkout. Collection entry points are
`tools.performance.study`, `tools.performance.profile` and `tools.performance.external`;
they refuse existing destinations. Fresh measurements require the declared PC, build and protocol.

Local verification covers 16 focused performance tests, 27 baseline tests, 16 CUDA-parent tests,
the independent raw-output audit, both CUDA timeline reconciliations, context analysis, compilation,
archive integrity and document references. The CPU profile retained 118,490 running samples but
lost 86,999 events and was throttled: sample fractions are clues, not precise elapsed-time shares.
Kernel-mode CPU samples were unavailable at the existing security setting. Nsight Compute and
`perf` were absent. Occupancy, bandwidth, isolated power/packing/allocation cost, total driver-memory
peak, long-run large-scene quality and hosted checks remain unverified.

## References used

<a name="ref-s060"></a> **S060** — Bender and contributors, *SPlisHSPlasH*, pinned fluid model, Partio reader and simulator.
[Source record](/docs/research/sources/060-splishsplash-pbf-implementation.md).
