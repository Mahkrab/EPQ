# Threaded CPU correctness verification

This is local correctness evidence collected on 17 October 2026, not a performance campaign.
The [collection record](/docs/project/development/milestones/02/assets/verification-v1/collection.json)
identifies the uncommitted Maelstrom worktree by its full base commit, per-file hashes and combined
fingerprint. It also records the release binary hash, verifier hashes, compiler/build environment,
commands, frozen reference hashes, execution settings and exit status of every invocation.

The [comparison report](/docs/project/development/milestones/02/assets/verification-v1/report.json)
contains **36 complete comparisons** against the unchanged goldens: the 27-particle unforced lattice
for 12 steps and the refined 64-particle falling block for 480 steps. Each fixture has fresh serial
brute-force and grid controls. Each threaded setting (1, 2, 3 and 7 workers) has an ordinary run, a
measured run, a separate stage profile and a replay of its ordinary result. Original CLI JSON bytes
are retained beside the report. Every run completed without warnings or failure.

All comparisons pass `reference-comparison-v1` with **exact binary32 acceptance**, including signed
zero. Every checkpoint and final position/velocity component has zero maximum absolute and RMS error;
all identities, inputs, requests, audits, CFL values, warning flags and completion classifications
agree. There is no first divergent checkpoint or CFL step. Backend/run identity, explicit execution
settings, build context and optional timings are excluded from physical equality; the collector
separately checks recorded backend/worker settings. The report includes both sides' metadata and
per-checkpoint audit values, applied limits, counts and worst particle/component locations.

Reproduce from the EPQ checkout with cached dependencies:

```sh
cargo build --manifest-path Maelstrom/Cargo.toml --release --locked --offline
python3 -m tools.verification.main collect /tmp/maelstrom-threaded-verification
python3 -m tools.verification.main report \
  docs/project/development/milestones/02/assets/verification-v1
```

Collection requires a new directory. `--workers 1 2 3 7` is the default; other explicitly selected
settings generate their own evidence. Reporting rechecks candidate/reference hashes and recalculates
judgements without executing simulation. To replay a retained threaded result from Maelstrom:

```sh
./target/release/maelstrom replay \
  ../docs/project/development/milestones/02/assets/verification-v1/00064-uniform-grid-3-ordinary.json \
  --format json --quiet
```

The [implementation record](/docs/project/development/milestones/02/phases/phase-00-threaded-cpu.md)
explains independent numerical, lifecycle and failure tests, including one-step comparisons across
all seven family sizes through 8,000 particles. These retained full-run results cover the two
goldens only. Timings here test instrumentation invariance; they do not establish PC scaling or
speedup. Memory use, cross-platform bitwise replay and hosted behaviour were not measured.
