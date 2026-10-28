# Reprofiling the ten-optimisation CUDA solver

**Do not retain either prototype.** The production solver remains exactly the
ten-optimisation control. The [assessment](/docs/project/development/milestones/05/performance-reprofile-ten.md)
explains the measured GPU fill saving, whole-solver regressions, limitations and decision.

The control has 191 source files and matches the preceding orchestration
investigation's candidate manifest. Maelstrom base remains
`1e0085926d05c42949bb76b55d177d42a1f8f94f`; EPQ remains
`1f76097a218266822cdf344c38db75ed128628a8`. No Git history, branches, tags,
remotes or parent gitlink changed. Frozen exports include prior uncommitted work.

## Experiment boundaries

All important measurements ran through `ssh pc` on the Ryzen 9 7900X/RTX 4070
under WSL2. Each command starts a new simulation: CUDA 0, block 128, refinement 4,
eight Jacobi iterations, 480 unpaced steps and no graphics. Four workloads cover
8,000/110,592 particles with and without XSPH 0.01 and confinement 0.1. Small primary
and regression runs request checkpoints 0/1/120/240/480; large runs request final
state. Complete-step timing includes host checks, transfers, submission, waits,
cancellation and acceptance. Construction, teardown, requested observations,
output and audits have separate boundaries.

The primary cache comparison uses one warm-up and five alternating pairs per
workload after full qualification and seven exact regression pairs. The lane
scheduling and initial cache trials use one warm-up and two exploratory pairs.
No samples were discarded or replaced. Traces explain mechanisms; ordinary,
unprofiled measurements determine application performance. Experiments are not pooled.

| Export | Patch parent | Meaning |
|---|---|---|
| control | Maelstrom base commit | All ten retained optimisations |
| diagnostic | control | Host markers and debug/frame-pointer instrumentation |
| trial-0 | control | Rejected spatial scheduling probe |
| candidate | control | Qualified, measured and rejected lookup cache |

The cache reuses the sort allocation's spare half for eight column starts. It
adds no allocation, launch, wait or transfer, but raises shared-entry registers
52→60. Fill improves in matched GPU captures; primary medians regress 11.04%,
3.73% and 4.74% in small, large and small-effects workloads. Large effects improve
1.96%, with all five pairs faster. This trade-off does not justify retention.

## Retained material

| File | Contents |
|---|---|
| `observations.tar.xz` | 563 members: fresh baseline/environment/identities, primary measurements, seven regression pairs, matched GPU captures and clean CPU follow-up |
| `inputs.tar.xz` | Two files: counted capacity scene and its default configuration; bundled scenes reconstruct from the source export |
| `investigation.tar.xz` | 266 members: both exploratory trials, scripts, logs, protocol, audits, CPU/queue analysis, GPU stages, resource queries and failed counter attempt |
| `verification.tar.xz` | 47 members: release/hardware/integration/Clippy/fmt/native checks and device diagnostics |
| `*-source.json`, `*.patch` | Four complete manifests and reconstructible source exports |
| `independent-audit.json` | 166 exact solver outputs, process hashes, primary statistics and CUDA sequence/copy/wait accounting |
| `clean-audit.json` | Eight additional clean-follow-up outputs compared with audited controls; 174 distinct exact records altogether |
| `clean-analysis.json`, `gpu-stages.json`, `resources.json`, `clean-overhead.json` | Disjoint CPU/GPU wall partitions, stage timing, static resource and overhead observations |
| `files-sha256.json`, `archive-members.json` | Expected hashes and counts for every archive member |
| `archive-readback.json`, `source-reconstruction.json`, `final-verification.json` | Independent readback, source and final workspace receipts |
| `SHA256SUMS` | Root-file identities, excluding itself |

Physical comparisons exclude measurements and build revision; accepted state,
configuration, signed zero, requested checkpoints and ordered diagnostics remain.
Main observations contain 166 full trajectories. The clean follow-up adds four
ordinary diagnostic-build runs and four rich captures. The failed one-step Nsight
Compute attempt is retained as tooling evidence and excluded from performance claims.

Native Nsight reports, full metadata databases, executables, complete source trees
and build/JIT caches are excluded. Public SQLite tables retain bounded solver
activities, CPU samples/scheduler intervals and symbol/module basenames. Source
patches and hashes establish identity without mutable temporary builds.

## Reproduction

From the EPQ root, with Python's standard library, Git and `patch`:

```sh
sha256sum -c docs/project/development/milestones/05/assets/reprofile-ten-v1/SHA256SUMS
python3 docs/project/development/milestones/05/assets/reprofile-ten-v1/verify-evidence.py \
  docs/project/development/milestones/05/assets/reprofile-ten-v1 Maelstrom \
  --extract /tmp/maelstrom-reprofile-evidence
python3 /tmp/maelstrom-reprofile-evidence/audit.py /tmp/maelstrom-reprofile-evidence
python3 /tmp/maelstrom-reprofile-evidence/clean-audit.py /tmp/maelstrom-reprofile-evidence
cmp docs/project/development/milestones/05/assets/reprofile-ten-v1/independent-audit.json \
  /tmp/maelstrom-reprofile-evidence/independent-audit.json
cmp docs/project/development/milestones/05/assets/reprofile-ten-v1/clean-audit.json \
  /tmp/maelstrom-reprofile-evidence/clean-audit.json
```

Use a new extraction directory. Verification recreates four source exports
without changing either checkout. Original GPU scripts preserve actual scratch
paths; rerunning experiments requires reconstructing/building the selected export
and adapting paths on the target PC. Timeline exporters requiring native Nsight
metadata need recapture; the public numerical/activity audits use retained tables.

## Tooling and uncertainty

No installation, system-wide driver/registry/security change, reset or reboot was
performed. Only task files, per-process environment/instrumentation and ordinary
CUDA allocations changed. Previous task Cargo target directories were reused for
control/diagnostic builds; normal build/JIT caches may populate without policy
changes. Both Nsight GPU-metric discovery and an actual Nsight Compute attempt
reported insufficient counter privileges. No setting was changed to obtain access.
Static resources do not establish achieved occupancy or GPU memory stalls.

An initial resource-probe compile omitted the `native` include directory; the
task-only correction succeeded. The original probe script is retained, and the
report records the failure. Initial exploratory traces partially overlapped a
short compile. Clean CPU captures ran after task builds, GPU tests, resource
queries and the CPU audit completed. Profiling overhead and scheduling variability
remain material: the earlier 1.750 ms idle estimate is not a fixed implementation
constant or a native Windows baseline. Real device-loss recovery and performance
on other devices/platforms remain unqualified.
