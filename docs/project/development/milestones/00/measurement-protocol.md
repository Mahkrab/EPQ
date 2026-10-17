# Serial baseline measurement protocol

## Primary measurement device

The PC reached through `ssh pc` is the primary device for important baselines and backend comparisons.
Routine verification and exploratory timings may run on the laptop. If the PC is unavailable, retain
any fallback timings as provisional, machine-specific evidence; do not pool them with PC samples or
silently replace the primary baseline. Device, source revision, toolchain and policy must be recorded
for every campaign, and comparisons between implementations should use the same device.

The current [primary PC campaign](/docs/project/development/milestones/00/assets/performance-baseline-pc-v1/README.md)
uses the unchanged `serial-baseline-v1` sampling and timing policy below. The
[laptop campaign](/docs/project/development/milestones/00/assets/performance-baseline-v1/README.md)
is retained separately. Both campaigns captured the
[protocol before this device designation](https://github.com/Mahkrab/EPQ/blob/dae2a2070c825846a54bc515983aad3adfab634a/docs/project/development/milestones/00/measurement-protocol.md);
their recorded protocol hashes refer to those original bytes, not this later annotation.

## Frozen policy

`serial-baseline-v1` is the project measurement decision for the
[frozen comparison family](/docs/project/development/milestones/00/reference-verification.md).
It is fixed before collecting the baseline. Inputs remain the manifest's seven falling blocks,
in ascending order: 64, 216, 512, 1,000, 1,728, 4,096 and 8,000 particles. Every full invocation
starts from an independently constructed initial state and requests 480 steps, factor-four
matched refinement, eight Jacobi iterations and checkpoints 0, 1, 120, 240 and 480.
No size, checkpoint, numerical parameter or solver work is adjusted to fit the measurement budget.

Build once with `cargo build --release --locked --offline`, the standard Cargo release profile,
no custom Rust flags, fast-math or target-specific tuning. Record Rust/Cargo versions, target,
compiler commit and LLVM version, profile, flags, application/backend IDs, build revision and binary
SHA-256. Record EPQ and Maelstrom base commits, tracked and non-ignored source-file hashes and their
combined tree fingerprint; a dirty tree is explicitly a local implementation, not a committed revision.
Record UTC collection times, OS release, kernel, architecture, CPU model and visible CPU topology,
CPU affinity, virtualisation and available memory. Do not infer physical host memory or controlled
frequency from a virtual guest. Record affinity and scheduling controls actually applied.

Before timing, replay the frozen 64-particle correctness request through the ordinary CLI and compare
all numerical output bits with its golden, excluding build context only. Retain the complete result,
checkpoint density errors, CFL diagnostics and finite-state, separation, compression, contact and
energy evidence supplied by the reference tests. Check manifest input and golden hashes before use.

For each size, run **one complete untimed warm-up**, then **three independent total-only samples**,
then **one independent instrumented stage profile**. Each invocation is a fresh process; warm-up
prepares OS code/data caches and the machine, not an in-process JIT or solver-state cache. Solver
construction is always outside timing. Run sizes and samples sequentially; do not run other project
checks concurrently. No CPU pinning, priority or frequency changes are required. Shared WSL/host
load, thermal state and scheduler migration remain threats to validity.

Each invocation has a **120-second wall-clock budget**, including its untimed setup, observations and
output. On expiry request cooperative cancellation, allow **30 seconds** to finish the current
non-interruptible stage and publish partial state, then kill if necessary. Retain actual exit status,
wall time, timeout flag, accepted work and failed-attempt time when available. A timed-out warm-up
prevents primary sampling at that size; still attempt one bounded stage profile. A failed primary
sample stops further primary samples at that size, retaining those already obtained, and does not
prevent the profile or later sizes. No partial run contributes to a full-workload summary.
A warning disqualifies a clean baseline sample while retaining its data. The practical limit is the
largest member completing warm-up and all three warning-free primary samples within this policy;
it is an observed limit of this machine and budget, not a universal algorithmic maximum.

## Timing boundary and units

All clocks are monotonic elapsed wall time; seconds are stored as binary64 JSON numbers. Primary
total begins immediately before entering the existing timestep body and ends after it returns,
including local destruction. It includes mandatory validation, allocations, acceleration, the CFL
calculation, prediction, discovery, every Jacobi iteration, plane projection, reconstruction,
cancellation polls, final checks and atomic acceptance. It excludes configuration and scene loading,
solver construction, workflow record allocation, checkpoint copies, fresh density audits, hashing,
CLI parsing, formatting, publication and process start-up. Invocation wall time is recorded separately
and never substituted for primary solver time. Failed attempts are recorded separately, never counted
as successful steps. Zero-step runs have no step measurements or rates.

The stage profile uses the same body and arithmetic, with additional clock reads. Contiguous intervals
end after the named stage and its cancellation poll, except acceptance ends just after commit:

| JSON field | Responsibility |
| --- | --- |
| `validation_and_acceleration_s` | Initial cancellation and accepted-state checks, acceleration, mandatory CFL diagnostic |
| `prediction_s` | Complete prediction snapshot |
| `neighbour_search_s` | Complete selected discovery and membership validation, including grid bounds checks, cell construction, candidate enumeration, ordering and temporary search-storage destruction |
| `jacobi_s` | Densities, multipliers, corrections and physical-density checks, accumulated across all eight iterations |
| `projection_s` | Candidate construction, ordered plane projection and position replacement, accumulated across all iterations |
| `acceptance_s` | Reconstruction, proposed-state and final-plane checks, cancellation and atomic commit |

Intervals partition the body without overlapping. Their sum may be smaller than total because clock
setup, return and local destruction lie outside them. Retain that residual, not a fabricated stage.
Stage proportions divide each stage sum by the instrumented total. Report profiles separately from
primary timings; their overhead matters most at small sizes. Measurement invariance tests compare
every accepted numerical value, checkpoint, CFL diagnostic and cancellation outcome with ordinary runs.

## Aggregation, profiling and retained evidence

Preserve every per-step timing for each attempted sample, including partial samples. For each complete
primary sample sum step seconds; report median, minimum, maximum, arithmetic mean and sample standard
deviation across the three run totals. Median time per step is median total / 480. Throughput is
`particle_count * 480 / median_total_s`, in particle updates per second. Report instrumented stage sums,
proportions and residual independently. Do not delete outliers or apply a significance claim to three
samples. The min–max range and standard deviation expose observed variability. Failed, warning-bearing
or incomplete samples remain visible and produce no complete three-sample summary.

Stage profiles at every size identify representative bottlenecks. Optimise only a demonstrated,
algorithmically neutral implementation problem; preserving arithmetic, reduction order, support,
validation and transaction semantics is mandatory. If an optimisation is made, retain before/after
samples under this policy and rerun the full correctness suite. No optimisation is required merely
because a quadratic neighbour search dominates: replacing it belongs to the next milestone.

Memory is **not measured** in this baseline. Guest available memory is environment context, not process
peak memory, allocation volume or a working-set measurement. No memory-performance claim follows.

The parent utility `python3 -m tools.baseline.main collect OUTPUT_DIRECTORY` builds the local source,
checks the manifest, records environment and source identities, and writes raw JSON plus a generated
Markdown report. `python3 -m tools.baseline.main report OUTPUT_DIRECTORY` recomputes the report without
running the solver. Destinations must be new; collection never replaces an earlier dataset. The
versioned JSON retains policy, inputs, command arguments, raw samples, correctness observations,
source/binary identities and calculated summaries. Large duplicate particle arrays are represented by
SHA-256 digests in performance samples; the separately retained correctness result remains replayable.

## Paired search comparison

The same policy also applies to serial uniform-grid measurements. No numerical or sampling setting
changes: construction and ordering occur inside discovery, and the complete transactional step stays
inside total timing. This clarification does not rewrite the original PC or laptop datasets; their
recorded protocol and collector hashes continue to identify the bytes used for those campaigns.

`python3 -m tools.baseline.main collect NEW_DIRECTORY --backend uniform-grid` selects an identified
grid series; the default remains brute force. `python3 -m tools.baseline.compare collect NEW_DIRECTORY`
collects a fresh brute-force control series followed by the grid on the same device. Each uses the
same binary, source, manifest and policy; fixed collection order remains a potential load/thermal bias.
Run the complete campaign sequentially without concurrent project checks on that device.

Before accepting paired timings, compare each clean complete attempt against the brute-force warm-up
at that size. Exclude only backend/run identity, optional timings and variable build context; preserve
physical identities, every checkpoint and final snapshot, audits, CFL diagnostics, statuses and failures.
Snapshot and input hashes retain signed-zero distinctions. The full 64-particle correctness results
remain replayable and are checked against the golden before each series. Missing clean reference or
primary sets, warnings and partial runs supply no speedup ratio. Stage profiles remain separate.

`python3 -m tools.baseline.compare report DIRECTORY` verifies raw hashes, recomputes both backend
summaries and exact comparisons, checks shared source/build/environment context, and regenerates the
comparison report. Each backend's ordinary `report` command remains available; historical datasets
without an explicit backend field retain their original brute-force interpretation and report text.
