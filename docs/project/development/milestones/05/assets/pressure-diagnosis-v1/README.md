# Pressure-projection diagnosis evidence

The [diagnosis report](/docs/project/development/milestones/05/pressure-projection-diagnosis.md)
owns interpretation and the go/no-go decision. This is a bounded manufactured/operator investigation,
not another solver implementation or a production policy. `protocol.json` preceded collection.
The standalone sources are uncommitted experimental work alongside the recorded EPQ and Maelstrom
HEADs; source hashes, not a movable checkout or an implied historical checkpoint, identify them.

## Evidence map

- `verified-operators/operator-results.json` and its `operators/*.npz` are the authoritative
  70 unique layer-reduced manufactured geometries. Each NPZ includes C, J, the full-particle
  Jacobi row norm, pressure and velocity fields, pressure action, singular values and exact
  projection outputs. Physical geometry stays fixed while spacing and support vary separately.
- The initial `operator-results.json` and `operators/` remain as exploratory evidence. Its
  catalogue repeats one identical free-surface configuration; the verified reproduction uses
  unique labels and exclusive output files. No distinct physical configuration was replaced.
- `gauge-and-neighbour-results.json` and `gauge-and-neighbours/` retain all small-strain,
  frozen-identity, finite-difference and mean-equation attribution controls. Positive constraint
  counts distinguish active compression rows from two-sided mathematical diagnostics.
- `constitutive-results.json` and `constitutive/` contain the independently evaluated C2 kernel
  Hessian, affine-shear curvature and separately predicted sinusoidal pressure forces. The
  artificial modulus was not fitted to these force observations or to a complete simulation.
- `native/` contains 16 pressure-only requests, exact initial arrays, actual primary-PC execution
  commands, binary identities, complete states, stderr and all pressure-iteration arrays. Viscosity
  and interparticle contact are disabled. Every case advances exactly one timestep.
- Native `*.ledger.trace.gz` uses magic 0x50524431, uint32 particle/iteration counts, six doubles
  (spacing, support, timestep, mass, epsilon, correction scale), then each iteration's p triples,
  scalar C, scalar lambda and correction triples. Native `*.ledger.jac.gz` exports the first
  iteration's actual sparse Jacobian: uint32 count; per row two doubles (C, lambda), uint32 entry
  count, then uint32 target and three double derivative components per entry. All are little-endian.
- `native-audits/` and `native-results.json` compare the native Jacobian/diagonal/correction against
  independent layer sums and point-kernel finite differences. `packed-readback/` repeats those
  audits from compressed canonical streams. These are verification results, not physical passes.
- `retained-failure-replay.json` associates the new pressure-only step with step97 of the previous
  complete-model failure. `multiplier-attribution.json` records its constant and nonconstant
  multiplier contributions. `replay-pressure-scale.json` checks the effective pressure magnitude
  against hydrostatics. Only that complete-model stage is replayed; the entire59.1% history is
  not newly apportioned.
- `native/instrumentation-equivalence.json` verifies that diagnostic instrumentation reproduces
  the existing reference's original raw state bytes. Original-baseline observations are retained
  separately. Physical acceptance uses manufactured references, not byte agreement.
- `assessment.json` records controlled exclusions and the negative decision for the present model.
  `pressure-diagnosis.png` and `.svg` provide standalone figures. `verification-final.log` records
  52 passing implementation/reference tests; the documented physical counterexamples still fail.

The layer reduction is exact for horizontally uniform layer motion. Its aggregated J is **not**
used to replace the full three-dimensional row norm in Jacobi denominators. Native checks validate
both quantities separately. Perturbed retained-state finite differences also test the full point
constraint. Uniform translation and total internal momentum can be correct while constant pressure
still produces nonzero internal forces and destroys a shear mode.

The SVD projection and zero-mean-equation control are offline mathematical attribution tools using
the same density Jacobian. Neither is a new time-stepped pressure method. Removing pressure mean
would require a separate free-surface/normal-traction derivation and is not proposed as a fix.

## Reproduction

All calculations use the recorded fixed geometry and physical masses. New output labels are
exclusive. Commands below state whether they start a new calculation or read saved observations;
none resumes a previous simulation. Use `uv` with pinned dependencies and fresh destinations.

This starts **new frozen manufactured calculations**, not a fluid simulation:

```sh
mkdir -p /new/study/verified-operators
uv run --with numpy==2.5.4 --with scipy==1.18.1 python -m tools.performance.pressure_campaign operators /new/study/verified-operators
uv run --with numpy==2.5.4 --with scipy==1.18.1 python -m tools.performance.pressure_constitutive /new/study
```

This builds the instrumented **existing** reference and prepares fresh one-step initial states:

```sh
c++ -std=c++17 -O3 -Wall -Wextra -Werror -fopenmp -ffp-contract=off -DMAELSTROM_DUMP_PRESSURE_JACOBIAN tools/performance/pressure_probe.cpp -o /new/study/pressure-probe
uv run --with numpy==2.5.4 --with scipy==1.18.1 python -m tools.performance.pressure_campaign prepare-native /new/study --binary /new/study/pressure-probe --replay docs/project/development/milestones/05/assets/traction-qualification-v1/coupled/mirror-mixed-n4-g9.81.raw.gz
```

`pressure_run.py` starts **new one-step pressure-only simulations** from prepared requests.
The recorded campaign ran on the primary PC, Ryzen9 7900X, GCC13.3.0, four workers. Its stdlib-only
runner requires no SciPy installation on that machine. Transfer prepared inputs and source/header,
build with the flags above, then run:

```sh
python3 tools/performance/pressure_run.py /new/study/native /new/study/pressure-probe
```

The runner verifies binary and initial-array identities, records remapped execution paths and sets
only process-local `OMP_WAIT_POLICY=PASSIVE`. Canonical requests retain their preparation command;
`*.execution.json` records the actual primary command. Extra native arguments are εh² and neighbour
refresh. Frozen identities still use current fluid and reflected positions. Mass remains geometric
after appending diagnostic arguments; the instrumentation-equivalence check guards that boundary.

This **reads saved observations**, with no simulation:

```sh
uv run --with numpy==2.5.4 --with scipy==1.18.1 python -m tools.performance.pressure_audit docs/project/development/milestones/05/assets/pressure-diagnosis-v1 --destination /new/audit
uv run --with numpy==2.5.4 --with scipy==1.18.1 python -m tools.performance.pressure_controls docs/project/development/milestones/05/assets/pressure-diagnosis-v1 /new/controls --legacy docs/project/development/milestones/05/assets/traction-qualification-v1
```

The readers accept the lossless gzip streams. To rerun a recorded native command directly, unpack
its initial array into a fresh scratch location and redirect binary, initial and output paths;
do not write into this archive. `pressure_assessment.py` reads the completed operator/native/control
results; `pressure_plot.py` renders the figure from those observations. Their numerical outputs
are deterministic within the stated floating-point tolerances, not a requirement for bitwise
agreement with a physically failed solver.

This runs verification of the new diagnostic tooling and retained reference boundaries:

```sh
uv run --with numpy==2.5.4 --with scipy==1.18.1 python -m unittest tests.performance.test_pressure_diagnosis tests.performance.test_traction tests.performance.test_qualification tests.performance.test_spatial -v
```

`sources/` and `source-provenance.json` freeze the tools, tests, direct dependencies and the exact
instrumentation diff from the preceding experimental reference. The production CUDA implementation
was not edited or benchmarked. Native one-step runs were on the primary PC; matrix calculations,
independent audits and tests ran locally. No comparative cost or real-time performance claim is made.

## Durable retention

`compression.json` identifies all82 raw streams by raw length, raw SHA256 and gzip SHA256.
Packing kept originals until independent primary-original readback succeeded. The subsequent
`local-packing-removal.json` records removal of duplicate local uncompressed files only: all raw
bytes remain in verified lossless streams and in the primary's original run directory. Produced
observations, including sparse Jacobians and every iteration, are retained rather than summaries
alone. No canonical evidence lives in a temporary directory.

`SHA256SUMS` seals source, protocol, observations, analyses and readback files. The later
`mirror-readback.json` verifies an independent copy under
`/home/oliver/.local/share/maelstrom-experiments/pressure-diagnosis-v1/evidence`.
The manifest and its later mirror receipt are excluded from their own checksum list to avoid
circular identities. `environment-and-preservation.json` verifies both unchanged HEADs, all13
native source identities and the unchanged pre-existing Maelstrom state. Prior-archive readback
verifies all249 checksums from the preceding traction study without modifying it.
