# Cooperative integer sorting: primary-PC evidence

This supports the [implementation record](/docs/project/development/milestones/05/performance-cooperative-sort.md)
and [prospective protocol](/docs/project/development/milestones/05/performance-cooperative-sort-protocol.md).
The control includes retained gradient-prefix reuse. Both exports are based on Maelstrom
[`87145510a9e5d812066138c35f1fac82e4f593b0`](https://github.com/Mahkrab/Maelstrom/tree/87145510a9e5d812066138c35f1fac82e4f593b0),
with [control changes](/docs/project/development/milestones/05/assets/cooperative-sort-v1/control.patch)
and the subsequent [sorting patch](/docs/project/development/milestones/05/assets/cooperative-sort-v1/candidate.patch).
These exports are measured working states, not new Git checkpoints.

## Contents and provenance

| File | Evidence |
| --- | --- |
| `verification.tar.xz` | Protocol, 179/180-file source identities, binary/native-code hashes, build/test logs, exact inputs, environment, paired summary, independent audit, negative controls and historical-reader compatibility |
| `regression.tar.xz` | Both variants' seven bundled 64–8,000-particle trajectories and surrounding machine readings |
| `paired.tar.xz` | Warm-ups and five alternating measured pairs at 8,000 particles and two separately identified 110,592-particle workloads |
| `timelines.tar.xz` | Separate full-motion disabled-effect profiles, sanitised analytical databases and early/evolved operation windows |
| `kernel-resources.json` | Driver-loaded function attributes, code/executable sizes and corresponding artifact hashes |
| `source-reconstruction.json` | Successful reconstruction from both patches and identification of the subsequent documentation-only change |

The source fingerprints are control
`a10a3f67d77ebf7d0ac0e8163e2fecd72981cc3f9d6b8851b48491762715d0e1` and candidate
`de68151b746deadb902f43a41ee1a47793d89d52ccf67c0ee02ffa7fe48d7e98`.
Separate Cargo targets and independent CUDA compilation checked that each executable contained
its own intended code and not the other's. No installed binary or ordinary PC repository was replaced.

The PC used a Ryzen 9 7900X and RTX 4070 under WSL2, driver 610.88, CUDA 13.3.73 and Rust 1.96.0.
All requests used 480 steps, refinement 4, eight iterations, CUDA device zero and block size 128,
without pacing or rendering. The 8,000-particle case kept checkpoints 0/1/120/240/480. Larger cases
had none; the enabled case used XSPH 0.01 and confinement 0.1 m/s. Their 259/181 warning-bearing
steps remain visible and do not establish final fluid quality.

Each request retains commands, exits, monotonic wall durations, stdout/stderr and hashes.
Machine readings sit outside invocation timing and cannot establish all Windows activity.
`summary.json` keeps every pair, including slow samples and overlapping ranges; the written
assessment decides retention. The audit independently checks physical records, raw step totals,
medians, ratios, kernel correlations, dimensions and operation windows. Four negative controls
reject changed timings, physical results, sort durations and launch dimensions. The updated
reader also successfully rechecks the previous prefix campaign without changing its data.

The candidate's extra 480 kernels and unchanged completion/transfer counts are verified from
the traces. Driver attributes report zero local/shared allocation and 46/45 registers; these are
not occupancy measurements. CUDA code grew from 108,114 to 188,930 bytes and executables from
4,459,264 to 4,540,320 bytes. These costs remain separate from the measured solver improvement.

## Recheck retained results

From the EPQ root, extract the four archives into one new directory:

```sh
sorting_evidence=$(mktemp -d)
for part in verification regression paired timelines; do
  tar -xJf "docs/project/development/milestones/05/assets/cooperative-sort-v1/$part.tar.xz" -C "$sorting_evidence"
done
python3 -m tools.performance.gradient_reassessment report "$sorting_evidence"
python3 -m tests.performance.audit_gradient_reassessment "$sorting_evidence"
```

The existing collector/report interface now accepts `--experiment cooperative-sort` for collection;
its default preserves the earlier gradient comparison. The audit reads the retained experiment
identity to account for the additional candidate kernel. Analysis does not rerun a simulation.

`files-sha256.json` indexes uncompressed archive contents; `SHA256SUMS` identifies the archives,
patches and additional checks. The source reconstruction reproduces both measured exports and
confirms every current runtime/test input. The only later Maelstrom difference clarifies the CUDA
guide's fill/sort description and is identified by both hashes. No binaries, build caches or whole
source trees are included.

Native profiler reports remain private. `privacy.json` maps original to sanitised SQLite identities
and verifies unchanged analytical tables. Trace summaries retain their original database hashes;
use that mapping for shared exports. Archive owner labels are cleared. The initial local trace-offset
test failure is retained with personal path prefixes removed and original/shared hashes recorded;
the final 68-test run passed. No hosted or device-memory-sanitiser pass is claimed.
