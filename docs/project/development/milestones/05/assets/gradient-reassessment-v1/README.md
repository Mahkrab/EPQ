# Ordered gradient reuse: primary-PC evidence

This supports the [reassessment](/docs/project/development/milestones/05/performance-gradient-reassessment.md)
and its [protocol](/docs/project/development/milestones/05/performance-gradient-reassessment-protocol.md).
The valid campaign compares separate release CUDA builds from Maelstrom
[`87145510a9e5d812066138c35f1fac82e4f593b0`](https://github.com/Mahkrab/Maelstrom/tree/87145510a9e5d812066138c35f1fac82e4f593b0)
and the [candidate patch](/docs/project/development/milestones/05/assets/gradient-reassessment-v1/candidate.patch).
Neither source export is a new Git checkpoint. Source identities list all 179 tracked file hashes;
compiled executable and independently compiled CUDA hashes identify what was actually measured.

## Contents

| Archive | Retained evidence |
| --- | --- |
| `verification.tar.xz` | Protocol, source/binary identities, build and test commands/output, environment, exact inputs, summaries, independent audit, negative controls and privacy manifest |
| `regression.tar.xz` | Both variants' seven 64–8,000-particle trajectories and surrounding machine readings |
| `paired.tar.xz` | Warm-ups and five alternating pairs at 8,000 particles and 110,592 particles, plus a separate 110,592-particle case with both effects enabled |
| `timelines.tar.xz` | Separate full-motion disabled-effect profiles, analytical SQLite exports and early/evolved operation summaries |
| `invalid-first-build.tar.xz` | Disqualified first campaign: both executables contained control CUDA code despite different Rust build identifiers; never combine its samples with the valid campaign |

The PC used a Ryzen 9 7900X and RTX 4070 under WSL2, driver 610.88, CUDA 13.3.73 and Rust 1.96.0.
All requests used 480 steps, refinement 4, eight iterations, CUDA device zero and block size 128.
Only the 8,000-particle case requested checkpoints 0/1/120/240/480. The enabled case used XSPH 0.01
and confinement 0.1 m/s. Larger disabled/enabled cases retained 259/181 CFL-warning steps; these
are equivalent-work runtime comparisons, not new physical-quality qualifications.

Each process retains its exact command, exit, monotonic duration, stdout/stderr and hashes.
GPU and Linux readings sit outside invocation timing; they do not establish all Windows activity.
`summary.json` describes every pair and requires a written assessment. It makes no automatic
retention decision. The independent audit checks raw durations, physical records and profile rows;
negative controls reject changed timing, physical and profile summaries.

`embedding-verification.json` establishes the corrected campaign's distinct native code. Each
executable contains its own independently compiled CUDA code and not the other's. The invalid
archive records the opposite finding for its candidate and keeps the original protocol and collector
hashes. That build mistake was corrected before retaining the optimisation.

## Recheck the valid results

From the EPQ repository root, extract the four valid archives into one new directory:

```sh
gradient_evidence=$(mktemp -d)
for part in verification regression paired timelines; do
  tar -xJf "docs/project/development/milestones/05/assets/gradient-reassessment-v1/$part.tar.xz" -C "$gradient_evidence"
done
python3 -m tools.performance.gradient_reassessment report "$gradient_evidence"
python3 -m tests.performance.audit_gradient_reassessment "$gradient_evidence"
```

The first command reconstructs descriptive timing evidence; the second independently checks it,
including operation windows from the traces. `files-sha256.json` indexes the uncompressed evidence;
`SHA256SUMS` identifies the archives, source patch and reconstruction check. The
[source check](/docs/project/development/milestones/05/assets/gradient-reassessment-v1/source-reconstruction.json)
confirms that applying the patch to the full starting Maelstrom commit reproduces the candidate's
file hashes and that current source matches. No compiled binaries, Cargo caches or
whole source trees are included.

Native profiler reports remain private. `privacy.json` records their hashes and maps original to
sanitised SQLite exports, checking that analytical tables stayed unchanged. Trace summaries retain
their original database identities; use that mapping for the shareable exports. The corrected
campaign includes raw PC verification logs and a separate local session record; the local CPU
console transcript was not archived. No hosted or device-memory-sanitiser pass is claimed.
