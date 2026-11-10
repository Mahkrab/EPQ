# Complete CUDA timestep comparison

The requested target is real-time live simulation at 110,592 particles, preserving
experimental 240 Hz/eight iterations/correction 0.25/relaxation 20 and all other
modes, exact accepted states, error priority and cancellation boundaries.

Control is the clean Maelstrom tree at 6bf2682325b7665e48f8a8647ce087d48ff13f0b;
parent starts at e7664ee354246507928ac0d80758cffceef0072d. Work uses isolated PC
sources/executables under `/home/oliver/.cache/maelstrom-critical-path-20261109`.
No installed executable, checkout, driver, clock or power policy changes.

Fresh preliminary control runs use the existing 8,000/32,000/110,592-particle
rendering inputs and hardware GL/X11 impostors. These are session checks, not
candidate comparisons. Separate Nsight runs identify the sequential critical path;
API waits and overlapped kernels must never be added as independent costs.

The first candidate assigns eight lanes to each correction row. Pair work runs
concurrently but contributions and their errors are consumed in original neighbour
identity order. There is no tree sum, fewer iterations, looser arithmetic, extra
allocation or changed cancellation/observation boundary. The original monolithic
entry remains available in the candidate source as a scalar reference. Existing
GPU component/error tests must pass before timing.

Ordinary comparison: one warm-up pair then three measured alternating pairs at
each required particle count, 1,200 complete accepted steps per run. Within pairs
order is AB, BA, AB, BA including warm-up. Retain every sample and error. Use
existing live_viewer frame/solver instrumentation and telemetry, with no concurrent
build, test or diagnostic workload. Compare complete solver ms/step, actual viewer
simulated seconds/wall second, presentation intervals and complete command wall
time. Individual pairs, medians and ranges remain visible. No fixed percentage
cutoff decides retention. If the prototype clearly regresses, reject it rather than
extending an optimisation frontier. A narrower subgroup may be examined only if
profiles identify subgroup overhead as a specific reason.

Separate diagnostic traces use 240 and, where needed, 1,200 steps. Profile perturbation
is disclosed. Kernel sequence attribution checks the complete repeated launch pattern;
GPU idle means absence of this solver's activity, not device-wide idleness.

Qualification of any retained production change requires CUDA unit/integration,
replay, cancellation/rollback and viewer lifecycle/render checks, native fault checks,
precise accepted-state equivalence across numerical modes and full workload horizons,
formatting and strict Clippy. If close to real time at 110,592, additionally run
4,800 steps and inspect every one-second interval with the existing capacity tool.
If no candidate survives, preserve its patch and measured rejection; do not install
it or claim a speedup. Remaining useful GPU work and the real-time gap are reported.

## Bounded layout follow-up, declared before measurement

The row-eight correction trial passed all 35 hardware-enabled CUDA unit checks.
Its three-pair viewer result offers only a modest large-case gain and inconsistent
middle-case results. A second candidate starts from control, without the correction
trial. It groups rows in tiles of 32, padding each tile to its longest row and
storing consecutive row elements at stride 32. Row counts and identity order remain
unchanged. A single additional integer kernel forms tile offsets after the CSR
prefix; unused cell-sort scratch holds those offsets. Count/fill, cooperative sort
and all numerical modes retain their checks and unbounded row sizes. No pair cache,
changed fluid work or persistent public setting is introduced. Existing scalar
CSR discovery remains available to component tests. This layout is a memory-access
hypothesis, not a claim of measured cache misses or bandwidth saturation.

Run CUDA correctness preflight before ordinary timing. Use the same warm-up plus
three alternating pairs at all three counts. This is the last structural prototype;
reject it if its padding/construction/traversal cost does not earn useful complete
viewer throughput. Keep each candidate's samples and source identities separate.

## Review follow-up

Final source review found that a zero-length final tile could form a padded lane
pointer beyond storage even though no element was read. The reviewed iterator
forms row pointers only for non-empty rows; an additional hardware case checks
empty rows, tail tiles, all four block sizes and no neighbour allocation. The same
warm-up/three-alternating-pair protocol was reapplied at all three counts to this
reviewed source. Those samples are `reviewed-*`; do not pool them with `final-*`
(the pre-review size-selective build) or credit their faster control rates to code.
Reviewed source also receives fresh full-motion traces and trajectory witnesses.
The trace before the pointer guard remains separately identified evidence.
