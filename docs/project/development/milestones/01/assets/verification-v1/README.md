# Serial grid correctness verification

This is local correctness evidence for the serial grid, collected on 17 October 2026. It is not a
performance campaign. The [comparison report](/docs/project/development/milestones/01/assets/verification-v1/report.json)
identifies the exact uncommitted Maelstrom worktree by per-file hashes and a combined fingerprint,
the release binary hash, compiler/build context, commands, frozen input/golden hashes and comparison
policy. Its base commit identifies the starting implementation, not a committed grid endpoint.

The later Maelstrom checkpoint
[`b179e6e42b4efd6e269d6eb35fbee50dba4fcfa1`](https://github.com/Mahkrab/Maelstrom/tree/b179e6e42b4efd6e269d6eb35fbee50dba4fcfa1)
matches all 80 recorded source-file hashes. The original report and result files are retained unchanged.

The retained candidates are [the 27-particle lattice](/docs/project/development/milestones/01/assets/verification-v1/small-lattice.json)
over 12 steps and [the refined 64-particle falling block](/docs/project/development/milestones/01/assets/verification-v1/falling-block.json)
over 480 steps. Both are ordinary complete CLI result documents, including every CFL diagnostic,
checkpoint density audit and final accepted snapshot. Each also replayed exactly through the public
CLI. The manifest's reference files and configuration remain unchanged.

Comparison uses `reference-comparison-v1` with zero numerical tolerance. The complete documents
agree after removing only top-level backend, metadata backend/run identity, build context and optional
measurements. Signed zero is compared as binary32 bits. All checkpoint and final position/velocity
maximum and RMS errors are zero, with no structural, density, CFL, warning or failure disagreement.
The report retains both original reference and candidate hashes; reference goldens stay in Maelstrom.

To reproduce the retained runs, build with `cargo build --release --locked --offline` in `Maelstrom`,
then execute each report command from that checkout. The report records the exact step counts,
refinement and checkpoints. To replay either candidate without its TOML inputs:

```sh
./target/release/maelstrom replay \
  ../docs/project/development/milestones/01/assets/verification-v1/falling-block.json \
  --format json --quiet
```

Replay validates recorded inputs and backend; it does not certify a saved outcome. The
[phase record](/docs/project/development/milestones/01/phases/phase-00-serial-uniform-grid.md)
explains the independent geometry, full-run, failure and cancellation tests that qualify this agreement.
Variable build context may differ on reproduction. This evidence does not establish cross-platform
bitwise equivalence, full-duration equivalence at every larger size, memory use or a PC speedup.
