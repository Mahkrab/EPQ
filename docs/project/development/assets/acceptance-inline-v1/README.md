# Host acceptance investigation evidence

The [record](/docs/project/development/milestones/05/performance-host-acceptance.md) explains the
component saving and failed whole-run admission. The
[original protocol](/docs/project/development/milestones/05/performance-acceptance-protocol.md) and
[confirmation protocol](/docs/project/development/milestones/05/performance-acceptance-confirmation.md)
were specified before their respective collections. The original helper is restored.

## Source identities

All exports start from Maelstrom `5120acfbcb07e94ebefd5957ad8f9afa47888be7`.
These fingerprints describe uncommitted source exports, not Git checkpoints:

| Role | Source fingerprint |
| --- | --- |
| Control and restored source | `e5c8613205873f3788baf630430302c098cd98b9d6395637405aaef244bd8198` |
| Candidate | `8c37d0e9c36fa6a8ff8f4a35916cf092570c76085ca6594ab0c5c355b580c2ad` |
| Instrumented control | `03b7e6ba8be3736fbea2b0254d8c2027e847ed8d1cf7abb0a527a4da2551d81c` |
| Instrumented candidate | `a8f360e5d195505e33eca7c8f0941ecb93597188e64776fb89d28c1fce5a6808` |

`source-identities.json` contains file hashes, including the unmeasured ordinary-inline
preparation. The candidate and control differ only by the annotation in `src/boundary.rs`.
Executable hashes and build revisions remain in campaign and confirmation metadata.

`source.patch` reconstructs 150 candidate files from the base, including earlier retained
numerical tests. Reversing `runtime.patch` reconstructs the control. The unchanged custom
scene is excluded; this does not claim that the patch alone reconstructs the complete
151-file measured catalogue or executable. `instrumentation.patch` reconstructs both
separate diagnostic overlays. `patch-checks.json` verifies those comparisons.

## Data and interpretation

Extract every archive below into the same directory to assemble `campaign/`:

| Archives | Contents |
| --- | --- |
| `campaign.tar.xz` | Environment, original protocol, seven-size regressions, initial 8,000-particle pairs, short traces, qualification and inputs |
| `capacity.tar.xz` | Five fresh serial/CUDA pilots and complete capacity observations |
| `comparison-controls.tar.xz` | Retained PC-produced physical controls |
| `paired-large-control.tar.xz`, `paired-large-candidate.tar.xz` | Initial 110,592-particle warm-ups and five samples per variant |
| `full-traces.tar.xz` | Full 110,592/480 before/after timelines |
| `diagnosis.tar.xz`, `diagnosis-candidate.tar.xz` | Separate component probes, references and input definitions |
| `screen.tar.xz` | Earlier three-pair screen, excluded from final statistics |
| `confirmation.tar.xz` | Confirmation protocol, identities, small pairs and all before/after telemetry |
| `confirmation-large-control.tar.xz`, `confirmation-large-candidate.tar.xz` | Five fresh larger pairs and their warm-ups |

`summary.json` retains the failed initial decision. `confirmation-summary.json` is separate;
`retention-decision.json` reconciles both without replacing or pooling samples. Median gains
do not satisfy the declared rule when ranges overlap. Warning-bearing results are not
independent large-fluid-quality qualification.

Independent audits reconcile raw output hashes, physical components, timings, component
windows and admission decisions. Negative controls challenge false totals and decisions.
`host-codegen.json`, `ptx-checks.json`, `traces/` and `full-motion-windows.json` explain the
target and unchanged GPU work. Before/after machine readings cannot identify the cause of
the first collection's changing run times or observe all Windows activity.

Both variants passed 258 CUDA tests with three known CLI failures. The candidate also passed strict Clippy,
formatting and native ASan/UBSan. The candidate and restored source each passed 239 CPU tests; final
parent verification passed 44 tests. Local verification metadata distinguishes the assessed
candidate from restored-source checks. No hosted verification is claimed.
Local transcript archives replace the checkout path with `[checkout]`; metadata retains
the original output hashes.

Native profiler reports and unsanitised originals remain private. Shareable SQLite files
retain analytical rows with process metadata sanitised and checked after compaction.
Archive and privacy checks cover every published member. Source snapshots, build caches,
full assembly dumps and the custom scene are not copied into these documentation archives.

These commands read saved evidence; they do not start simulations:

```sh
acceptance_evidence=$(mktemp -d)
for evidence_archive in campaign capacity comparison-controls paired-large-control paired-large-candidate full-traces diagnosis diagnosis-candidate screen confirmation confirmation-large-control confirmation-large-candidate; do
  tar -xJf "docs/project/development/assets/acceptance-inline-v1/$evidence_archive.tar.xz" \
    -C "$acceptance_evidence"
done
python3 -m tests.performance.audit_arithmetic \
  "$acceptance_evidence/campaign" "$acceptance_evidence/campaign/summary.json"
python3 -m tests.performance.audit_acceptance "$acceptance_evidence/campaign"
```
