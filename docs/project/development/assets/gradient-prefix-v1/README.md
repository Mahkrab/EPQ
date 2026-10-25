# Multiplier-prefix arithmetic experiment

This supports the [implementation record](/docs/project/development/milestones/05/performance-gradient-reuse.md)
and [prospective protocol](/docs/project/development/milestones/05/performance-gradient-protocol.md).
PC verification and measurement ran across 22–23 October 2026. Local CPU/tooling tests
are separate from the primary-PC benchmarks; no laptop timing replaces a PC baseline.

The candidate was rejected under its prospective admission policy. The active CUDA loop
is restored to the base implementation; only the new regression tests remain in Maelstrom.
This record preserves a measured trial, not a performance improvement claimed for the final tree.

## Source and comparison identities

Both exports start from Maelstrom
[`5120acfbcb07e94ebefd5957ad8f9afa47888be7`](https://github.com/Mahkrab/Maelstrom/tree/5120acfbcb07e94ebefd5957ad8f9afa47888be7).
Fingerprints hash the sorted compact JSON map of 150 file hashes:

| Export | Fingerprint |
| --- | --- |
| Unchanged multiplier | `02171272227b13474b9978744d504015f7674a054253c98533e9b0037584b256` |
| Prefix reuse trial | `0b695f83baae7217c26e187161e34a2f276e1316c00770ebad4c3ced218c2165` |

The unchanged, untracked custom scene appears in both exports but no measurement selects
it. These are working-tree identities, not commits.
[candidate.patch](/docs/project/development/assets/gradient-prefix-v1/candidate.patch) preserves the focused
trial changes against the base commit so that rejecting the implementation does not lose
its source. It excludes the unrelated custom scene. The complete tracked-file hashes in
`campaign/campaign.json` distinguish reconstruction from the full private export.

Original source archives, binaries and native profiler reports remain private. Shareable
SQLite removes process-environment, hostname and personal-path metadata. Original and
sanitised hashes remain linked through `campaign/privacy.json`; analytical tables are
checked after vacuuming. `kernel-resources.json` records 44 versus 48 registers per thread,
not an occupancy measurement or proof of the cause of the modest runtime difference.

## Recorded comparison

The five-sample medians were 2.023 versus 1.954 s at 8,000 particles and 13.194 versus
12.800 s at 110,592 particles, always for 480 refined steps and eight iterations.
All samples remain in `summary.json`. The smaller ranges overlap; neither case reaches
the prospective 1.05× gain criterion. The larger case retains the control's CFL warnings:
it is a matched runtime diagnostic, not independently qualified physical accuracy.

`independent-audit.json` checks raw hashes, exact observations and warnings, timing sums
and the decision. `negative-controls.json` checks rejection of false timing and retention
claims. `traces/` and `trace-checks.json` compare the source-specific traces and sanitised
reanalysis. `verification.json` distinguishes PC, local and unperformed checks.

The PC's old temporary comparison directories had disappeared. The first preparation
failure is retained under `campaign/setup-failure/`; inputs and PC-produced controls were
restored unchanged, with hashes in `campaign/restored-references.json` and metadata in
`campaign/reference-identities/`. An SSH disconnect followed successful main collection.
The detached continuation reused that completed evidence and ran only the larger pairs,
report and traces. `campaign/orchestration-notes.json` and the supervisor log record this.
No completed sample was discarded, replaced or rerun to obtain a favourable result.

## Evidence layout and saved-data inspection

Five archives extract into one `campaign/` tree. They separate ordinary regression and
profiling evidence, new capacity results, previous capacity controls, and each variant's
larger paired observations. Archives contain data and verification logs, not repositories,
executables, caches or native profiler reports. Each is kept below 50 MiB.

From the EPQ root, these commands read saved data; they do not start or rerun a simulation:

```sh
gradient_evidence=$(mktemp -d)
for evidence_archive in campaign capacity comparison-controls paired-large-control paired-large-candidate; do
  tar -xJf "docs/project/development/assets/gradient-prefix-v1/$evidence_archive.tar.xz" -C "$gradient_evidence"
done
python3 -m tools.performance.arithmetic report "$gradient_evidence/campaign"
python3 -m tests.performance.audit_arithmetic "$gradient_evidence/campaign" "$gradient_evidence/campaign/summary.json"
python3 -m tools.performance.compact_trace "$gradient_evidence/campaign/timelines/candidate-8000-480" --particles 8000 --steps 480 --layout compact-stages
```

`archive-checks.json` verifies archive members; `manifest.json` inventories public files
except itself. Historical evidence remains unchanged. Hosted verification, actual
device-loss recovery, a passing device-memory sanitiser, other platforms and independent
large-scene density qualification remain unverified. No new Git checkpoint is created.

`final-verification.json` and `final-verification.tar.xz` qualify the restored implementation
with the new tests: 257 Rust checks passed with the same three known CLI failures, and
strict Clippy and formatting passed. Their final source fingerprint is
`5beb47272ad832dcb79133f5fa140f244a177359885646fd112babba11b0b962`.
`patch-checks.json` verifies all 149 reconstructed tracked trial files independently.
