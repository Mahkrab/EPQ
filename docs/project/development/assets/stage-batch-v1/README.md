# Logical-stage batching evidence

This supports the [implementation record](/docs/project/development/milestones/05/performance-stage-batching.md)
and [protocol](/docs/project/development/milestones/05/performance-stage-protocol.md). Verification, matched
measurements and separate profiler runs were sequential on the primary PC through `ssh pc`
on 22 October 2026. Installed applications and ordinary PC checkouts were not changed.

## Source identities

Both complete dirty exports use Maelstrom base
[`a21d961a27706e2aa434f20100e9cbbf8ae747e6`](https://github.com/Mahkrab/Maelstrom/tree/a21d961a27706e2aa434f20100e9cbbf8ae747e6).
Their fingerprints hash the sorted, compact JSON map of all 150 file hashes:

| Variant | Source fingerprint |
| --- | --- |
| Individual-pass readback | `a08c3dd34b6e23079a1b7a8ac7c503222d2c0524fe5ceb81c1b6308977dd5d08` |
| Logical-stage groups | `02171272227b13474b9978744d504015f7674a054253c98533e9b0037584b256` |

These are not commits or tags. The control's file hashes match the preceding diagnostic
experiment's candidate; its differently serialised aggregate fingerprint is not a source
change. Both exports include the same unchanged custom scene, which no benchmark selects.
The user's parent `.gitignore` and that scene were preserved. Complete source/binary,
protocol and frozen collector identities are in `campaign/campaign.json`; post-collection
checks verify those bytes remained unchanged. Exact source exports are retained privately.

## Contents and interpretation

`campaign.tar.xz` contains the frozen protocol, environment, seven regression warm-up/profile
pairs, two primary warm-ups and five timing samples per variant, capacity admissions and
fresh serial/CUDA pilots, complete candidate trajectories, four separate traces and PC
verification logs. `comparison-controls.tar.xz` supplies the preceding capacity trajectories
under the same `campaign/previous/` directory. Neither archive contains simulator source,
executables, Git data, build caches or native Nsight reports.

`summary.json` retains all samples, medians, ranges, standard deviations, per-step summaries,
invocation/setup/teardown times and real-time factors. The matched 8,000-particle medians
are 2.725 and 1.928 s: 1.413× faster, or 29.2% less solver time. Larger single diagnostic
times are not paired speedups; their retained CFL warnings and absent independent density
qualification remain limitations. No statistical-significance or general-platform claim is made.

`independent-audit.json` checks raw process hashes, complete physical documents, independent
timing sums and capacity decisions. `negative-control.json` records rejection of a false
candidate median. `traces/` reconciles identical kernel counts, fewer completion/readback
calls, unchanged copy bytes and the larger four-slot reset/allocation. Traces are not primary
timing samples or total driver/context-memory measurements.
`trace-reanalysis.json` confirms the sanitised SQLite produces the same analytical results;
the trace summaries retain both original and shareable database hashes.

`verification.json` records 255 passing PC Rust checks and the same three CLI failures
reproduced in the control, strict CUDA Clippy, formatting, native ASan/UBSan and local checks.
The initial missing Plane-constructor argument and incorrect control test-target name remain
in the original logs; corrected verification preceded measurement. A subsequent full run
used Cargo's no-fail-fast option to cover targets after the known CLI failures. No test was
suppressed. `campaign/verification-sources.json` associates each attempt with its source.
Local raw logs remain private, with their commands, results and hashes in the summary.

Original profiler files remain private. Shareable SQLite exports redact process environments,
hostnames and personal paths; `campaign/privacy.json` maps original and shareable hashes.
`privacy-checks.json` verifies analytical rows after vacuuming, and `privacy-scan.json` checks
the exported files including decompressed stdout. `archive-checks.json` checks every archive
member; `manifest.json` inventories public files except itself. Historical evidence is unchanged.

Actual device-loss recovery, a passing device-memory sanitiser, other platforms, hosted checks,
large-scene independent density qualification and final evaluation remain unverified. Branches,
commits, tags and the parent gitlink are unchanged; these exports do not establish a Git checkpoint.

## Inspect saved evidence without starting a simulation

From the EPQ root:

```sh
stage_evidence=$(mktemp -d)
tar -xJf docs/project/development/assets/stage-batch-v1/campaign.tar.xz -C "$stage_evidence"
tar -xJf docs/project/development/assets/stage-batch-v1/comparison-controls.tar.xz -C "$stage_evidence"
python3 -m tools.performance.sort_batch report "$stage_evidence/campaign"
python3 -m tests.performance.audit_sort_batch "$stage_evidence/campaign" "$stage_evidence/campaign/summary.json"
python3 -m tools.performance.compact_trace "$stage_evidence/campaign/timelines/candidate-8000-480" --particles 8000 --steps 480 --layout compact-stages
```

These commands read retained observations; they do not start, rerun or resume a simulation.
Fresh collection requires the declared source exports, PC and protocol, not historical paths alone.
