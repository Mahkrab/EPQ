# Compilation and block-size evidence

This supports the [measurement record](/docs/project/development/milestones/05/performance-compilation-profile.md)
and its [prospective protocol](/docs/project/development/milestones/05/performance-compilation-profile-protocol.md).
The primary-PC campaign measures existing work; it does not change the numerical method, CUDA
block-size default, renderer or publication policy. Installed commands and ordinary PC checkouts
were left alone.

Both source exports derive from Maelstrom
[`87145510a9e5d812066138c35f1fac82e4f593b0`](https://github.com/Mahkrab/Maelstrom/tree/87145510a9e5d812066138c35f1fac82e4f593b0).
Apply the preceding [control patch](/docs/project/development/milestones/05/assets/host-coordination-v1/control.patch)
to that commit, then `candidate.patch` for the timing implementation. `source-reconstruction.json`
checks the complete 181-file candidate and its agreement with the measured local source. These
are uncommitted working states, not completion checkpoints.

| Export | Source fingerprint |
| --- | --- |
| Control, 180 files | `0383da2a3781bfe8e7a4e1518fa38e258611a2502d7194c822a0ad9236b1c4e0` |
| Candidate, 181 files | `991baa1e5e8681e13004128bda3be26e05344bd79a5b798ae4a22962197f3e8d` |

| Archive | Contents |
| --- | --- |
| `verification.tar.xz` | Protocol, source/binary/tool identities, environment, build and verification logs, exact inputs, summaries, independent audit, six negative controls and driver-JIT resource query |
| `headless-8000.tar.xz` | Warm-up and three measured requests at each of four block sizes, with checkpoints |
| `headless-110592.tar.xz` | Corresponding large disabled-effect requests, without checkpoints |
| `headless-effects.tar.xz` | Corresponding large enabled-effect requests, without checkpoints |
| `compile.tar.xz` | Warm-up and three requests for each compile setting, compressed manifests, actual PNG hash receipts, bundle-validation outcomes and surrounding machine readings |

All simulations use 480 unpaced steps, refinement 4 and eight iterations on CUDA device zero.
The enabled case uses XSPH 0.01 and confinement 0.1 m/s. Compilation uses hardware graphics at
1280×720. Strides 1 and 4 produce 481 and 121 images, with identical hashes at common steps.
Warnings remain numerical warnings; successful bundle validation establishes integrity separately.
The raw process files retain commands, exits, monotonic wall durations and output hashes.

The profile partitions export entry through the point before manifest construction. The command
wall remainder also contains CLI work, finalisation and teardown; it is not a pure file-write timer.
Component medians are calculated independently and need not sum to the median command wall time.
The separately declared `resource-followup.md` owns the subsequent static driver query. Its probe,
build/run logs and identities are retained; it launches no kernels and supplies no achieved counters.

To inspect the retained evidence without starting a simulation, extract the five archives into
one new directory from the EPQ root:

```sh
compilation_evidence=$(mktemp -d)
for part in verification headless-8000 headless-110592 headless-effects compile; do
  tar -xJf "docs/project/development/milestones/05/assets/compilation-profile-v1/$part.tar.xz" -C "$compilation_evidence"
done
python3 -m tools.performance.compilation "$compilation_evidence"
python3 -m tests.performance.audit_compilation "$compilation_evidence"
```

`files-sha256.json` indexes uncompressed archive members; `SHA256SUMS` identifies the archives,
patch and reconstruction receipt. `readback-checks.json` records successful fresh extraction, all 932
member hashes, and exact regeneration of both reports on the laptop without a simulation. Owner labels are cleared, and retained text is checked for
personal home paths. Original images remain in the isolated PC workspace; the archives contain
no source trees, executable binaries, build caches or image payloads. Local and PC checks are
identified separately. No hosted verification is claimed.
