# Complete CUDA solver profiling evidence

The [assessment](/docs/project/development/milestones/05/performance-full-solver.md)
records measured bottlenecks, the deferred containment change, performance,
regressions, validation, tooling limitations and the retention decision. The
[protocol](/docs/project/development/milestones/05/assets/full-solver-v1/protocol.md)
preceded collection; [containment reasoning](/docs/project/development/milestones/05/assets/full-solver-v1/containment-proof.md)
explains the unchanged numerical/error boundary and buffer lifetime.

Control is the 189-file retained integer-quartic build, including all eight prior
optimisations. Candidate has 190 files. This package identifies frozen exports,
not new commits: Maelstrom HEAD is `1e0085926d05c42949bb76b55d177d42a1f8f94f`;
EPQ HEAD is `1f76097a218266822cdf344c38db75ed128628a8`. Neither repository's
history, branches, tags, remotes or gitlink changed. The ordinary PC checkout
and installed solver were not replaced. Performance used independent temporary
exports on the primary PC. Every workload command starts a new simulation.

The candidate adds a deferred plane certificate to the existing final velocity
copy. It preserves numerical vectors, the eight prior optimisations, CUDA owner
thread, diagnostics, cancellation and accepted-state promotion. The original
host containment loop remains the error path after effects and host validation.
It adds 16 DtoH bytes per non-empty step and 32 requested device bytes, with no
additional launch, transfer or stream wait. The report distinguishes requested
capacity from physical allocator granularity and kernel time from overlapping
host/driver time.

## Source reconstruction

Export the Maelstrom base commit into a new directory, apply `control.patch`
with `patch --batch -p1`, then verify all `control-source.json` hashes. Applying
`candidate.patch` next produces the final live candidate. The source readback
checks the complete file set, not just changed files. Diagnostic and exploratory
patches have explicit parents:

| Patch/export | Parent | Files |
|---|---|---:|
| control | named Maelstrom base commit | 189 |
| candidate | control | 190 |
| diagnostic | control | 189 |
| candidate-diagnostic | candidate | 190 |
| trial-0 | control | 189 |
| trial-verification | trial-0 | 190 |
| candidate-prequalification | control | 190 |

The prequalification source retains the old-capacity native fixture failure.
The trial qualification overlay contains the new tests; the original trial
export was restored and reverified after that separate check. Its untouched CLI
is bound again to fresh PTX equal to final candidate PTX. Full exports, binaries,
PTX, private registry data and native Nsight reports are not copied into the
repository. Source manifests and patches reconstruct the required exports.

## Retained observations

- `observations.tar.xz`: all 62 primary/regression/warm-up outputs, input copies,
  source/binary/PTX identities, process commands/exits and monotonic durations,
  12 final traces reduced to privacy-limited activity tables, candidate CPU
  samples/scheduler, stage and queue readers, and final collector failures/resume.
- `investigation.tar.xz`: initial control samples, three-pair instrumentation
  overhead comparisons, eight initial traces, CPU hardware counters and samples,
  the 12 exploratory outputs, diagnostic source generator, collection commands,
  source/binary/PTX identities and raw failures. Sampling/profiling overhead is
  measured separately from primary performance; campaigns are not pooled.
- `verification.tar.xz`: release, explicit CUDA, Clippy/format and native ASan/UBSan
  evidence; device memory/race/synchronisation/initialisation checks; baseline
  versus candidate deferred-error fixture and context-teardown observations;
  static function resources; local CPU release log; raw failed checks.
- `tooling.tar.xz`: read-only tooling/configuration receipts, ordinary and root
  counter-denial records, package installation logs, both separately retained
  Windows/WSL boundary campaigns, explicit final compiler receipts, standalone
  Driver API microbenchmark, and privacy-limited registry recovery receipt.

`files-sha256.json` binds 1,079 retained archive members. `archive-readback.json`
records complete local member verification; `source-reconstruction.json` records
all seven reconstructed exports. `independent-audit.json` independently checks
146 solver records in 11 equivalent input/request groups, all 62 final outputs,
paired arithmetic, exact launch sequence/types and transfer/synchronisation
counts. It excludes only measurements and build revision from numerical checks.
Ordered arrays, signed zero, configuration, requested checkpoints, accepted final
state and diagnostic records remain part of the comparison.

The final five-pair comparison uses 480 unpaced steps, block 128, refinement 4
and eight Jacobi iterations at 8,000 and 110,592 particles, with effects disabled
and enabled. Effects mean XSPH 0.01 and confinement 0.1. Small primary/regression
runs retain checkpoints 0/1/120/240/480; large runs retain final state and ordered
step records. Completed-step timing includes all host/device solver work and
acceptance. Solver construction/teardown, requested observations, serialisation
and evidence collection are separate. All process outputs, slower samples and
warnings remain. Seven single-pair regressions are correctness checks with
reported timings, not a statistically precise small-scene performance campaign.

## Readers and reproduction

On a machine with the base Maelstrom commit, this read-only verifier checks member
hashes and reconstructs source in temporary directories:

```sh
python3 verify-evidence.py /absolute/path/to/full-solver-v1 /absolute/path/to/Maelstrom
```

Extract the observation and investigation archives into a separate scratch
folder to rerun the independent numerical/timing reader:

```sh
python3 scratch/audit.py /absolute/path/to/scratch
```

The reader writes its summary in scratch. Collectors and timeline readers retain
the recorded `/tmp/maelstrom-fullprofile-20261028` root; recreate that scratch root
or deliberately change their `w` variable. `analyse.py` and
`analyse-candidate.py` use sanitised activity/scheduler tables, so their disjoint
wall partitions can be regenerated without the private native profiler reports.
`queue-analysis.py` reports overlapping queue metrics separately; adding them to
wall contributions would double-count. CPU sample exports retain phase/symbol
and module basename but omit unresolved addresses and native report metadata.

Fresh precise PTX is checked inside each corresponding ordinary/diagnostic
executable before collection and source manifests after collection. Source
identity checks, output comparisons and storage stay outside primary timers.
The final diagnostic build differs in markers/debug/frame pointers; the CUDA
PTX is the same as its ordinary counterpart. Static resource attributes are
not achieved hardware counters. GPU counters were denied even as WSL root;
no cache-hit, DRAM throughput, achieved-occupancy or memory-stall results exist.
The supplementary `nsys-counter-check.json` confirms the same permission failure
for Nsight Systems GPU-metric discovery under both ordinary and root invocation.

## Tooling and failures

[evidence-notes.json](/docs/project/development/milestones/05/assets/full-solver-v1/evidence-notes.json)
explains setup changes, the registry incident/recovery, early qualification
failures, collector schema corrections, the trial overlay and timing limits.
The erroneous registry operation was stopped and the affected 233 keys/501
values and ACLs restored before baseline measurements. Private hives and raw
registry values remain outside the package. The driver was not reset or rebooted.
Three originally absent profiling values remain intentionally configured;
[rollback-profiling-settings.ps1](/docs/project/development/milestones/05/assets/full-solver-v1/rollback-profiling-settings.ps1)
removes only those values when run in elevated PowerShell. Installed tools remain
available. The temporary GUI task/process and loaded recovery hive were removed.

The full optional leak check exits 86 on allocations deliberately held until
private-context destruction in both builds. It is retained as a finding, not a
passing leak qualification. Access checking passes across the CUDA component
suite, and race/sync/init checking passes for the new certificate. No production
cleanup redesign was added to suppress this existing teardown classification.

The initial installed-scene failure is left intact outside isolated test roots.
The two test-draft compile errors were corrected without changing production
contracts. The native capacity fixture was updated for the new trailer and
sanitised native checks rerun. Incorrect SQL assumptions and an unsupported
Nsight sampling flag are preserved; completed raw captures were hash-verified
and reused by corrected readers, not replaced with fresh favourable samples.

The report's native Windows figures come only from the second same-source
microbenchmark campaign with explicit compiler receipts. The earlier campaign
remains separate. Neither is a complete Windows Rust/CUDA solver benchmark.
No memory-stall hypothesis, microbenchmark ratio or profiler timing substitutes
for the primary whole-solver paired comparison.
