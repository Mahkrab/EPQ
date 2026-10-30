# Viscosity and traction qualification evidence

The [physical report](/docs/project/development/milestones/05/viscosity-traction.md) owns the
interpretation. `assessment.json` records the negative full-model qualification decision. No
production configuration is proposed. This is an uncommitted standalone experimental source
snapshot based beside EPQ `814f88a7f4122b1b24ea645b210d89e1200a0c44` and Maelstrom
`250932784790ba26cdc55fc38a877ccefacbf054`; it is not a historical checkpoint.

## Protocol and results

- `protocol.json`, `edge-quadrature-protocol.json`, `coupled-admission-protocol.json`,
  `mirror-pressure-protocol.json` and `pressure-support-protocol.json` were written before their
  respective experiments. `hydrostatic-initialisation-control.json` identifies a separate initial
  value experiment and the unchanged conditioning trajectory.
- `weak-strain-screen.json` and `weak-hourglass-failure.json` preserve the rejected nodal version.
  `edge-strain-screen.json` retains all 41 time samples per mode/resolution over 2τ. The assessment
  applies unchanged error limits to both one-τ and two-τ windows; eight full-depth layers pass
  through τ, while twelve are needed through 2τ. Admission to a one-τ coupled diagnostic is not
  a longer qualification.
- `edge-matched-horizontal.json` retains **fixed H=0.05 m**, L=0.6 m refinements.
  `exact-old-geometry-horizontal.json` instead matches the old constant Δx=0.025 m two/four-layer
  study exactly, with H=0.05/0.1 m. The geometries must not be conflated.
- `native-operator/`, `invariants/` and `deformed/` retain every produced p/v/acceleration array;
  their adjacent JSON files contain commands, force/energy diagnostics and hashes.
  `pressure-jacobian/` retains the one-step sheared/jittered native constraint probe, its actual
  sparse Jacobian, initial arrays, output states and independent finite differences.
- `pressure-gradient-reference.json` independently evaluates lattice density and the pressure
  gradient tensor under isochoric shear at two spacings and five support ratios.
  `isochoric-shear-density.json` retains the earlier scalar/curvature calculation.
- `quietness-physical-reference.json` records exact modal decay and threshold times for both
  viscosities. `dimensional-viscosity-check.json` verifies viscosity changes the clock rather
  than the dimensionless spatial error. These are shear references, not collision predictions.

Each full PBF label in `coupled/` has a request, original stderr, collection metadata, a lossless
compressed state stream and compressed every-step energy ledger. Uncompressed originals also
remain here. There are **17 completed coupled runs and one deliberately rejected prefix**.
The complete cases provide 473 scheduled p/v states and 11,142 accepted-step ledger records.
The extra pressure-Jacobian probe is a separate one-step experiment.

The h=4Δx case violated the predefined transient velocity L2 gate repeatedly and was terminated
only after its failure-prefix calculation was saved. Its header/request still state the intended
duration. `*.rejection.json` identifies the exact assessed prefix by length and hash;
`*.termination.json` identifies the reason and targeted process. Original produced bytes,
including any incomplete trailing record, remain unchanged. `readback.json` distinguishes complete
runs, complete produced prefix frames and truncated tails. No full-duration or settled h=4 pass
is claimed. Incomplete observations are never silently repaired into successful runs.

`audits-final/` contains the authoritative independent re-audits, each identifying the final auditor
hash. Earlier exploratory `coupled/*.audit*.json` remain for transparency. An instrumented label
was initially misclassified as a fixed density boundary; `audit-erratum.json` identifies the
superseded result. Final audits explicitly identify known boundary models and reject unknown
unlabelled models. Raw trajectories were unaffected. The modal and axis-instrumented native
trajectories are byte-identical to the original mirrored run; physical admission remains based
on references, not that instrumentation check. `modal-stage-attribution.json` records pressure's
nonzero shear projection despite zero net tangential pressure impulse.

Native states use the spatial reference's little-endian binary64 layout: four uint32 header
values (magic 0x50424634, particle count, fixed-sample count, planned steps), eleven doubles,
fixed sample positions, then a uint32 accepted step followed by all p and v triples per observation.
The energy ledger records all accepted steps, including pressure/plane/contact work, reconstructed
and accepted energies/momentum, dimensional viscous dissipation, backward-Euler time loss and
linear-solve residual. Angle-integrated momentum on a periodic torus is not a physical global
angular-momentum test; free finite-cloud operator tests supply that check instead.

The old Fourier files' `kinetic_per_amplitude_squared` uses the complex-mode norm. For horizontal
nonzero-wavenumber real shear its physical kinetic energy is half that value. Native p/v energies
and the final operator tool's `physical_kinetic_per_amplitude_squared` use the physical convention.
Forces, decay rates, amplitudes and pass/fail findings are unchanged. No old array was overwritten.

## Reproduction

Commands below either start a **new isolated calculation** or **read saved observations**, as
specified. They do not resume a previous fluid simulation. Use a fresh output directory/label;
canonical requests and audit outputs refuse overwrite. Run Python modules from the EPQ root.
Dependencies are managed with `uv`; no global installation or system setting is required.

This starts new fixed-position operator calculations:

```sh
uv run --with numpy==2.5.4 --with scipy==1.18.1 python -m tools.performance.traction_operator /new/output/operator.json
c++ -std=c++17 -O3 -Wall -Wextra -Werror -fopenmp -ffp-contract=off tools/performance/traction_probe.cpp -o /new/output/traction-probe
OMP_WAIT_POLICY=PASSIVE uv run --with numpy==2.5.4 --with scipy==1.18.1 python -m tools.performance.traction_native_check /new/output /new/output/traction-probe
```

This builds and starts a **new** mirrored channel simulation. The campaign's JSON request contains
the complete native command and binary identity. To reproduce another retained case, use its
recorded parameters, including pressure support, initial-state hash and the exact timestep.

```sh
c++ -std=c++17 -O3 -Wall -Wextra -Werror -fopenmp -ffp-contract=off tools/performance/traction_pbf_mirror.cpp -o /new/output/traction-pbf-mirror
python3 -m tools.performance.traction_campaign /new/output/coupled /new/output/traction-pbf-mirror mixed-n4 --ny 4 --amplitude .01 --gravity 9.81
```

Fixed-wall controls use `traction_pbf.cpp`; instrumented controls use `traction_pbf_axis.cpp` and
`traction_pbf_modal.cpp`. The optional pressure probe builds the mirrored source with
`-DMAELSTROM_DUMP_PRESSURE_JACOBIAN`; without it the rebuilt source retains the exact original
mirrored binary hash `6a25890e9667839301f00b108a0c37ed5918931747da9ff8ca2400a26f00eca7`.
The dump changes no constraint action. `traction_jacobian.py` starts a new one-step probe and
compares the actual Jacobian with independent finite differences of the density field.

This **reads saved states and ledgers** and writes an independent audit to a new destination:

```sh
uv run --with numpy==2.5.4 --with scipy==1.18.1 python -m tools.performance.traction_audit docs/project/development/milestones/05/assets/traction-qualification-v1/coupled mirror-mixed-n8-g9.81 --destination /new/output/audits
```

The audit uses a periodic KD tree, independently summed physical masses and analytic C2 slab
integrals. Off-particle probes do not subtract the particle-site bias. Volume/height reconstruction
uses irrational horizontal sampling strides and 0.45/0.50/0.55 density thresholds, compared with
an identically filtered continuum slab; it is not fitted to the measured centroid. Reported
particle heights are envelope proxies. Compression extrema are sampled at approximately 0.05 s;
full accepted-step density distributions were not stored and are not claimed. Ledger quietness
and energy limits use all accepted records, not only graphical snapshots.

The complete coupled simulations ran on the primary PC, Ryzen 9 7900X, four CPU workers,
GCC 13.3.0 and the flags above. Isolated operator/probe checks and independent audits ran locally;
their native arrays and exact source are retained. `OMP_WAIT_POLICY=PASSIVE` is process-local.
Elapsed CPU times are retained but are not comparative solver benchmarks. No CUDA performance,
production Rust/CUDA validation, real-time suitability or optimisation benefit is claimed.

This runs the local focused numerical/reference regression suite:

```sh
uv run --with numpy==2.5.4 --with scipy==1.18.1 python -m unittest tests.performance.test_traction tests.performance.test_qualification tests.performance.test_spatial -v
```

`verification-complete.txt` records 41 passing tests. Earlier verification logs are retained.
`sources/final/` and `source-provenance.json` freeze the final tools/tests and direct dependencies;
earlier weak/edge source snapshots remain alongside them. Exact native commands and source hashes
are the reproduction authority, not assumptions about a movable checkout.

## Retention and preservation

`SHA256SUMS` seals the local files, including original and compressed observations, source snapshots,
protocols, audits, figures and readback records. Compressed and raw hashes are separately checked.
`mirror-readback.json` records independent readback of the same manifest from
`/home/oliver/.local/share/maelstrom-experiments/traction-qualification-v1/evidence` on the primary PC.
The primary's original run directory also remains. These are durable home/workspace locations,
not temporary directories. The manifest and later mirror receipt are excluded from their own
manifest to avoid circular identities. `traction_retain.py` verifies stream/ledger completeness
and rejected-prefix hashes before sealing; it does not make an incomplete run pass.

`prior-evidence-preservation.json` and `prior-archive-readback.txt` verify all 508 checksums of the
unchanged preceding archive. `environment-and-preservation.json` verifies the thirteen retained
native source identities, both unchanged HEADs and the unchanged pre-existing Maelstrom dirty state.
No production source, optimisation, history, branch, tag, gitlink or system-wide setting was changed.
The five-second collision failures in the prior study remain original failures.
