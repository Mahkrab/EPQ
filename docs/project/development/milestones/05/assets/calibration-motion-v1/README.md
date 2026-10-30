# Calibration and motion evidence

This directory retains the raw evidence for the
[physical-qualification report](/docs/project/development/milestones/05/calibration-motion.md).
Canonical observations live here and on the primary PC under
`~/.local/share/maelstrom-experiments/calibration-motion-v1`. Neither copy depends on temporary
storage. The primary `work/` directory contains isolated executables and pinned executable objects;
it is outside this evidence manifest. No repository, Git metadata, binary build artefact or cache
is copied into this directory. These are local/primary-PC records, not published checkpoints.

## Authority and interpretation

`protocol.json` predates experiments and fixes the physical hypotheses, accuracy/conservation
budgets, material viscosities and qualification sequence. Dated supplements record later tests
before they run: viscosity quadrature and slab refinement, restart ablations, physical mass
convention and unforced momentum/iteration controls. No tolerance is loosened after observing a
failure. `qualification-matrix.json` explains the bounded scene/resolution matrix.

The default collision holds physical mass 52.23230175835605 kg and geometric envelopes fixed.
Particle-site correction and wall-volume controls vary separately. Runs named `geometric-*`
instead change mass to match physical geometric volume: collision M=54 kg, deep tank M=288 kg.
Their hydrostatic reference follows the actual mass in the raw header. They are distinct physical
inputs, not replacement baselines. The inherited initial envelopes contain a dilute sampling
relative to rho=1000 kg/m³; they cannot simultaneously represent fully dense 0.3 m cubes.

Density admission uses the candidate's independently recalculated site estimator. Raw unit-integral
particle-site compression is also retained as `raw_site_p95_compression`. Off-particle field density
always uses actual masses and the unit-integral kernel, without a site subtraction or ratio.
Centroid, geometric height, volume, field accuracy, energy and motion remain separate criteria.
The volume statistic compares the measured reconstruction with an identically reconstructed
analytic slab; it is an independent diagnostic correction, not solver feedback or exact sharp volume.

Quietness is assessed against the original t=5–6 s budget. The extended run starts from a saved
five-second state and integrates seven new seconds: its local clock 0–7 corresponds to physical
t=5–12. Restart diagnostics are not admitted as new fluid policies. Zeroing initial velocity is
explicitly a causal experiment, never a proposed damping method. Contact-off and unforced-strain
tests are also diagnostics. Their misleading hydrostatic or settling labels must not enter admission.

## Retained files

- `runs/*/request.json` records the exact command, parameters, executable and protocol hashes,
  restart input identity and UTC start. `collection.json` records completion, raw/gzip checksums,
  byte counts, native diagnostics and finish time. Requests are immutable and existing labels
  cannot be overwritten.
- `states.bin.gz` contains all scheduled positions and velocities, including initial/final states,
  every 0.05 simulated seconds. The schema is exactly the
  [preceding spatial format](/docs/project/development/milestones/05/assets/shallow-resolution-v1/README.md#raw-binary-format):
  magic `0x50424634`, counts, eleven double constants, fixed wall positions and step/p/v frames.
  Physical particle mass is explicit; the header number-density sum is not a substitute mass.
- `ledger.jsonl.gz` contains **every accepted step**, with K/U, linear/angular momentum per kg,
  prediction and reconstructed/accepted velocities' energy, density/plane/contact/viscous work,
  correction sizes, active constraints, wall impulses and explicit-viscosity row bound.
  `displacement_rms_sum` is sqrt(sum over passes/particles of squared displacement divided by N),
  not the net step correction; `max_displacement` is the largest single-pass particle correction.
  Window work integrates intervals after the lower endpoint; both endpoint states enter kinetic
  extrema. Intermediate velocity is displacement from the step's old position divided by dt. Accepted
  velocities include the subsequent viscosity update, if configured.
- Raw particle and ledger files are flushed/fsynced, compressed with deterministic gzip metadata,
  fsynced and decompressed for SHA-256 readback before redundant uncompressed files are removed.
  `stderr.txt` retains native diagnostics. Failed numerical hypotheses are retained as completed
  observations with failed physical criteria; a zero native exit code does not establish accuracy.
- `audit.jsonl` independently recalculates physical quantities at stored particle states.
  `physical-summary.json` gives extrema and the endpoint. `energy-summary.json` reconciles all
  accepted steps, the gravity prediction identity, internal/external impulses, stage work and
  independent saved-state K/U/momentum. The audit never imports the native solver's calibration
  constant: it separately sums the physical-rest lattice.
- `assessment.json` exposes individual criteria and spatial comparisons, declines production
  admission and excludes restart/short diagnostic runs. A single case passing cannot establish a
  converged material model. Strict calibration, original 5% centroid, field, quietness and energy
  are separate checks. The independent viscosity boundary test can reject a model even when
  some full-PBF cases pass their aggregate statistics.
- `inputs/` and per-restart `initial.bin` retain exact restart arrays. `restart-provenance.json`
  identifies the source five-second observations. `diagnostic-summary.json` independently checks
  unchanged restart trajectories, unforced linear/angular momentum and physical t=5–12 energy.
- `shear-validation.json` retains the first rejected bulk viscosity test.
  `shear-support-validation.json` retains the support comparison at unchanged dimensional nu.
  `slab-validation.json` and `slab-spatial-convergence.json` contain native vertical mode profiles
  at all scheduled times for free-slip slab tests. Their exact Fourier reduction tests the fixed
  viscosity operator, not an unrun high-resolution PBF simulation.
- `slab-independent-matrix-checks.json` forms the same prescribed-position operator independently
  from the analytic radial derivative, verifies native evolution against its eigen-decomposition,
  and compares explicit Euler with the exact discrete matrix exponential. This separates spatial
  boundary error from timestep error. No effective viscosity is fitted.
- `environment-and-preservation.json`, `worker-policy.json`, `source-identities.json`,
  `audit-provenance.json` and `research-readback.json` record source/runtime provenance. Early
  experiments used the ordinary OpenMP wait policy. Later children use process-local passive
  waiting through explicit immutable wrappers or their launch environment; numeric observations
  match in the recorded equivalence control. This changes no system setting. Concurrent physics
  and instrumentation make native `solver_s` unsuitable for comparative performance claims.
- `rebuild-readback.json` confirms that all three native fluid binaries rebuild exactly from
  the retained snapshots and header on the primary PC. `reference-equivalence.json` binds the
  raw instrumentation/wait-policy controls to earlier retained observations. These are identity
  checks, separate from physical admission. `operator-binaries.json` identifies local probe
  builds; `verification.json` summarises the checks actually performed.
- `readback.json` verifies exact particle schedules, endpoints, raw/gzip hashes and ledger step
  sequences. `mirror-readback.json` records independent primary-PC verification. `SHA256SUMS`
  covers the retained evidence except itself. `local-tests.log` records the focused checks.

Every-step energy work is a telescoping account, not a claim that each positive component
independently supplies unphysical energy. Static density and plane corrections must recover the
known semi-implicit gravity-prediction loss. Accepted total-energy growth, stage closure and
independent initial conditions distinguish this from the demonstrated raw calibration-driven
energy injection in the unforced physical-rest test.

## Sources and reproduction

The source boundary is EPQ `814f88a7f4122b1b24ea645b210d89e1200a0c44` with explicitly uncommitted,
isolated additions. Maelstrom stays at `250932784790ba26cdc55fc38a877ccefacbf054` with unrelated
pre-existing work preserved. Source snapshots have SHA-256 identities; they are not historical
Git checkpoints. `solver-v1.cpp` adds calibration and stage measurement to the spatial reference;
version 2 adds a separate viscosity-support search; version 3 adds the explicit geometric-mass
control. The shared viscosity header is unchanged across these fluid binaries.

The archived old shear/slab versions and their source hashes identify unsuccessful tests.
The slab version-1 source was reconstructed from the later source by reversing its sole input-
range extension, then verified against the original recorded hash. It is not presented as a Git
checkpoint. Latest maintained tools and their reused readers/collector helpers are also snapshotted.
When reproducing a historical request, compile its source version and use its exact recorded
argument list; newer optional arguments must not be added to an older executable.

The following commands **read saved observations**. Run from the EPQ root on a separate evidence
copy to preserve canonical manifests. Energy/assessment/readback readers regenerate derived JSON.
The physical auditor refuses to overwrite `audit.jsonl`; remove only derived audit/summary files
in that separate copy before rebuilding them.

```sh
python3 -m tools.performance.qualification_retain /path/to/evidence-copy
uv run --with numpy==2.5.4 --with scipy==1.18.1 python -m tools.performance.qualification_audit /path/to/evidence-copy/runs/collision-self-n12
uv run --with numpy==2.5.4 --with scipy==1.18.1 python -m tools.performance.qualification_audit /path/to/evidence-copy/runs/internal-self-480 --energy-only
uv run --with numpy==2.5.4 --with scipy==1.18.1 python -m tools.performance.qualification_diagnostics /path/to/evidence-copy
uv run --with numpy==2.5.4 python -m tools.performance.qualification_operator /path/to/evidence-copy
python3 -m tools.performance.qualification_assessment /path/to/evidence-copy
uv run --with numpy==2.5.4 --with scipy==1.18.1 --with matplotlib==3.11.2 python -m tools.performance.qualification_plot /path/to/evidence-copy
uv run --with numpy==2.5.4 --with scipy==1.18.1 python -m unittest tests.performance.test_qualification tests.performance.test_spatial -v
```

To **start new simulations**, compile the selected source and shared header in a new work directory,
create a new evidence directory with an explicit protocol copy, then run the collector:

```sh
c++ -std=c++17 -O3 -Wall -Wextra -Werror -fopenmp -ffp-contract=off \
  /path/to/sources/qualification_solver.cpp -o /path/to/new-work/solver
OMP_WAIT_POLICY=PASSIVE python3 -m tools.performance.qualification_campaign \
  /path/to/new-evidence /path/to/new-work/solver screen
```

`spatial`, `temporal` and `viscosity` are other bounded phases; exact additional controls are
reproducible through `qualification_campaign.run` with recorded request parameters and preserved
restart files. All start new integrations from the explicitly recorded initial state; loading
observations for analysis does not continue a simulation. Shear/slab probes compile separately
with the same C++17 precise flags, without OpenMP, and take arguments recorded in their native JSON.
No production backend, CUDA timing or production adoption is performed by these tools.
