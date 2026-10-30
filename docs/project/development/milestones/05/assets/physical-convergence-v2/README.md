# Physical-convergence evidence

The [decision report](/docs/project/development/milestones/05/physical-convergence.md) explains
the corrections, unsuccessful approaches and remaining shallow-fluid failure. Production was
not changed. The combined physical gate remains false; no cost measurements were made.

## Durable observations and readback

The canonical evidence is this directory in the local EPQ worktree. A complete second copy is
retained on the primary PC at
`/home/oliver/.local/share/maelstrom-experiments/physical-convergence-v2`.
Neither location is temporary storage. `mirror-readback.json` records checksum verification of
the copied package. No system settings, repository history or installed commands were changed.

There are **54 successful simulation requests**, two failed/interrupted requests with retained
raw streams, and two pre-execution setup-failure receipts. Each run owns immutable `request.json`,
complete scheduled `states.bin.gz`, stderr, independent `audit.jsonl` and `summary.json`.
Observations include every particle position and velocity, the initial state, fixed wall positions,
physical constants and checkpoint step numbers. The observation period is 0.05 simulated seconds;
the complete requested observations are retained, not only selected frames or density summaries.
No every-step or every-iteration observation claim is made.

The collector fsyncs raw/compressed files and immutable request/summary records, verifies decompressed
SHA256 before removing the redundant uncompressed copy, and rejects reuse of an existing request
directory. All **110,444,168 uncompressed bytes**, including failed-request bytes, were read back
and checked. Every successful stream was re-audited using the final independent reader, with
**zero changes to common numerical fields**. See `readback.json` and each `readback-audit.jsonl`.
This addresses the earlier temporary-directory archive loss; it does not restore that older data
or constitute a power-loss/disaster-recovery test.

`protocol.json` was written before runs. The contact, distribution, kernel, resolution and extent
supplements were written before their respective experiments. Original acceptance thresholds were
not loosened. `assessment.json` applies the gates and records decreasing timestep/iteration shape
changes, together with the failed combined original-scene gate. It is evidence for the report's
engineering judgement, not an automatic production-retention rule.

## Source and physical-model identity

The implementation under investigation remains Maelstrom
`250932784790ba26cdc55fc38a877ccefacbf054`; the independent experimental source is in parent
tooling. `sources/` retains the small standalone C++ variants used as the model evolved.
`source-identities.json` identifies maintained tools, tests, source snapshots and build flags.
`environment-and-preservation.json` records compilers, CPU environments, Git identities and
native-source preservation. The reference uses binary64 and precise host arithmetic. It has no
production GPU API, vorticity/viscosity post-process, cancellation callback or rollback contract.

The reference builds use:

```sh
c++ -std=c++17 -O3 -Wall -Wextra -Werror -ffp-contract=off \
  tools/performance/convergence_solver.cpp -o solver
c++ -std=c++17 -O3 -Wall -Wextra -Werror -ffp-contract=off \
  tools/performance/convergence_audit.cpp -o audit
```

The exact command is retained for each request. Parameter positions are:

```text
solver SCENE DT DURATION ITERATIONS WALL_DENSITY CLAMP EPSILON_H2 SCALE PRESSURE_H2 KERNEL REFRESH [CONTACT [CONTACT_DISTANCE [WALL_INSET]]]
```

Kernel 0 uses Poly6 density/Spiky directions, 1 uses Poly6 and its derivative, and 2 uses Wendland C2
and its derivative. Rest density and mass are recalibrated with the kernel; spacing is 0.05 m and
support 0.1 m. The archived initial state and wall array make scene geometry independently available.
These commands start new simulations. Observation files are accepted-state recordings, not resumable
solver checkpoints. Binary headers use little-endian 32-bit integers and IEEE binary64 on the tested
x86 hosts: magic `0x50424632` stores seven constants; `0x50424633` adds a kernel identifier before
the wall array. Each frame stores a step index, all positions and then all velocities.

The campaign runner is
[convergence_campaign.py](/tools/performance/convergence_campaign.py). It pins executables by hash
so solver and auditor cannot change during a request. The early, unpinned screen predates that
collector repair; final readback audits establish a common numerical reader for every retained
stream. The collector's current `qualification` phase describes the C2 point-plane model, including
the known failing shallow scenes. It must not be interpreted as an admission command.

The independent reader uses direct all-pairs summation, with no solver grid, gradients or multipliers.
It reports particle-site density, fluid-only and wall-supported density, analytical bulk/free-surface
groups, uniform Eulerian probes, geometry, separation, energy and centre-of-mass motion. Empty bulk
groups are unavailable diagnostics, not passes. Hydrostatic shape admission uses the mean over
t=5–6 s for convergence and checks every observed state in that window against the accuracy limits.

## Failures and checks

Two concurrent initial setups exposed non-atomic executable-cache publication. One local depth
request and the first primary 128-pass setup failed before simulation; their setup receipts remain.
Atomic temporary-file publication repairs that race and has a parallel regression test. A subsequent
primary retry passed a newly added optional argument to an older executable and failed before any
observations; that empty raw stream and stderr remain. Optional zero-inset arguments are now omitted
for compatibility. The local 128-pass six-second request reached its 600 s operational timeout;
its partial raw stream is retained. The successful primary retry has its own identity and is not
substituted into that failed request. None of these is labelled a physical solver defect.

Local verification:

```sh
python3 -m unittest tests.performance.test_convergence tests.performance.test_physical_accuracy -v
```

All twelve passed; `local-tests.log` is the retained output. Derivatives use independent central
differences, C2 normalisation uses radial quadrature, wall support uses a corner-lattice oracle, and
ballistic motion uses the integration formula. Additional checks cover truncated observations,
invalid kernels, concurrent pinning and rejection of density-only admission.

To re-audit the entire package into new derived files, use a disposable **durable** scratch location
and a copy of the evidence directory. Remove the generated `readback-audit.jsonl` files from that
working copy first; preserve the canonical originals. The verifier refuses to overwrite existing
derived readback audits:

```text
python3 -m tools.performance.convergence_retain EVIDENCE_COPY AUDITOR DURABLE_SCRATCH
python3 -m tools.performance.convergence_assessment EVIDENCE_COPY
uv run tools/performance/convergence_plot.py EVIDENCE_COPY
```

The plots use recorded raw coordinates and independent audit outputs. They are orthographic particle
projections, not a rendered animation or validated fluid-surface reconstruction. Fresh Rust, CUDA,
binary32/backend and production failure-path qualification were not performed. Pressure accuracy,
capillarity, spatial asymptotics, moving boundaries and engineering-CFD accuracy remain unqualified.

`SHA256SUMS` covers all files of this evidence package except itself. The primary directory also
contains task-owned build/cache files outside that manifest; they are not required to interpret the
retained numerical observations.
