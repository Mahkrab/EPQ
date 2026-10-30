# Pressure feasibility evidence

This is the isolated 29 October 2026 pressure-replacement feasibility study, not a production
solver or Git checkpoint. The [report](/docs/project/development/milestones/05/pressure-feasibility.md)
owns the interpretation. Preserve the protocol, failed candidates, coarse-grid failures and all
three timing samples; the direct flat-domain solver is not evidence for general free surfaces.

## Contents and identities

- `protocol.json`, `admission.json`: prospective gates and cost policy, with both baseline HEADs.
- `mathematics/`, `mathematics.json`: initial 27-case screen. `verified/` contains the 29-case
  reproduction and two added fine periodic levels. `mathematics-reproduction.json` checks every
  shared raw array. Equality here checks reproducibility; physical admission uses independent errors.
- `pilot-sources/`: exact pilot sources reconstructed by removing later diagnostic fields and
  additional levels. Every body matches the source SHA256 recorded by the pilot. This is explicitly
  a reconstructed experimental snapshot, not repository history.
- `sources/`, `source-provenance.json`: final standalone experiment/test sources with original
  relative paths, source identities and baseline commit identities. No repository or production
  implementation is copied. External packages are pinned in script metadata and commands below.
- `cost-geometry/`: continuum fields and solve histories for each geometry admitted to timing.
  The original calculation is codified in `feasible_cost_geometry.py` for reproduction.
- `policy/`, `policy.json`: original interactive timestep/tolerance study. `verified-policy/` is
  the maintained-script reproduction, also retaining the infinitesimal material-volume tests.
- `gpu-audit/`: two initial implementation-admission trials and six raw FP64 fields per trial.
  `gpu-audit-assessment.json` includes the independent sparse CPU comparison.
- `gpu/`: all 30 timed trials, exact commands, subprocess status, stdout, stderr, per-step iteration
  counts and final `p`, `rhs`, `truth`, `vx`, `vy`, `vz` fields. No timed trial was discarded.
  A `.f64` field is little-endian FP64, C order `(ny,nz,nx)`; coordinates are cell/positive-face
  locations as defined by the source. `gpu-assessment.json` contains every field audit.
- `gpu-campaign.log`, `build-command.json`, `build.log`, `build-identities.sha256`, compiler/device
  records: actual primary-PC execution/build evidence. The executable stays outside the repository
  in the primary experimental directory; its SHA256 is recorded here. Build outputs are not
  versioned documentation assets.
- `primary-readings.json`: author-PDF hashes, URLs and actual reading scope. Copyrighted PDFs
  were not redistributed. Research records S077–S079 distinguish source claims from local findings.
- `assessment.json`, `feasibility.svg`, `feasibility.png`: derived tables and plots.
- `preservation.json`, `prior-archive-mirror-readback.json`: 13 native source guards, independent
  repository states, and fresh local/primary checks of the prior 450-file pressure-diagnosis archive.
- `SHA256SUMS`, `local-readback.json`, `mirror-readback.json`: final checksum readbacks. Receipts
  verifying this manifest sit outside it to avoid self-reference.

The canonical root is this directory. Its independent durable copy is the primary PC's
`~/.local/share/maelstrom-experiments/pressure-feasibility-v1/`; it also retains the built executable.
Both copies are read back against the same manifest. The previous diagnosis's independent evidence
copy is in `~/.local/share/maelstrom-experiments/pressure-diagnosis-v1/evidence/`.
No raw file was deleted after copying or replaced by a summary/archive pointer.

## Reproduce mathematical calculations

These commands create **fresh manufactured pressure experiments**, not Maelstrom simulations or
resumption of saved fluid state. Run from the repository root or from the retained `sources/` root.
Use a new durable output directory each time; experiment commands reject an existing case directory.

```sh
mkdir -p "$HOME/.local/share/maelstrom-experiments/pressure-feasibility-reproduction"
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 uv run --with numpy==2.5.4 --with scipy==1.18.1 python -m tools.performance.feasible_campaign "$HOME/.local/share/maelstrom-experiments/pressure-feasibility-reproduction"
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 uv run --with numpy==2.5.4 --with scipy==1.18.1 python -m tools.performance.feasible_policy "$HOME/.local/share/maelstrom-experiments/pressure-feasibility-reproduction"
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 uv run --with numpy==2.5.4 --with scipy==1.18.1 python -m tools.performance.feasible_cost_geometry "$HOME/.local/share/maelstrom-experiments/pressure-feasibility-reproduction"
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 uv run --with numpy==2.5.4 --with scipy==1.18.1 python -m unittest tests.performance.test_feasible_pressure -v
```

The BLAS/thread variables apply to these processes only. No system configuration or global Python
package installation is needed. Mathematical calculations used managed Python/NumPy/SciPy locally;
hardware timing was performed only on the primary PC. The source tree has no production dependency
on these tools or the experimental CUDA executable.

## Reproduce GPU measurements

These commands create **fresh pressure-stage workloads**. First reproduce mathematical admission
and inspect it against the unchanged protocol. Copy the CUDA source and campaign driver to a new
durable primary-PC experimental directory. Build there with the exact flags:

```sh
/usr/local/cuda/bin/nvcc -O3 -arch=sm_89 --fmad=false -prec-div=true -prec-sqrt=true feasible_pressure.cu -lcublas -lcufft -o feasible-pressure
python3 feasible_gpu_campaign.py /absolute/new/experimental/root --binary /absolute/new/experimental/root/feasible-pressure --audit-only
```

Transfer the `gpu-audit/` fields for independent checking before admitting timings:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 uv run --with numpy==2.5.4 --with scipy==1.18.1 python -m tools.performance.feasible_gpu_audit /absolute/new/experimental/root/gpu-audit --cpu
```

Only after both continuum and implementation admission, run the predeclared paired campaign on
the primary PC:

```sh
python3 feasible_gpu_campaign.py /absolute/new/experimental/root --binary /absolute/new/experimental/root/feasible-pressure
```

Then audit **all saved observations**, without rerunning their solver steps:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 uv run --with numpy==2.5.4 --with scipy==1.18.1 python -m tools.performance.feasible_gpu_audit /absolute/new/experimental/root/gpu
```

For derived plots, `feasible_assessment` reads the retained layout and writes derived outputs; use
a disposable copy rather than altering the sealed canonical evidence. It requires pinned
`numpy==2.5.4`, `scipy==1.18.1`, `matplotlib==3.11.2`. It never runs a fluid simulation.
Ordinary whole-solver timings remain necessary before any production/performance claim.

## Read-only integrity check

This command reads saved evidence and checks file identities; it does not rerun experiments:

```sh
python3 -m tools.performance.feasible_retain verify docs/project/development/milestones/05/assets/pressure-feasibility-v1
```

The seal preserves raw arrays directly (and NumPy arrays in lossless NPZ). There is no lossy
resampling, removed outlier, or binary-agreement criterion for physical acceptance. The complete
Maelstrom test suite, arbitrary cut-cell solver, particle transport, dynamic surfaces and coupled
fluid model were not run or qualified in this study.
