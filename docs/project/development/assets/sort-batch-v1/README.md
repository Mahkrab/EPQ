# Batched-sort experiment evidence

This supports the [implementation record](/docs/project/development/performance-sort-batching.md)
and its [predeclared protocol](/docs/project/development/performance-sort-protocol.md).
Measurements ran sequentially on the primary PC through `ssh pc` on 22 October 2026.
This is uncommitted implementation evidence, not a Git checkpoint or final evaluation.

## Identities and contents

Both implementations are based on Maelstrom `c17d8c586eba7455582ad9597cb23d7addc3c6d9`:

| Variant | Source-manifest SHA-256 fingerprint |
| --- | --- |
| Individually completed compact-row sort | `c65cf1720cbb125f70528eed460f1f63f904dada8480369adf43080ef7fd6b4f` |
| Batched compact-row sort | `90d5223aa255e904b95363afaf023b191cbfea1b01276841ad34bf5520fd2d90` |

These fingerprints are not commit IDs. Full file manifests, executable hashes, build revisions,
protocol/collector identities and commands are retained in `campaign.tar.xz`. Both used locked,
offline release CUDA builds with no custom Rust flags. The control already includes compact rows
and the pageable-copy ordering repair; no earlier bitset timing is pooled into this comparison.
The source and executable identities were rechecked after collection.

The archive contains the protocol, independent serial controls, seven ordinary/profiled regression
pairs, five alternating primary samples per variant, capacity admissions/pilots/trajectories,
previous compact trajectories, four separate CUDA traces, input fixtures and raw verification output.
It contains no simulator source tree, executable, Git directory or build cache. Private originals
and exact source exports remain outside Git; ordinary PC repositories and installations were untouched.

Native Nsight reports and original SQLite exports remain private because they capture process
environments. Published SQLite exports remove environment and personal-path metadata, with original
hashes and unchanged analytical-table hashes in `campaign/privacy.json`. Original inventories remain
separate from the shareable inventories. Sanitised exports are derived evidence, not original bytes.

Alongside the archive, `summary.json` retains primary variability and capacity diagnostics;
`traces/` reconciles launches, completions, transfers, activity and allocation peaks;
`independent-audit.json` checks raw numerical components and timing totals;
`negative-control.json` records rejection of a false median; and `verification.json` records
checks and limitations. `manifest.json` inventories the retained public files except itself.

## Checks and interpretation

The local CPU release suite passed 239 checks and the parent experiment suite passed 21.
On the PC, 251 CUDA-enabled Rust checks passed, including the new exact cell-sort oracle and
all opt-in hardware checks. Three existing automatic-backend CLI tests failed; their failures
remain visible rather than skipped or reported as passes. Strict CUDA Clippy, formatting and
native ASan/UBSan injected-failure checks passed. These establish tested failure policy, not
recovery from actual device loss. No passing device-memory-sanitiser or hosted check is claimed.
The fresh control-only CLI suite reproduced the same three failures. Source rechecking also
confirmed that both builds produced byte-identical PTX device code.

Five independent total-only samples per variant preserve 480 steps, refinement four, eight
iterations and checkpoints 0/1/120/240/480. Order reverses on even sample numbers. Profiles do
not enter primary medians. Timers include required solver checks, transfers, submission and
completion; audits, observations, construction, teardown and invocation have separate boundaries.

Larger capacity trajectories retain their previous CFL warnings and lack density qualification.
Their exact agreement is regression evidence, not proof of competitive physical quality, real
time or maximum capacity. Traced allocation peaks exclude untracked driver/context memory.
No frequency, affinity, priority, driver or security setting was changed.

## Inspect retained observations without running a simulation

From the EPQ root:

```sh
sort_evidence=$(mktemp -d)
tar -xJf docs/project/development/assets/sort-batch-v1/campaign.tar.xz -C "$sort_evidence"
python3 -m tools.performance.sort_batch report "$sort_evidence/campaign"
python3 -m tests.performance.audit_sort_batch "$sort_evidence/campaign" "$sort_evidence/campaign/summary.json"
python3 -m tools.performance.compact_trace "$sort_evidence/campaign/timelines/candidate-8000-480" --particles 8000 --steps 480 --layout compact-batched
```

These commands read saved evidence; they do not start, rerun or resume a simulation. Fresh
collection requires the declared source trees, primary PC and protocol, not just the old paths.
