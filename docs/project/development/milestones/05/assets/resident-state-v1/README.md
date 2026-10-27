# Accepted device buffers: primary-PC evidence

This supports the [decision record](/docs/project/development/milestones/05/performance-resident-state.md)
and [prospective protocol](/docs/project/development/milestones/05/performance-resident-state-protocol.md).
The first residency slice keeps current host snapshots and existing cancellation boundaries.
It changes accepted/working device ownership and preparation, not the device mathematics.

## Reconstruct the measured source

Start at Maelstrom
[`87145510a9e5d812066138c35f1fac82e4f593b0`](https://github.com/Mahkrab/Maelstrom/tree/87145510a9e5d812066138c35f1fac82e4f593b0).
Apply the preceding [host-coordination control patch](/docs/project/development/milestones/05/assets/host-coordination-v1/control.patch)
and [export-timing patch](/docs/project/development/milestones/05/assets/compilation-profile-v1/candidate.patch)
to obtain this control, then this directory's `candidate.patch` for the candidate.
`source-reconstruction.json` verifies all 182 candidate files against the measured export and
current source. These uncommitted states are not historical completion checkpoints.

| Export | Source fingerprint |
| --- | --- |
| Control, 181 files | `991baa1e5e8681e13004128bda3be26e05344bd79a5b798ae4a22962197f3e8d` |
| Candidate, 182 files | `5be76164b52dc187d9d3a327301877cd29a9601b68999c4d77893120cd10a502` |

`preflight-reconstruction.json` identifies the two unsuccessful qualification states. The first
retains a reproduced private-constructor compilation diagnostic; the second retains the original
strict-Clippy failure. Neither reached timing collection. Removing the later panic-test block,
restoring the unused CPU outcome and, for the first state, private constructor visibility reconstructs
their changed files. Their per-file identities remain with the failure logs.

## Retained observations

| Archive | Contents |
| --- | --- |
| `verification.tar.xz` | Protocol, source/binary/tool/input identities, environment, release and device checks, native sanitised fault tests, preflight failures, summaries, independent audit, six negative controls and local checks |
| `regression.tar.xz` | Seven exact 480-step checkpoint comparisons |
| `paired.tar.xz` | Warm-ups and five alternating pairs for each workload, original hashed outputs, process dispositions and surrounding machine readings |
| `timeline.tar.xz` | Separate complete-motion traces: physical results, analytical SQLite exports, operation windows and profiler/export logs |

Every request used CUDA device zero, block 128, refinement 4 and eight iterations. The small case
kept checkpoints 0/1/120/240/480; larger cases kept none. Enabled XSPH/confinement used 0.01 and
0.1 m/s. All raw results, including warning-bearing runs and the slower small control, are retained.
Commands, exits, monotonic durations and output hashes belong to their original attempts.

Timing samples establish whole-solver performance. Trace counts establish the removed preparation
calls/uploads with unchanged launches/readbacks; instrumented durations are separate observations.
Native fault tests prove controlled ownership transitions, not recovery from actual device loss.
Installed commands and ordinary PC checkouts were left alone.

## Recheck without a simulation

From the EPQ root, extract all four archives into one new directory:

```sh
resident_evidence=$(mktemp -d)
for part in verification regression paired timeline; do
  tar -xJf "docs/project/development/milestones/05/assets/resident-state-v1/$part.tar.xz" -C "$resident_evidence"
done
python3 -m tools.performance.gradient_reassessment report "$resident_evidence"
python3 -m tests.performance.audit_gradient_reassessment "$resident_evidence"
```

`files-sha256.json` indexes uncompressed members; `SHA256SUMS` identifies the archives, patches
and additional checks. `readback-checks.json` records a fresh extraction, all 754 member hashes,
unchanged analytical tables and exact regeneration of the report and independent audit on the laptop.
Source reconstruction, physical agreement, raw timing reconstruction and
false-summary rejection are distinct checks. Privacy receipts map original and shareable SQLite
hashes and unchanged analytical tables. Original native reports stay on the PC; only their hashes
are published. Owner labels are cleared. No whole source trees, binaries or build caches are included.
Local verification and PC measurements remain distinct, with no hosted-verification claim.
