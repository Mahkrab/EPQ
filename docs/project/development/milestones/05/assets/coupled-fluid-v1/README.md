# Coupled-fluid qualification evidence

This is the isolated 29 October 2026 coupled reference. The
[report](/docs/project/development/milestones/05/coupled-fluid-qualification.md) records **NO-GO**:
the candidate conserves mass/momentum but fails wave velocity/energy and collision gates.
No complete-fluid GPU benchmark was admitted. These are standalone experiments, not a production
change or a Git checkpoint.

## Records and versions

- `protocol.json`, `energy-and-cases-protocol.json`: criteria, material/geometry assumptions,
  resolution bounds, wave-energy normalisation and collision inputs specified before those runs.
- `initial-state.json`: independent repository HEAD/index/working-state records and pre-existing
  source hashes. Existing unrelated work was preserved.
- `operators/`: raw hydrostatic and shared-versus-mismatched mass-flux controls.
- `translation-*`, `shear-*`: original algebraic/geometric translation and coupled manufactured
  shear screens. The coarsest shear's failed CFL prefix is retained.
- `wave-midpoint-*`: original wave runs, including geometry-cancellation failures. Their exact
  original source versions remain in each case's `sources/`.
- `geometry-cancellation-control/`: exact-area oracle, original/stable results and identical-input
  failed-step replays. `geometry-stable/` repeats waves with only that implementation defect fixed,
  then holds the formulation fixed for timestep/Euler controls and the original fixed-step collisions.
- `interface-control-protocol.json`, `interface-pressure-control/`: frozen-interface initial
  acceleration tests. Physical staggered masses are a diagnostic counterfactual, not a coupled fix.
- `collision-cfl-protocol.json`, `adaptive-collision/`: evolving-velocity CFL policy, spatial/time
  controls and recorded timestep rejections. No damping or state clipping was introduced.
- `steady-controls/`: exact hydrostatic equilibrium with affine tangential shear.
- `wave-acceleration-screen/`: original early acceleration/energy screen; its inputs are the same
  wave state, timestep and original source version retained under `wave-midpoint-*/sources/`.
- `wave-diagnosis/`: independent liquid/gas velocity comparisons and stage-energy accounting.
- `reproduction/`: complete small-wave repeat using final sources. Its original physical failure
  remains a failure; reproduction tolerances are not physical acceptance thresholds.
- `assessment.json`, per-case `assessment.json`, `coupled-qualification.svg/.png`: derived tables,
  gate results and plots. All coarse failures and unsuccessful approaches remain visible.
- `primary-readings.json`: sources actually read and their limited scope; copyrighted PDFs were
  not redistributed. Research records S080/S081 distinguish published methods from the local prototype.
- `raw-readback-final.json`: independent recalculation of conservation, divergence, integrated
  pressure forces, body-force/momentum and kinetic-stage closure for **all 15,700 states in 30 cases**.
- `tests-final.log`, `tests-snapshot.log`: final tests and standalone frozen-source verification.
- `final-sources/`, `source-provenance.json`: final tools/tests with original relative paths and
  source identities, including the admitted Python pressure reference used as a test oracle.
- `preservation.json`, `prior-mirror-preservation.json`, `SHA256SUMS`, `local-readback.json`,
  `mirror-readback.json`: production guards, earlier-archive preservation and independent readbacks.

Each streamed case has `input.json`, `status.json`, `frames.jsonl`, `states.npy.gz` and its actual
source snapshot. The gzip stream consists of consecutive lossless NumPy arrays of shape
`(4, ny, nx)`, FP64, ordered **alpha, u, v, p**. Arrays are not pickled. Face velocities are on
positive x/y faces; the top velocity is fixed to zero in a wall-bounded case. Every initial,
midpoint and accepted state is indexed by time and kind in JSONL. Midpoints are diagnostic stages,
not additional accepted timesteps. Failed cases retain the successful prefix and failure reason.
Adaptive cases also retain `rejected-steps.jsonl`; their actual timestep is in each stage ledger.

The model is two-dimensional and per unit out-of-plane depth. The finite gas, rigid lid, inviscid
limit and zero surface tension are physical assumptions, not a claim of general liquid/coalescence
qualification. There are no particles, transfers, curved walls or physical settling model here.

## Durable copies

The canonical evidence is this directory. An independent copy is stored on the primary PC at
`~/.local/share/maelstrom-experiments/coupled-fluid-v1/`. Both are read back against the same
manifest and flushed to storage. The prior pressure feasibility archive and the diagnosis's
`evidence/` mirror are checked separately. Raw states are stored directly in lossless streams;
they have not been replaced by summaries or deleted after making an archive pointer.

Receipts verifying the current manifest are outside it to avoid self-reference. Per-case source
versions are authoritative for old runs. The final source snapshot incorporates the stable area
formula and adaptive-CFL driver; it does not silently rewrite the original failed runs.

## Reproduce fresh experiments

These commands create **new manufactured/coupled simulations**, not resumption of saved states.
Run from the repository root or the retained `final-sources/` root. Choose a new durable output
directory: case directories are exclusive and are never overwritten.

```sh
mkdir -p "$HOME/.local/share/maelstrom-experiments/coupled-reproduction"
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 uv run --with numpy==2.5.4 --with scipy==1.18.1 python -m tools.performance.coupled_campaign "$HOME/.local/share/maelstrom-experiments/coupled-reproduction" operators
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 uv run --with numpy==2.5.4 --with scipy==1.18.1 python -m tools.performance.coupled_campaign "$HOME/.local/share/maelstrom-experiments/coupled-reproduction" transport
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 uv run --with numpy==2.5.4 --with scipy==1.18.1 python -m tools.performance.coupled_campaign "$HOME/.local/share/maelstrom-experiments/coupled-reproduction" shear
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 uv run --with numpy==2.5.4 --with scipy==1.18.1 python -m tools.performance.coupled_campaign "$HOME/.local/share/maelstrom-experiments/coupled-reproduction" wave
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 uv run --with numpy==2.5.4 --with scipy==1.18.1 python -m tools.performance.coupled_campaign "$HOME/.local/share/maelstrom-experiments/coupled-reproduction" time
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 uv run --with numpy==2.5.4 --with scipy==1.18.1 python -m tools.performance.coupled_collision "$HOME/.local/share/maelstrom-experiments/coupled-reproduction"
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 uv run --with numpy==2.5.4 --with scipy==1.18.1 python -m tools.performance.coupled_steady "$HOME/.local/share/maelstrom-experiments/coupled-reproduction"
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 uv run --with numpy==2.5.4 --with scipy==1.18.1 python -m tools.performance.coupled_interface_control "$HOME/.local/share/maelstrom-experiments/coupled-reproduction"
```

To repeat the original area-cancellation failures, copy that case's `sources/*.py` into a fresh
`tools/performance/` package directory and run the corresponding command there. Do not overwrite
current tools. The fixed-step collision control is `coupled_campaign ROOT collision`; its known
CFL failures are distinct from the adaptive driver above. No numerical criterion requires
bitwise agreement with an old source version.

Dependencies are managed by `uv`; thread settings apply only to these processes. There are no
global package installations or system-wide settings. All qualification calculations are local
CPU references; the primary PC was used for durable mirroring, not a new throughput claim.

## Tests and saved-observation readers

Run the independent tests without starting a full simulation:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 uv run --with numpy==2.5.4 --with scipy==1.18.1 python -m unittest tests.performance.test_coupled_fluid -v
```

The following reads **saved observations** and checks raw conservation/force/energy accounting:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 uv run --with numpy==2.5.4 --with scipy==1.18.1 python -m tools.performance.coupled_rawcheck /absolute/evidence/root
python3 -m tools.performance.coupled_retain verify docs/project/development/milestones/05/assets/coupled-fluid-v1
```

`coupled_audit ROOT --pattern 'wave-*'` reads saved fields and writes independent reference arrays
and derived assessments. `coupled_diagnosis` and `coupled_assessment` also write derived products;
use disposable copies of sealed evidence. Plot generation additionally uses
`matplotlib==3.11.2`. None of these readers reruns the recorded solver timesteps.

The complete reproduction driver expects an existing `geometry-stable/wave-midpoint-n32`
reference and no `reproduction/` directory. Use a fresh copy of that reference layout, then run
`python -m tools.performance.coupled_reproduce ROOT` with the same pinned dependencies. It creates
a new complete wave run, compares fields and preserves the failed physical gate.

The production Rust/CUDA suite, general boundary geometry and complete-fluid GPU performance
were not qualified by these commands. The benchmark gate remains closed.
