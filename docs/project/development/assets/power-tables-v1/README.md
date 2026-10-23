# Correction profiling and rejected table-placement evidence

The [record](/docs/project/development/performance-correction-profile.md) explains the
findings and rejection. The [protocol](/docs/project/development/performance-correction-protocol.md)
owns the prospective workload and admission criteria. Original table placement is restored;
the shared numerical tests and profiling tools remain.

## Source and verification

All exports start from Maelstrom `5120acfbcb07e94ebefd5957ad8f9afa47888be7`. These are
uncommitted source identities, not Git checkpoints:

| Role | Source fingerprint |
| --- | --- |
| Initial diagnosis | `5beb47272ad832dcb79133f5fa140f244a177359885646fd112babba11b0b962` |
| Matched control and final source, including new tests | `e5c8613205873f3788baf630430302c098cd98b9d6395637405aaef244bd8198` |
| Rejected candidate | `31b9763aef262e669f190f2a4c7685baf63cdb84255aa5b2802f54f6bac817d2` |

`source-identities.json` contains file hashes; campaign metadata records executable hashes
and build revisions. The matched exports differ only in `native/power.cuh`. The final
working tree matches the independently tested control. Its source qualification is recorded
in `final-verification.json` and `pc-verification.json`.

`candidate.patch` reconstructs all 150 assessed source files from the base commit, including
the previous numerical tests and the new correction module. `patch-checks.json` verifies
that reconstruction and the control obtained by reverting only the power header. The
unchanged untracked custom scene is excluded and no benchmark selects it. This is not a
claim that the patch alone reconstructs the complete measured catalogue or executable.

The candidate and control each passed 258 CUDA tests with the same three existing CLI
failures. Strict Clippy, formatting and native ASan/UBSan passed. Local preparation passed
239 CPU and 37 parent tests, compilation and formatting. Local logs are in
`local-verification.tar.xz`, with the checkout path replaced by `[checkout]`; original hashes
are retained. `local-verification.json` describes that derived export.

## Retained data

Extract these archives into the same directory to assemble `campaign/`:

| Archive | Contents |
| --- | --- |
| `campaign.tar.xz` | Environment, protocol, seven-size regressions, 8,000-particle paired samples, short traces, PC checks and inputs |
| `capacity.tar.xz` | Fresh serial/CUDA pilots and complete capacity diagnostics |
| `comparison-controls.tar.xz` | Retained PC-produced physical controls |
| `paired-large-control.tar.xz` | Warm-up and five fresh 110,592-particle control samples |
| `paired-large-candidate.tar.xz` | Corresponding candidate samples |
| `full-traces.tar.xz` | Full 110,592/480 control/candidate timelines and physical outputs |
| `diagnosis.tar.xz` | Initial full timeline, CPU sampling, counter-access failure, reference inputs and additional stage profile |

`summary.json`, `independent-audit.json` and `negative-controls.json` reconcile raw hashes,
physical observations, warning schedules, timings and the rejection decision. All five
samples per variant remain, including slow large samples. Warning-bearing capacity runs
are not independent fluid-quality qualification.

`ranked-costs.json`, `full-motion-windows.json`, `large-stage-profile.json` and
`cpu-sampling-summary.json` separate the diagnostic boundaries. `traces/` and their checks
reconcile kernel, completion and copy counts. `ptx-checks.json` verifies unchanged table
initialisers and power-function source alongside the changed generated loads. Reported
entry-kernel attributes are not achieved occupancy measurements.

Counter capture failed with `ERR_NVGPUCTRPERM`; there are no successful GPU counter metrics.
User-space CPU sampling retained 4,115 IP events, but 4,109 backtraces were broken and kernel
samples were unavailable. Leaf counts over the invocation cannot establish packing or
allocation percentages within solver time. No security settings were changed.

Native profiler reports remain private. Shareable SQLite exports retain analytical rows
with process-environment metadata sanitised. Privacy checks verify those rows after
compaction; archive checks verify every member. `source-checks.json` identifies the measured
candidate before restoration; the final source is recorded separately. `review-checks.json`
and `manifest.json` cover the final evidence and repository review. No hosted, other-platform,
actual device-loss or passing device-memory-sanitiser claim follows.

To reanalyse data without running simulations:

```sh
correction_evidence=$(mktemp -d)
for evidence_archive in campaign capacity comparison-controls paired-large-control paired-large-candidate full-traces diagnosis; do
  tar -xJf "docs/project/development/assets/power-tables-v1/$evidence_archive.tar.xz" \
    -C "$correction_evidence"
done
python3 -m tools.performance.arithmetic report "$correction_evidence/campaign"
python3 -m tests.performance.audit_arithmetic \
  "$correction_evidence/campaign" "$correction_evidence/campaign/summary.json"
python3 -m tools.performance.compact_trace \
  "$correction_evidence/campaign/timelines/control-110592-480" \
  --particles 110592 --steps 480 --layout compact-stages
```
