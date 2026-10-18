# Threaded CPU scaling measurement protocol

This campaign extends the [existing measurement protocol](/docs/project/development/milestones/00/measurement-protocol.md)
with explicit execution settings. Its `serial-baseline-v1` inputs, seven ascending particle counts,
480-step requests, checkpoints, factor-four refinement, eight Jacobi iterations, one warm-up,
three total-only samples, separate profile and 120-second timeout plus 30-second grace remain unchanged.

The assessed source is Maelstrom `60b9a767636428a26f39a1901e2cac4276c75c83`, already qualified by the
[threaded verification record](/docs/project/development/milestones/02/phases/phase-00-threaded-cpu.md).
No arithmetic, numerical policy, solver work or fixture changes are proposed. Build once in release
mode with the existing locked, offline, default-flags command. Use the same binary for every series.
Record actual source and collector hashes, binary hash, toolchain, build identity and PC environment.

Run on the primary PC reached through `ssh pc`. Collect fresh serial-grid controls first, then
threaded worker counts **1, 2, 4, 8, 12 and 24**, sequentially with no concurrent project checks on
that device. These counts span one-worker overhead, intermediate scaling and the PC's observed
24-logical-processor capacity. Before collection, run the ordinary threaded CLI without `--threads`
and retain its selected default; require that count in the sequence. Record guest-visible topology
and inherited affinity. A pool worker is not a physical core or a guarantee of simultaneous service.
No affinity, priority or frequency control is applied. Do not infer unseen host topology.

Each series first retains a full replayable 64-particle correctness result and compares every
physical output exactly with the frozen golden. Validate backend identity and explicit execution
settings separately. Compare every clean complete warm-up, primary sample and profile with the
same-size serial-grid warm-up, excluding only execution/backend/run identity, optional timings and
variable build context. Retain physical identities, all checkpoint and final snapshot hashes, density
audits, every CFL diagnostic, warnings, failures and completion classification. Hashes preserve signs.
Exact equality suffices for this unchanged arithmetic. Unequal hashes reject acceptance; compact data
cannot establish tolerance acceptance and must not be silently admitted. A future tolerance-based
implementation would need independently compared underlying component values and its own evidence.

A timed-out or unclean warm-up prevents primary sampling but still permits one bounded profile.
Retain all raw attempts, partial timings, actual invocation wall times, exits, warnings and failures.
Missing controls or incomplete clean primary sets yield no ratio. No outliers are removed.

The complete transactional timestep includes dispatch, stage barriers, synchronisation, validation,
repeated allocations and repeated setup. One-time private pool construction and teardown remain
outside solver timing. Invocation wall time includes those costs, audits and output. Profile clocks
measure caller-coordinated elapsed intervals after joined work, never summed worker clocks. Report
stage sums, proportions and residual separately from primary totals.

Report median, min–max, mean, sample standard deviation, time per step and particle updates per second.
Threading speedup is fresh serial-grid median / selected threaded median. Worker scaling is threaded
one-worker median / selected threaded median. Requested-worker efficiency is scaling / requested
workers; it is not physical-core utilisation. Preserve per-series profiles and invocation medians.
No fresh brute-force series is planned: do not report an overall original-method gain using historical
denominators. Profile before considering tuning; no optimisation is required by a slowdown.

Collect using `python3 -m tools.baseline.scaling collect NEW_DIRECTORY`; regenerate and verify using
`python3 -m tools.baseline.scaling report DIRECTORY`. Destinations must be new. Keep this protocol's
pre-collection bytes in the campaign. No memory-use measurement, larger-size series or change to
solver semantics is included. Fixed collection order, host activity, thermals and scheduling remain
limitations; three samples establish observed variability, not statistical significance.
