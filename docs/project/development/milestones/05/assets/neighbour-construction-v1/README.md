# Neighbour-construction evidence

This supports the [assessment](/docs/project/development/milestones/05/performance-neighbour-construction.md)
and preserves the [prospective protocol](/docs/project/development/milestones/05/assets/neighbour-construction-v1/protocol.md).
Every request starts a new simulation on the primary PC; no recorded state is called resumed work.

The 186-file control exactly matches `final-source.json` from the retained
[state-transfer collection](/docs/project/development/milestones/05/assets/state-transfers-v1/README.md).
Reconstruct that final source using its documented predecessors, then apply `candidate.patch`
with `patch -p1` to obtain this 186-file candidate. Only `native/solver.cu`,
`src/cuda/solver_tests.rs` and `docs/cuda.md` change. Manifests and reconstruction receipts
identify both uncommitted exports, based on Maelstrom
`87145510a9e5d812066138c35f1fac82e4f593b0`. Final live source hashes match the measured
candidate; there is no later comment or source overlay. No ordinary PC checkout or installed
executable was changed.

`observations.tar.xz` contains:

- The preliminary full-trajectory control profiles collected before choosing the optimisation,
  with separately labelled stage activity, compressed original output and commands.
- All 12 exploratory warm-up/sample observations and their two-pair results per size.
- All 50 final ordinary regression/warm-up/sample observations, commands/exits, original
  output hashes, environment/resource admission, source/input/binary/embedded-PTX identities,
  complete timings and five-pair summaries. No samples were replaced.
- Four separate final 480-step profiles, privacy-limited activity SQLite, copy/API counts,
  and the custom capacity scene/defaults needed to reproduce the requests.

Primary solver times sum completed-step clocks, including validation, transfers, launches,
completion and acceptance, excluding construction/teardown, audits and output. Final collector
`wall_s` ends before compression; `collector_wall_s` includes storage. The preliminary profile
script's command `wall_s` also includes output compression; it is never used as a primary
solver or kernel duration. Diagnostic GPU intervals and cell-start/row-sort-end spans remain
separate from ordinary sample medians. Early/late bands expose evolved-motion costs.

`measurements/activity.sqlite` retains only variant, particle count, API/kernel names,
start/end times, correlation IDs and copy byte counts/directions. Addresses and private
profiler metadata are excluded; original native reports remain on the PC. The independent
reader checks every copy against its host API correlation and source-owned size schedule,
checks kernel order/types, and reconstructs stage intervals, launches and explicit waits.
The prefixes' three individual timings are available in `independent-audit.json`.

`verification.tar.xz` contains qualification commands/logs, local CPU feature-isolation evidence,
collection/audit scripts, exploratory source hashes, loaded-kernel resource probes and platform
observations. The CPU command's complete child duration was not recorded; its test output
and exit are retained. PC qualification includes the ordinary suite, explicit CUDA checks,
Clippy, formatting and control/candidate native ASan/UBSan. Compute Sanitizer exited 97 with
eight WDDM debugger/device-support errors despite its selected test completing. This is no
device-memory diagnostic pass, and racecheck was not run after that failure. Device-loss
recovery, worst-case cancellation latency and other-device/block-size performance remain
unqualified.

`files-sha256.json` indexes every uncompressed archive member. `SHA256SUMS` covers archives,
protocol, manifests, patch, audit and integrity receipts. No whole source trees, binaries,
build caches or private native profiler reports are retained in this collection.

From the EPQ root, these commands inspect evidence without running a simulation:

```sh
cd docs/project/development/milestones/05/assets/neighbour-construction-v1
sha256sum -c SHA256SUMS
neighbour_evidence=$(mktemp -d)
tar -xJf observations.tar.xz -C "$neighbour_evidence"
tar -xJf verification.tar.xz -C "$neighbour_evidence"
python3 "$neighbour_evidence/audit.py" "$neighbour_evidence/measurements"
```

The reader verifies all final output hashes, workload completion, exact canonical physical
and diagnostic records, internal timing medians/ranges/paired changes, and both profiled
physical comparisons. It reconstructs every transfer, launch schedule and stage timing.
Physical equivalence does not establish independent fluid quality or statistical significance.
