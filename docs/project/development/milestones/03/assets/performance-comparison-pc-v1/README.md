# Primary-PC CUDA performance evidence

This collection supports the
[implementation and measurement record](/docs/project/development/milestones/03/phases/phase-02-performance-comparison.md).
The [protocol](/docs/project/development/milestones/03/measurement-protocol.md) was written before
collection. All **105 benchmark attempts** completed 480 steps without warnings, failures or
timeouts. Three ordinary correctness runs matched the frozen golden. All 108 full component
comparisons passed exactly, covering 8,439,552 position/velocity components, audits, CFL values,
physical identities and completion fields. No numerical tolerance was needed.

The starting revisions are EPQ `abc441e2c278eb48c4828c2536bfea2a6b36f2b4` and Maelstrom
`80cce8a8b8bb604ed988b176298211c6fed491f0`. Temporary PC checkouts isolate the experiment from
the existing working copies. Uncommitted simulator changes add lifecycle clocks and tests;
they do not change kernels, arithmetic, fixtures, dependencies or the lockfile.
All 99 simulator file hashes match the current local source and the final PC copy. Their combined
tree SHA-256 is `4295e9bd90041fb5b3f45e0f8a0c7c466a6112105c1165d7ba00a92ff41d678b`.

| Evidence | Responsibility |
| --- | --- |
| [campaign/report.md](/docs/project/development/milestones/03/assets/performance-comparison-pc-v1/campaign/report.md) | Primary medians, spreads, fresh CPU/CUDA ratios, invocation and lifecycle medians |
| [campaign/comparison.json](/docs/project/development/milestones/03/assets/performance-comparison-pc-v1/campaign/comparison.json) | Recomputed numerical reports with counts, maxima, RMS errors, worst components, audits and every CFL comparison |
| [campaign/campaign.json](/docs/project/development/milestones/03/assets/performance-comparison-pc-v1/campaign/campaign.json) | Frozen order, device, toolkit/native flags, embedded PTX hashes and collector identities |
| [campaign/protocol.md](/docs/project/development/milestones/03/assets/performance-comparison-pc-v1/campaign/protocol.md) | Exact pre-collection measurement extension bytes |
| [serial-grid dataset](/docs/project/development/milestones/03/assets/performance-comparison-pc-v1/campaign/serial-grid/dataset.json) | Fresh serial controls, raw/full result indices, source/binary/environment identities and statistics |
| [threaded-grid dataset](/docs/project/development/milestones/03/assets/performance-comparison-pc-v1/campaign/threaded-grid/dataset.json) | Fixed twelve-worker controls with the same evidence and timing boundaries |
| [cuda-grid dataset](/docs/project/development/milestones/03/assets/performance-comparison-pc-v1/campaign/cuda-grid/dataset.json) | Device zero / 128-lane series with the same evidence and timing boundaries |
| [pc-checks.json](/docs/project/development/milestones/03/assets/performance-comparison-pc-v1/pc-checks.json) | 219 release Rust tests with hardware cases enabled, strict feature-enabled Clippy, and the original parent-test failure |
| [pc-parent-checks.json](/docs/project/development/milestones/03/assets/performance-comparison-pc-v1/pc-parent-checks.json) | Successful 41-test parent rerun after copying the omitted historical protocol |
| [local-checks.json](/docs/project/development/milestones/03/assets/performance-comparison-pc-v1/local-checks.json) | Local CPU regression, formatting, strict Clippy and parent tooling checks |
| [cancellation checks](/docs/project/development/milestones/03/assets/performance-comparison-pc-v1/cancellation/checks.json) | Actual 1.5-second GPU timeout, 76-step exact CPU prefix and fresh post-cancellation golden comparison |
| [timeout-command.json](/docs/project/development/milestones/03/assets/performance-comparison-pc-v1/timeout-command.json) | Timeout-check source, exact arguments, elapsed time, exit and output |
| [collection-command.json](/docs/project/development/milestones/03/assets/performance-comparison-pc-v1/collection-command.json) | Actual collection command, environment overrides, UTC interval, elapsed time, exit and full output |
| [audit.json](/docs/project/development/milestones/03/assets/performance-comparison-pc-v1/audit.json) and [pc-audit.json](/docs/project/development/milestones/03/assets/performance-comparison-pc-v1/pc-audit.json) | Independent full-component/hash, statistics, throughput, lifecycle, profile and ratio checks on both copies |
| [local-final-checks.json](/docs/project/development/milestones/03/assets/performance-comparison-pc-v1/local-final-checks.json) and [pc-final-checks.json](/docs/project/development/milestones/03/assets/performance-comparison-pc-v1/pc-final-checks.json) | Independent audit, byte-identical report regeneration and final focused PC tests |
| [pc-integrity.json](/docs/project/development/milestones/03/assets/performance-comparison-pc-v1/pc-integrity.json) | Final source, binary, PTX and collector hashes; no remaining simulator process |
| [historical-report-checks.json](/docs/project/development/milestones/03/assets/performance-comparison-pc-v1/historical-report-checks.json) | Four historical reports and both comparative JSON summaries regenerate unchanged |
| [integrity.json](/docs/project/development/milestones/03/assets/performance-comparison-pc-v1/integrity.json) | Retained-file hashes and final verification-tool identities |

## Environment and boundaries

The PC exposed an AMD Ryzen 9 7900X, 24 logical CPUs with inherited affinity 0–23, 15,966,376 kB
guest memory, and an RTX 4070 with 12,282 MiB, compute capability 8.9 and driver 610.88 (API 13030).
It used Ubuntu 24.04.5/WSL2, Rust/Cargo 1.96.0, CUDA 13.3.73 and GCC 13.3.0. No affinity, priority,
frequency or GPU controls were applied. Memory figures are environment context, not measured use.

All series used one release executable, SHA-256
`06c1448b0aa4e9e6e4308cd36a3d9428de3e930df4637bbc78eee88a0ee5f9c3`, with locked offline
dependencies, no custom Rust flags and compute_89 PTX. Driver JIT uses the ordinary driver cache;
the construction clock does not claim to isolate cold compilation. The collection ran sequentially
on 19 October 2026, serial grid then twelve workers then CUDA, without concurrent project checks.
Full invocation timestamps and applied settings remain in the datasets. No backward UTC transition
was observed between successive retained benchmark invocations; elapsed clocks are monotonic.

Each series has seven sizes in the frozen order: 64, 216, 512, 1,000, 1,728, 4,096 and 8,000.
Every size has one ordinary warm-up, three total-only samples and one separate profile. Every
attempt starts from a fresh process and independently owned state. The common completed-step
boundary includes allocation/growth, transfers, launches, synchronisation, validation and atomic
acceptance. Separate lifecycle fields include context/module/stream construction and consuming
destruction. First-step device buffers remain inside solver timing. Invocation time additionally
includes audits, snapshots, output and process costs. Profile stages are synchronised host elapsed
intervals, with residuals retained; they are not isolated device-event measurements.

CUDA loses to serial grid at 64 and 216 particles; the observed crossover is between 216 and 512.
At 8,000 its solver median is 7.611185 s (range 7.579296–7.632092), versus 63.791997 s serial
and 21.519382 s with twelve workers: 8.381× and 2.827× respectively. Its invocation median is
8.623839 s. Twelve-worker ratios do not establish the fastest CPU configuration at each size.
No original-method, whole-application, memory, bandwidth, utilisation or statistical-significance
claim is made. There was no tuning or launch study.

## Reproduction and verification

`python3 -m tools.cuda.performance report DIRECTORY/campaign` rechecks hashed raw/full results,
all three goldens, declared context, component comparisons and summaries before printing the report.
`python3 tests/evidence/checks/cuda_performance.py DIRECTORY/campaign` independently derives
physical equality and all statistics from full observations and raw clocks without collector imports.
Both run on the PC and locally; report text regenerates byte for byte. Current source and collector
files must match retained provenance for the independent audit. Each series also retains its ordinary
baseline report with throughput, sample standard deviation, stage sums/proportions and residuals.

Raw compact records preserve every per-step timing and diagnostic. Their `full_result` indices
identify losslessly compressed complete JSON observations and hashes; full components are compared
before any primary ratio is admitted. The records also retain the application's original stdout
hash, distinct from the compressed JSON representation. `correctness.json` remains replayable.

The initial PC parent test failure was a missing `scaling-protocol.md` in the temporary copy;
it was retained and resolved before timing. The timeout check preserved compressed complete
invocation records, including the partial result and failed-attempt time, CPU control and fresh
CUDA run. No benchmark timings are taken from these verification runs.

No commits, tags, remote state or parent gitlink were changed. The retained source hashes identify
measured bytes; an uncommitted tree does not establish a durable completion checkpoint. Fixed order,
shared host load, thermals, scheduling and three samples limit interpretation. Previous unavailable
Compute Sanitizer diagnostics and actual device-loss recovery remain unqualified; neither was rerun
or converted into a pass by this performance campaign.
