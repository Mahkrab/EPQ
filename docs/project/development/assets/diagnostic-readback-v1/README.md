# Diagnostic-readback experiment evidence

This supports the [implementation record](/docs/project/development/performance-diagnostic-readback.md)
and [protocol](/docs/project/development/performance-diagnostic-protocol.md). Important measurements
ran sequentially on the primary PC through `ssh pc` on 22 October 2026. No new Git checkpoint,
installed application or ordinary PC checkout was created or changed.

## Identities and contents

Both exports use Maelstrom base `a21d961a27706e2aa434f20100e9cbbf8ae747e6`. Their full
source-manifest SHA-256 fingerprints are:

| Variant | Fingerprint |
| --- | --- |
| Complete error-array control | `37c5d6e64e8e578700b88261754f7485eee29fd0167907044799b7f66e63da2a` |
| Packed atomic first error | `8a89dbe1c89c429a31c97cf3ad8a6482ccc944f97a3c001899e8885399006fbc` |

These fingerprints are not commits. Both exports include the same unchanged, uncommitted
user scene; no benchmark selects it. The parent's `.gitignore` edit and that scene were
preserved. Complete source, binary, protocol and collector hashes are in `campaign/campaign.json`.
Source and binary checks ran again after collection. Locked offline release CUDA builds
used the recorded explicit revisions, toolkit and flags; no new dependency was introduced.

The retained data is split to keep each archive below 100 MiB:

- `campaign.tar.xz`: the protocol, environment, seven regression warm-up/profile pairs,
  original five timing pairs, separately declared five confirmation pairs, capacity
  admissions and fresh serial/CUDA pilots, complete candidate trajectories, four separate
  profiles, fixtures and PC verification logs;
- `comparison-controls.tar.xz`: the five previous capacity trajectories, extracted into
  the same `campaign/previous/` directory for complete physical comparisons;
- `rejected.tar.xz`: the earlier separate-reduction-kernel candidate's primary comparison,
  source/binary identities, original protocol, verification failures/reruns and exclusion note.

The rejected candidate had no meaningful 8,000-particle gain. Its later profiles started
before its final capacity collection finished; those timings are excluded. The complete
original rejected collection remains private. The published subset retains its full
five-sample-per-variant primary comparison, not a selected favourable or failed sample.

No archive contains a simulator source tree, executable, Git directory, build cache or
native Nsight report. Exact source exports and original profiles are retained privately.
Published SQLite exports remove process-environment and personal-path metadata; the
privacy map retains original/sanitised hashes, and analytical tables were checked unchanged
after vacuuming. Original CUDA inventories are retained separately from shareable inventories.

## Verification and interpretation

`summary.json` keeps the original, confirmation and combined timing summaries separate.
Confirmation was declared after the initial small, variable gain. All ten samples per
variant remain visible; no outlier was removed and no statistical-significance claim is
made. Profiles are separate from uninstrumented timings. All ordinary checks, transfers,
resets and submission/completion work remain within the declared solver boundary.

`independent-audit.json` checks raw hashes, exact physical documents and independently
summed timings. `negative-control.json` records rejection of false medians. `traces/`
reconciles kernels, completions, copies, the initial eight-byte reset and tracked allocations.
`verification.json` records source checks and actual test outcomes; `analysis-identity.json`
identifies the report/test code separately from the collector frozen before measurement.
The confirmation report helper was added after collection, not used to change the solver.

The local CPU release suite passed 239 checks; the parent suite passed 25. On the PC,
253 CUDA-enabled Rust checks passed, including opt-in hardware cases, while three existing
automatic-backend CLI tests failed. A fresh control-only CLI suite reproduced the same
three failures. Strict CUDA Clippy, formatting and native ASan/UBSan checks passed.
Initial test-build errors and corrected reruns remain visible; no failing test was suppressed.
Local raw logs remain private, with their hashes in the verification summary.

Larger capacity trajectories retain CFL warnings and lack independent density qualification.
Their unchanged physical results are regression evidence, not clean-quality benchmarks,
paired large-scene speedups, real-time attainment or a maximum-capacity result. Tracked
allocation peaks exclude untracked driver/context memory. No passing device-memory
sanitiser, actual device-loss recovery, other-platform or hosted verification is claimed.

`manifest.json` inventories the public files except itself; `archive-checks.json` verifies
archive members against the shareable data. Historical evidence is retained unchanged.

## Analyse saved evidence without starting a simulation

From the EPQ root:

```sh
diagnostic_evidence=$(mktemp -d)
tar -xJf docs/project/development/assets/diagnostic-readback-v1/campaign.tar.xz -C "$diagnostic_evidence"
tar -xJf docs/project/development/assets/diagnostic-readback-v1/comparison-controls.tar.xz -C "$diagnostic_evidence"
python3 -m tools.performance.diagnostic_report "$diagnostic_evidence/campaign"
python3 -m tests.performance.audit_sort_batch "$diagnostic_evidence/campaign" "$diagnostic_evidence/campaign/summary.json"
python3 -m tools.performance.compact_trace "$diagnostic_evidence/campaign/timelines/candidate-8000-480" --particles 8000 --steps 480 --layout compact-atomic
```

These commands inspect retained observations. They do not start, rerun or resume a simulation.
Fresh collection requires the recorded source exports, PC and protocol, not just historical paths.
