# Shallow-resolution evidence

This directory retains the complete scheduled raw observations for the
[shallow-collision investigation](/docs/project/development/milestones/05/shallow-resolution.md),
including unsuccessful controls. It contains 66 immutable requests: 64 complete simulations and
two initial-only geometry rejections. The primary-PC copy lives under
`~/.local/share/maelstrom-experiments/shallow-resolution-v1`; its `work/` directory contains
the isolated build tools and binaries, outside this evidence manifest. The repository directory
is the second durable copy. Neither canonical copy relies on temporary storage. These are local
and primary-PC files, not a published archive or a Git checkpoint.

## What the records mean

- `protocol.json` predates the experiments and fixes the physical collision, refinement, criteria
  and observation interval. `depth-protocol.json` corrects the planned rounded depth labels to
  the actual mass-derived depths. `control-matrix.json` records the controlled extensions;
  `sampler-protocol.json` and `initial-geometry-protocol.json` explain initialisation sensitivity
  and the subsequent geometry correction. Earlier protocols and raw observations are retained.
- `runs/*/request.json` gives the exact invocation, binary hash, protocol hash and parameters.
  `collection.json` records completion or rejection, raw/gzip hashes, bytes and solver-only timing.
  `stderr.txt` preserves native diagnostics. Requests start fresh simulations; they do not resume
  saved observations.
- Every `states.bin.gz` is a complete raw stream for that request's scheduled observations.
  The collector flushes and fsyncs raw files, compresses, fsyncs and verifies decompression before
  removing the redundant uncompressed file. Initial and final states and all 0.05 s snapshots are
  present for complete simulations; intermediate solver steps are not saved. The two rejected
  `valid-ceil-L1.25` and `valid-ceil-L1.5` requests retain their initial state and diagnostic, with
  non-zero exit status. They are deliberate geometry rejections, not missing archives.
- `audit.jsonl` contains independent measurements for each complete physical trajectory;
  `physical-summary.json` gives extrema and the final observation. Timing-only runs are instead
  checked against the matching six-second trajectory prefix in `timing-equivalence.json`.
- `initial-geometry.json` checks each raw initial state's inset and separation. Eleven completed
  old controls and two initial-only rejections fail this check; all are listed in
  `initial-geometry-rejections.json`. Failed initialisations are excluded from positive
  qualification, even if their final centroid happens to look accurate.
- `assessment.json` applies the declared physical budgets, exposes each criterion separately and
  declines production admission. `all_declared_pass` refers to this spatial study's sampled
  checks; it does not assert the previous study's energy criterion or a complete production gate.
  `macroscopic_pass` deliberately excludes transient density and settled quietness; it cannot
  qualify a dynamic fluid policy. Energy remains in every audit and is discussed in the report.
- `cost-summary.json` contains all five measured samples per resolution after warm-up.
  `timing-protocol.json` defines the primary-PC serial alternating order. Timers cover 0.5
  simulated seconds from the collision start, not sustained six-second or CUDA throughput.
- `readback.json` verifies decompressed hashes, complete frame structure, exact observation steps
  and complete endpoints. It counts 5,106 observations and 1,204,730,520 uncompressed bytes across
  all requests. `mirror-readback.json` records independent primary-PC checksum verification;
  `SHA256SUMS` covers all evidence files except itself. No excluded or slow raw sample was deleted.
- `environment-and-preservation.json`, `source-identities.json` and `reference-equivalence.json`
  tie compiler settings, sources, binaries and preservation checks to the observations.
  `audit-provenance.json` and `independent-reader-checks.json` record independent calculations.
  `*.volume-grid-control.json` inside the selected run directories retains the finer audit-grid
  controls. `local-tests.log` records twelve focused local tests.

The independent volume diagnostic stores raw observed and analytic-slab reconstructions at
thresholds 0.45, 0.50 and 0.55. The reported equivalent volume adds their difference to M/ρ;
it removes measurement convolution bias, not solver error. Its physical reference is never passed
to the solver. Particle p95 height plus half spacing and geometric column volumes are separate,
explicitly resolution-dependent diagnostics. The interparticle density criterion compares an
off-particle kernel field with a continuum-convolved slab, not with 1000 kg/m³ across missing
air-side support. Observations every 0.05 s do not certify intermediate-step bounds.

## Source and binary identities

`sources/solver-v1.cpp` through `solver-v5.cpp` are the exact isolated source versions, linked by
SHA-256 in `source-identities.json`. These small standalone experimental snapshots originate from
the parent working tree at EPQ `814f88a7f4122b1b24ea645b210d89e1200a0c44`, with uncommitted experimental
additions; they are not historical committed checkpoints. No copied repository, Git metadata or
build artefacts are included. Production Maelstrom remains
`250932784790ba26cdc55fc38a877ccefacbf054` with unrelated pre-existing working changes.

Version 1 produced the main ladder. Version 2 reuses search allocations without changing
arithmetic; full six-second n=6 and n=12 streams match version 1 exactly. Version 3 permits fractional
depths and supplied the original auxiliary controls and timings. Version 4 adds the alternative
ceil-stratum initializer. Version 5 corrects auxiliary initial geometry and rejects infeasible
aligned strata before stepping. Collision initialisation/arithmetic is unchanged between versions.
All timing streams are identical to their qualified ladder trajectory prefixes. Bitwise agreement
establishes those harness relationships only; physical admission uses independent references.

## Reproduction

The following commands run from the EPQ root. The verification commands **read saved observations**;
they do not start or resume simulations. `uv` supplies the explicitly pinned audit dependencies.

```sh
python3 -m tools.performance.spatial_retain docs/project/development/milestones/05/assets/shallow-resolution-v1
uv run --with numpy==2.5.4 --with scipy==1.18.1 python -m tools.performance.spatial_initial docs/project/development/milestones/05/assets/shallow-resolution-v1
python3 -m tools.performance.spatial_assessment docs/project/development/milestones/05/assets/shallow-resolution-v1
uv run --with numpy==2.5.4 --with scipy==1.18.1 python -m unittest tests.performance.test_spatial -v
```

These readers regenerate their derived JSON records. To preserve the checksum manifest byte for
byte, run them on a separate evidence copy. The independent full audit refuses to overwrite an
existing `audit.jsonl`; remove only derived audit files in that separate copy before rerunning it:

```sh
uv run tools/performance/spatial_audit.py /path/to/separate-copy/runs/ladder-n12
uv run --with numpy==2.5.4 --with scipy==1.18.1 --with matplotlib==3.11.2 python -m tools.performance.spatial_plot /path/to/separate-copy
```

To **start new simulations**, compile the corresponding source snapshot identified by each
request's binary hash, on the primary PC for comparable timing:

```sh
c++ -std=c++17 -O3 -Wall -Wextra -Werror -fopenmp -ffp-contract=off \
  /path/to/evidence/sources/solver-v5.cpp -o /path/to/new-work/solver
python3 -m tools.performance.spatial_campaign /path/to/new-evidence /path/to/new-work/solver ladder
```

The new evidence directory must first contain an explicitly chosen copy of `protocol.json`.
Never reuse a canonical run label: the collector rejects existing directories. `flat`, `controls`,
`depth` and `timing` are other supported campaign phases. To reproduce a particular historical
request, use its archived source version and exact `request.json` parameters through
`spatial_campaign.run`, changing the destination and binary path. Historical invalid initialisers
must not be silently replaced with version 5 and called reproductions. Binary hashes may vary with
toolchain/build paths; compare physical outcomes against the stated criteria.

## Raw binary format

All streams use little-endian binary64 arrays, as written/read on the recorded x86 hosts:

1. Four uint32 values: magic `0x50424634`, particle count N, wall-sample count W, planned step count.
2. Eleven doubles: dt, support h, number-density rest sum, particle mass, box upper x/y/z,
   kernel id 2, nominal spacing, collision inset and distance target.
3. W wall positions, each three doubles; fixed for the entire request.
4. Repeated frames: uint32 step, N positions (three doubles each), then N velocities.

No header, frame or failed stream is inferred from a plot. Readback verifies the raw hashes against
the collector, exact scheduled step sequence and planned endpoint for successful requests. The
initial-only failure format remains readable and is explicitly distinguished from a complete run.
