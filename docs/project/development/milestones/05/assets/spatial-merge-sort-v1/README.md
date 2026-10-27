# Spatial merge-sort evidence

This supports the [assessment](/docs/project/development/milestones/05/performance-spatial-sort.md)
and follows the [prospective protocol](/docs/project/development/milestones/05/assets/spatial-merge-sort-v1/protocol.md).
All requests start new simulations on the primary PC; saved observations are not resumed state.

The control matches all 182 files of the preceding
[synchronisation candidate](/docs/project/development/milestones/05/assets/stream-synchronisation-v1/README.md).
Reconstruct that export using its documented predecessors, then apply `candidate.patch` here.
This yields the 184-file candidate. Separate manifests, reconstruction receipts, source/binary
hashes and fresh embedded-PTX checks identify the measured uncommitted trees. Ordinary PC
checkouts and installed binaries were left alone. No new Git checkpoint is claimed.

`observations.tar.xz` contains 74 complete regression, warm-up, ordinary sample and diagnostic
records, all commands/exits, monotonic collector durations, original output hashes, environment,
input/source/binary/PTX identities, separate summaries and four eight-step trace observations.
`measurements/activity.sqlite` retains API names/times/correlations and kernel
names/times/correlations without private profiler metadata. Original native reports remain on
the PC. Launch totals are reconstructed from these rows, not inferred from performance gains.
The control uses its fixed per-step launch order to identify sorting calls; candidate sorting
calls also have their own kernel name.

`verification.tar.xz` contains qualification and preflight logs, commands, the independent
reader, collection scripts, diagnostic overlay generator/patches/manifests, kernel-resource
probe, device-memory diagnostic failure and timing-boundary receipt. The CUDA event overlay
is confined to diagnostic exports. It records sort start/end on the same stream and reads
after the existing neighbour-count completion. Its PTX matches the ordinary counterpart.
It adds no wait; its solver totals remain separate from primary timings. CPU submission and
GPU event intervals overlap and must not be added. Raw process `wall_s` includes collector
compression and is not an invocation-only measurement.

All physical and diagnostic comparisons passed. Compute Sanitizer exited 97 after failing to
initialise the WDDM debugger interface and reporting unsupported-device errors. Although the
test completed, the tool did not establish device-memory safety. This failure is retained;
racecheck was not attempted after it. Native ASan/UBSan and ordinary GPU tests establish
separate things. No actual device-loss recovery or other-GPU qualification is claimed.

`files-sha256.json` indexes uncompressed archive members. `SHA256SUMS` covers the archives,
protocol, source delta, manifests and audit/reconstruction receipts. Whole source trees,
binaries, build caches and private native profiler reports are excluded.

From the EPQ root, inspect without running a simulation:

```sh
cd docs/project/development/milestones/05/assets/spatial-merge-sort-v1
sha256sum -c SHA256SUMS
sort_evidence=$(mktemp -d)
tar -xJf observations.tar.xz -C "$sort_evidence"
tar -xJf verification.tar.xz -C "$sort_evidence"
python3 "$sort_evidence/audit.py" "$sort_evidence/measurements"
```

The audit checks original output hashes, exact canonical physical records, both timing
boundaries and paired effects. It also joins kernel/API correlation IDs and verifies that
all removed launches belong to sorting, with unchanged non-sort work, waits and transfers.
