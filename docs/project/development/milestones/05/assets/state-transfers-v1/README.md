# State-transfer evidence

This supports the [assessment](/docs/project/development/milestones/05/performance-state-transfers.md)
and follows the [prospective protocol](/docs/project/development/milestones/05/assets/state-transfers-v1/protocol.md).
All requests start new simulations on the primary PC. No saved state is treated as resumed work.

The 184-file control exactly matches the preceding
[spatial-sort candidate](/docs/project/development/milestones/05/assets/spatial-merge-sort-v1/README.md).
Reconstruct that export using its documented predecessors, then apply `candidate.patch` here
to obtain the 186-file measured candidate. The final tree adds `comment-clarification.patch`,
which corrects one neighbour-header comment. `final-source.json` identifies that tree; a fresh
PTX comparison proves the comment change leaves the measured PTX byte-identical.
All other final source hashes match the measured export. These are uncommitted exports based
on Maelstrom `87145510a9e5d812066138c35f1fac82e4f593b0`, not new Git checkpoints.
Ordinary PC checkouts and installed commands were left alone.

`observations.tar.xz` contains all 50 regression/warm-up/sample records, original output hashes,
commands/exits, monotonic child and collector durations, environment, input/source/binary/PTX
identities, the summary and four separate eight-step trace observations. Solver timings use
internal completed-step clocks; construction/teardown, audits, output and compression stay
outside them. Process `wall_s` ends before collector compression; `collector_wall_s` includes it.
Profiled times are separate from primary samples.

`measurements/activity.sqlite` retains API names/times/correlations, kernel
names/times/correlations and copy sizes/directions/times/correlations. Private profiler metadata,
addresses and native reports are excluded; original reports remain on the PC. The independent
reader correlates every copy with its actual host call and checks every transfer against the
source-owned step schedule. Initial uploads are separated from steady-step totals. It checks
unchanged final snapshot downloads and explicit waits, not just a claimed byte reduction.

`verification.tar.xz` contains qualification commands/logs, the full preliminary qualification and its source
manifest, earlier exploratory logs, local CPU results, collection/audit scripts, kernel-resource probe, platform observation,
Compute Sanitizer failure, and final comment/PTX receipts. Both full qualification runs passed;
the later run includes the final Rust safety/documentation comments. All physical comparisons
passed. Compute Sanitizer exited 97 with 16 WDDM debugger/device-support errors; although its
two selected tests completed, no device-memory diagnostic pass follows. Racecheck was not run
after that failure. Native ASan/UBSan and ordinary GPU checks establish separate things.
Actual device-loss recovery and worst-case cancellation latency remain unqualified.

`files-sha256.json` indexes uncompressed members. `SHA256SUMS` covers the archives, protocol,
source deltas/manifests, audit and reconstruction receipts. No whole source trees, binaries,
build caches or private native profiler reports are stored here.

From the EPQ root, inspect without running a simulation:

```sh
cd docs/project/development/milestones/05/assets/state-transfers-v1
sha256sum -c SHA256SUMS
transfer_evidence=$(mktemp -d)
tar -xJf observations.tar.xz -C "$transfer_evidence"
tar -xJf verification.tar.xz -C "$transfer_evidence"
python3 "$transfer_evidence/audit.py" "$transfer_evidence/measurements"
```

The audit checks original output hashes, workload admission, exact canonical physical records,
medians and paired changes. It then reconstructs copy counts, every transfer size, total bytes
in both directions, first uploads, kernel additions and explicit synchronisation counts.
