# Reused-reservation candidate evidence

This supports the [investigation record](/docs/project/development/milestones/05/performance-reservation-reuse.md)
and its [prospective protocol](/docs/project/development/milestones/05/performance-reservation-protocol.md).
The primary-PC comparison and independent audit are complete. **The candidate was rejected:**
neither declared workload showed a clear runtime gain. The original runtime is restored.

- `source-identities.json` identifies the separate complete control and candidate exports
  by file hashes. Both start from Maelstrom `5120acfbcb07e94ebefd5957ad8f9afa47888be7`.
  They are uncommitted source identities, not historical Git checkpoints. Build revisions
  and measured executable hashes are recorded separately in the campaign metadata.
- `candidate.patch` reconstructs all 149 tracked candidate files from that commit, including
  the previous trial's retained Rust regression tests. `patch-checks.json` records the check.
  The unchanged untracked custom scene is excluded and is not selected by any benchmark.
- `verification.json` records local preparation checks. `local-verification.tar.xz` contains
  derived logs with the checkout path replaced by `[checkout]`; original hashes are retained.
- `pc-verification.json` summarises actual candidate/control checks. Their original logs
  are in the campaign archive. The negative native control intentionally aborts at the
  new assertion against the original bridge; it is not a candidate test failure.
- `final-verification.json` and `final-verification.tar.xz` separately identify and verify
  the restored source, fingerprint `5beb47272ad832dcb79133f5fa140f244a177359885646fd112babba11b0b962`.
- `summary.json`, `independent-audit.json` and `negative-controls.json` reconcile raw samples,
  physical results and the admission decision. Five samples per variant at each size are
  retained without filtering. Larger runs keep their existing CFL warnings.
- `traces/`, `independent-traces.json`, `trace-checks.json` and `kernel-resources.json`
  reconcile counts, allocation peaks, physical output and reported kernel attributes.
  `generated-kernel-checks.json` verifies byte-identical PTX between variants.
- `consecutive-waits.json` identifies consecutive recorded waits and their instrumented
  API durations. Context push/pop was not recorded by default; these are not complete
  reservation spans or primary timings. The method and count checks are included.
- `historical-trace-checks.json` records exact reproduction of the four preceding analytical
  summaries with the extended reader. It is compatibility evidence, not a candidate profile.
- `collector-manifest.json`, `final-source-checks.json`, `source-checks.json` and
  `analysis-identity.json` record source, executable and analysis integrity.
- `privacy-checks.json` and `privacy-scan.json` verify analytical rows after sanitisation
  and check the shareable files. Native reports and original SQLite remain private.
- `archive-checks.json` verifies every packaged member. `historical-checks.json` and
  `review-checks.json` record preserved evidence, user files and Git boundaries.
  `manifest.json` inventories the complete bundle, excluding itself.

Five archives extract into one `campaign/` tree:

| Archive | Contents |
| --- | --- |
| `campaign.tar.xz` | Environment, protocol, seven-size regressions, paired 8,000-particle samples, traces, PC checks and input definitions |
| `capacity.tar.xz` | Fresh independent serial/CUDA pilots and complete capacity diagnostics |
| `comparison-controls.tar.xz` | Retained PC-produced physical comparison controls |
| `paired-large-control.tar.xz` | Warm-up and five fresh 110,592-particle control samples |
| `paired-large-candidate.tar.xz` | Corresponding candidate samples |

The initial local checks passed 239 CPU and 30 parent tests, compilation and formatting.
Both the candidate and restored PC CUDA suites passed 257 tests with the same three known
CLI failures; strict Clippy, formatting and native ASan/UBSan passed. All opt-in hardware
checks ran. No hosted, other-platform, actual device-loss, passing device-memory-sanitiser
or independently qualified large-fluid result follows.

To reanalyse the retained data without running a simulation:

```sh
reservation_evidence=$(mktemp -d)
for evidence_archive in campaign capacity comparison-controls paired-large-control paired-large-candidate; do
  tar -xJf "docs/project/development/assets/reserve-reuse-v1/$evidence_archive.tar.xz" \
    -C "$reservation_evidence"
done
python3 -m tools.performance.arithmetic report "$reservation_evidence/campaign"
python3 -m tests.performance.audit_arithmetic \
  "$reservation_evidence/campaign" "$reservation_evidence/campaign/summary.json"
python3 -m tools.performance.compact_trace \
  "$reservation_evidence/campaign/timelines/candidate-8000-480" \
  --particles 8000 --steps 480 --layout compact-reserved
```
