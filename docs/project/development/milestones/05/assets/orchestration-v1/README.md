# CUDA orchestration evidence

The [assessment](/docs/project/development/milestones/05/performance-orchestration.md)
retains error-only mapped diagnostic observations after the nine earlier CUDA
optimisations. Complete solver medians fall by 20.71% at 8,000 particles and
7.94% at 110,592; effects workloads improve by 23.95% and 9.76%. All 20 measured
pairs improve. Instrumented wait/readback-associated GPU idle at large size falls
from 1.620 to 1.095 ms per step. Instrumented timings are separate evidence,
not the source of the application speedup estimates.

## Boundaries and source

Measurements ran on the primary PC reached through `ssh pc`, using WSL2,
RTX 4070, CUDA 13.3.73 and Rust 1.96.0. Each workload starts a new simulation:
CUDA device 0, block 128, refinement 4, eight Jacobi iterations and 480 unpaced
steps without graphics. The 8,000-particle scene requests checkpoints
0/1/120/240/480; the 110,592-particle scene requests the final state. Effects
enable XSPH 0.01 and vorticity confinement 0.1. The prospective [protocol](/docs/project/development/milestones/05/assets/orchestration-v1/protocol.md)
sets one warm-up and five alternating measured pairs per workload, after seven
exact regression pairs. All slow samples remain. Step totals include acceptance,
host checks, transfers, launches and waits. Construction, teardown, requested
observations, JSON output and evidence processing have separate timer boundaries.

Both Git histories and the parent's gitlink remain unchanged. Maelstrom base is
`1e0085926d05c42949bb76b55d177d42a1f8f94f`; EPQ HEAD is
`1f76097a218266822cdf344c38db75ed128628a8`. Frozen exports include existing
uncommitted work and are identified by file manifests, not invented commits.

| Export | Files | Patch parent |
|---|---:|---|
| control | 190 | Maelstrom base commit |
| diagnostic | 190 | control |
| trial-0 | 191 | control |
| candidate | 191 | control |
| candidate-diagnostic | 191 | candidate |

Control exactly matches the preceding full-solver investigation's retained
candidate manifest. The final candidate preserves all nine optimisations.
The exploratory trial differs from final candidate in test/documentation details;
freshly rebuilt PTX matches. Diagnostic builds add host markers/debug information
and retain matching production CUDA PTX. Exact patch reconstruction is checked
independently of live trees, builds and timing records.

## Contents

| File | Evidence |
|---|---|
| `observations.tar.xz` | 466 members: all primary/warm-up outputs, inputs, seven regression pairs, matched final traces and overhead controls, sanitised activity/CPU tables, readers and summaries |
| `investigation.tar.xz` | 435 members: fresh control baseline, bounded alternatives, exploratory candidate, context-binding follow-up, failed attempts, sources, raw outputs and selection rationale |
| `verification.tar.xz` | 104 members: final release/hardware/boundary/execution checks, native ASan/UBSan, device diagnostics, local CPU-only check, CPU counters, tool availability and environment record |
| `*-source.json`, `*.patch` | Complete SHA-256 manifests and reconstructible source deltas for all five exports |
| `independent-audit.json` | 182 exact solver outputs in 14 equivalent input/request groups, 258 process hashes, timings and CUDA sequence/copy/wait accounting |
| `files-sha256.json`, `archive-members.json` | Expected identity and count of every retained archive member |
| `archive-readback.json`, `source-reconstruction.json` | Fresh local readback and reconstruction receipts |
| `mirror-proof.md`, `selection.md` | Diagnostic invariant, ownership argument and measured selection |
| `evidence-notes.json` | Failed collectors, measurement boundaries, environmental changes and limits |
| `final-verification.json`, `SHA256SUMS` | Final workspace/source/audit/link checks and root-file identities |

The independent reader compares physical records, accepted state, configuration,
ordered diagnostics, signed zero and requested checkpoints, excluding timings and
build revision. The 182 outputs include 178 full trajectories and four separate
16-step all-API captures. All 62 final primary/warm-up/regression records match.
The remaining outputs belong to investigation, profiler-overhead and diagnostic
campaigns and are not pooled into primary performance estimates.

Native Nsight reports and their full metadata databases, executables, full source
archives, caches and private system data are excluded. Retained SQLite tables
contain only bounded solver activities, selected CPU samples/scheduler intervals
and symbol/module basenames. Root `files-sha256.json` covers archive members;
`SHA256SUMS` covers all root files except itself.

## Independent reproduction

From the EPQ root, the following commands verify archive members and reconstruct
all five exports from the base commit without editing either checkout. Use a new
temporary extraction directory:

```sh
sha256sum -c docs/project/development/milestones/05/assets/orchestration-v1/SHA256SUMS
python3 docs/project/development/milestones/05/assets/orchestration-v1/verify-evidence.py \
  docs/project/development/milestones/05/assets/orchestration-v1 Maelstrom \
  --extract /tmp/maelstrom-orchestration-evidence
python3 /tmp/maelstrom-orchestration-evidence/audit.py /tmp/maelstrom-orchestration-evidence
cmp docs/project/development/milestones/05/assets/orchestration-v1/independent-audit.json \
  /tmp/maelstrom-orchestration-evidence/independent-audit.json
```

The checks use Python's standard library, Git and `patch`. The two verification
receipts are regenerated deterministically. `SHA256SUMS` uses paths relative to
the EPQ root, so run its command from that directory. Original GPU experiment
scripts preserve their actual scratch paths and commands; reproducing GPU runs
requires rebuilding the corresponding source export and setting those paths on
the target machine. No captured executable or primary sample is reused as a new
measurement. Timeline analysis scripts using native Nsight metadata require
recapture; the public audit runs entirely from retained tables and observations.

## Mechanism and limits

Four device records still select stage/particle/quantity errors and gate dependent
kernels. Winning minima also update a private mapped host packet. After the same
stream completion, ordinary host reads replace 21 diagnostic-copy commands per
normal step or 26 with effects. Five real data copies remain. Explicit stream
waits and launch counts are unchanged. Requested memory grows by eight device
bytes and 32 pinned host bytes per context, with one extra eight-byte setup upload;
page/allocator granularity is unmeasured. Mapped accesses on errors are genuine
system-memory traffic, outside explicit CUDA memcpy accounting. Their bus volume
was not measured. The [proof](/docs/project/development/milestones/05/assets/orchestration-v1/mirror-proof.md) explains GPU-only atomicity,
ordered host access, context-owned lifetime and failure publication.

Nsight Systems and Compute Sanitizer were already installed. No software was
installed or reconfigured, and no driver settings, registry entries or security
permissions were modified or removed. No reset/reboot occurred. Only task-owned
files, per-process environment/instrumentation and normal CUDA allocations changed;
ordinary build/JIT caches may populate without policy changes. GPU hardware
counters remain permission-blocked. WSL CPU counters and static kernel resources
do not establish GPU memory stalls, achieved occupancy or device-wide idle time.
Native Windows performance, other devices, real device-loss recovery and worst-case
cancellation latency remain unqualified.

The graph collector's initial expected-record count was incorrect; its completed
raw data were hash-checked and reused by a corrected reader. An initial C++ mirror
prototype failed a brace/indentation warning before measurement; a separate fixed
campaign is retained. Default graph tracing omits node activity, which the reader
reports as unavailable rather than zero. These limitations and rejected pinning,
copy-order and graph approaches remain in the investigation archive.
