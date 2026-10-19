# Phase 1 GPU solver implementation and verification

## Starting point

Implementation began with clean EPQ `c32bcfb9b59560f9dd49d5516295dc18fb9fed10` and Maelstrom
[`facf789e349a3dbbc42126504e150befe67cb519`](https://github.com/Mahkrab/Maelstrom/tree/facf789e349a3dbbc42126504e150befe67cb519),
the local `milestone-03/phase-01/start` checkpoints. The existing CUDA integration owned contexts,
streams and a layout probe, but could not execute a fluid timestep. The
[milestone plan](/docs/project/development/milestones/03/plan.md) defines the scope; the inherited
[numerical contract](/docs/project/development/milestones/00/phases/phase-00-design-contract.md) and
[comparison policy](/docs/project/development/milestones/00/reference-verification.md) remain unchanged.

## Scope and outcome

The library and CLI now support explicit CUDA simulation and public replay. GPU kernels execute
uniform-grid discovery, acceleration, prediction, every configured Jacobi pass, ordered projection
and velocity reconstruction. Host work coordinates completion, diagnostics and atomic acceptance.
CPU implementations and historical records retain their existing numerical meaning.

The assessed implementation is now committed as Maelstrom
[`80cce8a8b8bb604ed988b176298211c6fed491f0`](https://github.com/Mahkrab/Maelstrom/tree/80cce8a8b8bb604ed988b176298211c6fed491f0).
All 99 source, fixture, test and documentation hashes in the retained
[source manifest](/docs/project/development/milestones/03/assets/solver-v1/source-manifest.json)
match that commit. The original collection retains its working-tree provenance unchanged;
the local completion tags provide the subsequently authorised historical boundary.

## Decisions and implementation

### Deterministic storage without occupancy truncation

Persistent device arrays separate accepted input, working positions, complete multipliers and
corrections. The GPU sorts occupied-cell entries and searches the 27 adjacent cells. Cell width
uses the serial grid's conservative power-of-two construction, including the squared-distance
underflow floor and bounded indices. Strict binary32 distance decides membership; unsafe bounding
diagonals retain reference-ordered distant-pair checks.

Fixed prediction membership uses checked bitsets rather than bounded cell buckets or neighbour
rows. Each particle owns its row and visits set bits in ascending identity order, independently
of scheduling. This avoids silent occupancy limits and a second row-sorting operation, at the
cost of quadratic storage: 8,000 particles need 8,000,000 membership bytes even for sparse input.
Allocation failure rejects the attempt. Density includes self once at its ordered position.

### Preserving the host's arithmetic

Separate synchronised launches establish whole-stage barriers. Ordered binary32 reductions,
precise division/square root, denormal handling and disabled contraction preserve the CPU operation
sequence. Per-particle errors are read in stage and identity order rather than whichever lane fails first.

Two power implementations failed qualification. Native CUDA `powf` exceeded the position budget by
checkpoint 120; using binary64 library power delayed the failure until checkpoint 480. A component
trace found the host approximation itself rounding differently at a power boundary. The retained
[rejected observations](/docs/project/development/milestones/03/assets/solver-v1/rejected/README.md)
show these disagreements. A small MIT-licensed adaptation of Arm's power approximation reproduces
the tested host rounding; its pinned provenance and licence accompany the source. No CPU equation,
tolerance, fixture, dependency lockfile or workload was changed to obtain agreement.

### Acceptance, resources and public execution

The host snapshot is the sole accepted-state authority. Each attempt reloads it into private device
scratch; dependent work finishes before errors or cancellation are observed. Final downloads, state
checks, plane checks and the last cancellation poll precede publication. Numerical failure and
cancellation can retry from the old snapshot. Uncertain driver failures poison the resource; allocation
exhaustion permits retry. No CPU fallback or device reset is attempted.

`--execution cuda` requires the grid and records device ordinal and block size. It rejects CPU worker
options. Runtime metadata identifies the GPU, driver and embedded target separately from physical
input identity. Replay restores execution settings; historical CPU replay remains supported.
The [CUDA guide](https://github.com/Mahkrab/Maelstrom/blob/80cce8a8b8bb604ed988b176298211c6fed491f0/docs/cuda.md)
in the assessed source explains transfers, synchronisation and supported requests.
Required transfers and validation remain inside completed-step timing; independent fresh density
audits remain outside. These are instrumentation boundaries, not performance findings.

## Verification

The [retained collection](/docs/project/development/milestones/03/assets/solver-v1/README.md) records
the primary-PC environment, exact commands, source/build identities, original results and component
reports. The complete release suite passed **219 tests**, including explicitly enabled hardware cases;
the focused debug device suite passed **23**. Strict feature-enabled Clippy and Rustdoc passed.
Native ASan/UBSan checks passed with injected allocation, transfer, submission, completion and cleanup
failures. Local CPU regression, disabled-feature rejection and a release build with deliberately
invalid CUDA/compiler environment settings also passed. Parent comparison tests reject missing
checkpoints, identity/warning changes, non-finite values, signed-zero changes and isolated outliers.

Final qualification retained **86 successful application runs and 80 exact component comparisons**,
covering 1,776,150 snapshot components. Both complete goldens repeated at 32, 64, 128 and 256 lanes
under ordinary, total-only and profiled execution, with public replay. Every larger family member
through 8,000 particles completed 480 steps at 128 lanes against fresh serial-grid and four-worker
CPU controls. Every required snapshot, audit, CFL value, warning and status matched exactly.
An independent local audit rechecked raw hashes and complete physical documents with the existing
serial comparator. Real CLI cancellation retained 189 accepted steps, matching a fresh CPU prefix.

## Limitations and Gate G01

Compute Sanitizer memcheck and racecheck both exited 90 because the WDDM debugger interface could
not initialise. Their application runs completed, but neither diagnostic passed. Actual device-loss
recovery remains unqualified; injected faults establish ownership policy only. Exact agreement is
bounded to the recorded environment, requests and launch settings, not every libm, compiler or GPU.

**G01 passes locally on the recorded primary PC**, with the diagnostic and portability limits above.
The final source manifest and retained-data audit passed. Annotated
`milestone-03/phase-01/complete` tags identify the local completion checkpoints in both repositories,
and the parent gitlink pins the assessed implementation. Original raw results and integrity records
are unchanged. Remote publication and hosted verification remain separate; no GPU performance
campaign or later implementation work is included.
