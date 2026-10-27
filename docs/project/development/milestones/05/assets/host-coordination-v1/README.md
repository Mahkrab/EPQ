# Host coordination: primary-PC evidence

This supports the [attribution record](/docs/project/development/milestones/05/performance-coordination.md)
and [prospective protocol](/docs/project/development/milestones/05/performance-coordination-protocol.md).
It compares a normal control with temporary CPU-clock instrumentation, not an optimisation candidate.
The ordinary Maelstrom checkout and installed PC executable were unchanged.

## Sources and observations

Both 180-file exports derive from Maelstrom
[`87145510a9e5d812066138c35f1fac82e4f593b0`](https://github.com/Mahkrab/Maelstrom/tree/87145510a9e5d812066138c35f1fac82e4f593b0).
Apply `control.patch` to that commit, then `diagnostic.patch` for the probe. The latter changes
only `src/cuda/solver.rs`. These are measured working states, not new Git checkpoints.
`source-reconstruction.json` records successful reconstruction and agreement with the unchanged
normal source. It also checks that the current overlay generator reproduces the formatted probe.

| Export | Source fingerprint |
| --- | --- |
| Control | `0383da2a3781bfe8e7a4e1518fa38e258611a2502d7194c822a0ad9236b1c4e0` |
| Diagnostic | `f7a88dd6ef9ddc422572f226bfad7121163a97f589635a5772211f6efadabc2c` |

Separate Cargo targets and independent native compilation verified identical intended CUDA code
in both binaries. Per-file, binary, input, protocol and collector hashes remain in the archives.
The overlay's duplicate-application guard was added after export; this does not change generated
Rust, and the measured diagnostic patch remains authoritative.

| Archive | Contents |
| --- | --- |
| `verification.tar.xz` | Protocol, source manifests, environment, build/test/Clippy/format logs, exact inputs, summary, independent audit, negative controls, local test result and privacy mapping |
| `paired.tar.xz` | Warm-ups and three alternating measured pairs for each of the three workloads, with hashed outputs, exits, commands, monotonic durations and surrounding machine readings |
| `timeline.tar.xz` | Separately declared control-only full-motion GPU trace: solver result, export logs, sanitised analytical database and operation windows |

The primary PC used a Ryzen 9 7900X and RTX 4070 under WSL2, driver 610.88, CUDA 13.3.73 and
Rust 1.96.0. All simulations used 480 unpaced steps, refinement 4, eight iterations, CUDA device
zero and block size 128, without rendering. The 8,000-particle workload kept checkpoints
0/1/120/240/480; both 110,592-particle workloads kept none. The enabled workload used XSPH 0.01
and confinement 0.1 m/s. Larger-run warnings are preserved and do not establish physical quality.

Probe intervals separate pure CPU work from packing and blocking native wrappers. Instrumented
totals expose observer effects and are never primary optimisation timings. The GPU-ranking
follow-up was declared after the host results, before its capture; `ranking-followup.md` records
that boundary. Its times are not pooled with the paired solver totals.

## Recheck without running a simulation

From the EPQ root, extract all three archives into one new directory:

```sh
coordination_evidence=$(mktemp -d)
for part in verification paired timeline; do
  tar -xJf "docs/project/development/milestones/05/assets/host-coordination-v1/$part.tar.xz" -C "$coordination_evidence"
done
python3 -m tools.performance.coordination report "$coordination_evidence"
python3 -m tests.performance.audit_coordination "$coordination_evidence"
```

The independent reader reconstructs raw physical agreement, sums, early/evolved windows, medians
and fractions. Four altered host summaries/results were rejected. `independent-ranking-audit.json`
records the independent launch/transfer/completion and operation-window checks; a fifth negative
control rejected an altered correction duration.

`files-sha256.json` indexes uncompressed archive members. `SHA256SUMS` identifies the archives,
patches and additional checks. Native profiler reports stay private; `privacy.json` maps original
and shareable SQLite hashes and verifies unchanged analytical tables. Trace summaries retain
their original database identities. Archive owner labels are cleared. No whole source trees,
executables, build caches or hosted-verification claims are included.
