# CUDA GPU evaluation and application handoff

## Outcome and evidence boundary

The optional CUDA backend executes uniform-grid discovery and the complete iterative solver on the
GPU, with host coordination and atomic host acceptance. The assessed implementation is Maelstrom
[`afb8ffbf6482d7d70fe01d03d6c32ce2277ad96b`](https://github.com/Mahkrab/Maelstrom/tree/afb8ffbf6482d7d70fe01d03d6c32ce2277ad96b).
Its 99 retained source, test, fixture and documentation hashes match the measured tree. The earlier
solver qualification matches
[`80cce8a8b8bb604ed988b176298211c6fed491f0`](https://github.com/Mahkrab/Maelstrom/tree/80cce8a8b8bb604ed988b176298211c6fed491f0);
the subsequent revision adds lifecycle measurement without changing kernels or arithmetic.

The [hardware qualification](/docs/project/development/milestones/03/assets/solver-v1/README.md)
retains 80 exact comparisons across 86 application runs. The
[primary-PC campaign](/docs/project/development/milestones/03/assets/performance-comparison-pc-v1/README.md)
adds 105 clean full-workload benchmark attempts and 108 exact comparisons. At 8,000 particles CUDA
reduces median completed solver time to **7.611185 s**, against **63.791997 s** for fresh serial grid
and **21.519382 s** for the fixed twelve-worker control: **8.381×** and **2.827×** respectively.
CUDA is slower than serial grid at 64 and 216 particles. These findings support this implementation
and tested workload on this PC; application integration and rendering remain future work.

## Requirement assessment

The [milestone plan](/docs/project/development/milestones/03/plan.md) owns the required outcomes.
No numerical equation, comparison budget, fixture or golden changed. Exact agreement establishes
preservation of the reference calculation. It does not establish greater physical accuracy; the
[reference evaluation](/docs/project/development/milestones/00/serial-brute-force.md#evaluation-and-limitations)
retains the modelling limits of fixed prediction membership, empirical corrections, eight fixed
iterations and simple plane contact, without physical-experiment or visual validation.

| Outcome | Assessment and evidence | Boundary |
| --- | --- | --- |
| Numerical agreement | Met for tested requests: the [qualification audit](/docs/project/development/milestones/03/assets/solver-v1/audit.json) checks 1,776,150 snapshot components exactly, including signed zero, with every required audit, CFL value, warning and status; the campaign adds 8,439,552 components | Parallel budgets were unnecessary for accepted results; neither tolerance agreement nor compact hashes excuse structural differences |
| Repeatability | Both complete goldens repeat under ordinary, measured and profiled execution, blocks of 32/64/128/256 lanes, and public replay; larger family members through 8,000 run and replay for 480 steps at 128 lanes | The full launch/repetition matrix applies to the goldens; no general cross-device or cross-libm bitwise guarantee follows |
| Failure safety | [Device transaction tests](https://github.com/Mahkrab/Maelstrom/blob/afb8ffbf6482d7d70fe01d03d6c32ce2277ad96b/tests/cuda_execution.rs) cover cancellation, rollback/retry, error precedence and independent lifetimes; [native injected failures](https://github.com/Mahkrab/Maelstrom/blob/afb8ffbf6482d7d70fe01d03d6c32ce2277ad96b/native/tests.cpp) cover allocation, transfer, launch, completion and cleanup | Cooperative cancellation waits for synchronised work; injected faults do not establish actual device-loss recovery |
| Public usability | Explicit optional build, device/launch selection, typed failure and public replay are implemented in the [CUDA guide](https://github.com/Mahkrab/Maelstrom/blob/afb8ffbf6482d7d70fe01d03d6c32ce2277ad96b/docs/cuda.md) and [CLI tests](https://github.com/Mahkrab/Maelstrom/blob/afb8ffbf6482d7d70fe01d03d6c32ce2277ad96b/tests/cli_workflow.rs) | Unsupported builds and unavailable devices fail explicitly; no CPU fallback or automatic device selection |
| Performance | Fresh same-binary serial-grid, twelve-worker-grid and CUDA controls qualify every admitted observation before ratios; the [report](/docs/project/development/milestones/03/assets/performance-comparison-pc-v1/campaign/report.md) retains spreads and invocation/lifecycle costs | One PC, three samples, fixed order and one scene family; twelve workers are a fixed control, not each size's fastest CPU setting |

## Decisions, diagnosed defects and costs

The [implementation record](/docs/project/development/milestones/03/phases/phase-01-cuda-solver.md)
owns the storage and arithmetic decisions. Occupied cells are sorted on the GPU; checked membership
bitsets preserve complete rows without fixed occupancy caps. Ascending identity traversal preserves
reduction order independently of lane scheduling. Separate completed launches provide whole-stage
barriers between immutable positions, complete multipliers and corrections.

Native CUDA `powf` exceeded the position budget from checkpoint 120. A binary64 library-power
alternative failed at checkpoint 480. The
[rejected controls](/docs/project/development/milestones/03/assets/solver-v1/rejected/README.md)
and reproduced variants retain those observations. The supported implementation uses the narrowly
adapted, licensed host power approximation to reproduce its tested rounding. No tolerance was widened
and no CPU contract was revised. Agreement remains conditional on the tested host/compiler/device
arithmetic; changing that combination requires qualification.

The [host/device path](https://github.com/Mahkrab/Maelstrom/blob/afb8ffbf6482d7d70fe01d03d6c32ce2277ad96b/src/cuda/solver.rs)
uploads the last accepted particles and planes for each attempt. Acceleration velocities return for
the shared host CFL check; predicted positions return for bounding and cell-width checks. Working
positions and multipliers stay resident through iteration. Stage errors and final state return for
ordered inspection and validation. Persistent scratch saves repeated allocation, but this interface
does not keep the accepted simulation exclusively on the GPU.

Membership alone occupies `4 * N * ceil(N/32)` bytes: 8,000,000 bytes at 8,000 particles, regardless
of sparsity. Other device buffers, host copies and stored observations add further costs. Checked
indices and allocation errors prevent silent truncation; neither 8,000 particles nor device-visible
memory establishes a maximum feasible input. Dense support can still require quadratic work.
Peak memory, adversarial performance and allocation exhaustion on real hardware were not measured.

Cancellation is polled between completed stages, including discovery and iteration work, and once
more before acceptance. Long stages can delay response; no worst-case latency bound was measured.
Real SIGINT qualification exited 130 after 189 accepted steps with an exact fresh CPU prefix. The
separate [forced timeout](/docs/project/development/milestones/03/assets/performance-comparison-pc-v1/cancellation/checks.json)
at 8,000 particles retained 76 accepted steps within the 30-second grace, matched a fresh CPU prefix,
and was followed by a successful CUDA golden check. These examples establish observed cancellation,
not a universal response deadline.

## Measured benefit and remaining uncertainty

The primary PC exposed a Ryzen 9 7900X with 24 logical CPUs and an RTX 4070 with 12,282 MiB under
Ubuntu 24.04.5/WSL2. The campaign used Rust/Cargo 1.96.0, CUDA 13.3.73, driver 610.88 and compute_89
PTX. One release binary ran every series. Each size used 480 factor-four-refined steps, eight
Jacobi iterations, one ordinary warm-up, three primary samples and a separate profile. The
[pre-collection protocol](/docs/project/development/milestones/03/measurement-protocol.md) owns
the exact workload, clocks, acceptance and timeout rules.

| Particles | Serial grid median (s) | Twelve-worker median (s) | CUDA median (s) | Serial/CUDA | Twelve-worker/CUDA |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 64 | 0.328366 | 8.426217 | 1.993456 | 0.165× | 4.227× |
| 216 | 1.255364 | 8.417105 | 2.307267 | 0.544× | 3.648× |
| 512 | 3.181563 | 7.330407 | 2.586743 | 1.230× | 2.834× |
| 1,000 | 6.815932 | 6.948293 | 3.033133 | 2.247× | 2.291× |
| 1,728 | 12.484920 | 7.997439 | 3.401524 | 3.670× | 2.351× |
| 4,096 | 31.378775 | 12.681015 | 4.694764 | 6.684× | 2.701× |
| 8,000 | 63.791997 | 21.519382 | 7.611185 | 8.381× | 2.827× |

The observed serial/CUDA crossover lies between 216 and 512 particles. At 8,000, CUDA samples span
7.579296–7.632092 s with sample standard deviation 0.026588 s; throughput is 504,521 particle
updates/s. Dividing the total by 480 gives 15.856635 ms per solver step, not a rendered frame time
or a real-time application guarantee. No fresh brute-force series supports an original-method ratio.

Completed-step totals include required allocations, packing, transfers, launches, synchronisation,
host diagnostics, final validation and atomic acceptance. At 8,000, separate CUDA construction and
teardown medians are 0.152743 s and 0.038824 s; invocation median is 8.623839 s. Construction includes
context/module/stream setup and any driver JIT, without isolating a cold-cache compilation cost.
First-step device-buffer allocation stays inside solver timing. Fresh brute-force audits, snapshot
copies, formatting and process costs contribute outside that timer. These boundaries matter when
estimating future application costs.

The separate 8,000-particle CUDA profile assigns 69.35% to Jacobi and 19.22% to discovery. These
synchronised host intervals include the corresponding device work, transfers, driver calls and
waiting; they do not isolate kernel execution or transfer overhead. Setup outside the step timer
cannot alone explain the small-input solver slowdown. Launch, synchronisation and transfer overhead
are plausible contributors, but their individual costs were not measured. No tuning was performed.
Memory use, bandwidth, GPU utilisation and CPU waiting behaviour were not measured. Fixed order,
shared Windows/WSL activity, scheduling, thermals and three samples limit causal or significance
claims. Other GPUs, drivers, targets and operating systems have no retained qualification here.

## Supported execution and reproduction

CPU-only builds require no toolkit or device. CUDA builds support native x86_64 Linux/WSL with
CUDA 13 headers/compiler, a compatible driver and host C++17 toolchain; cross-compilation and other
platforms are rejected. The [pinned CUDA guide](https://github.com/Mahkrab/Maelstrom/blob/afb8ffbf6482d7d70fe01d03d6c32ce2277ad96b/docs/cuda.md)
owns prerequisites, flags and hardware-test commands. From the Maelstrom checkout, with locked
dependencies already cached:

```sh
CUDA_HOME=/usr/local/cuda MAELSTROM_CUDA_ARCH=89 cargo build --release --locked --offline --features cuda
./target/release/maelstrom cuda-check --device 0 --repetitions 8 --format json
./target/release/maelstrom run falling-block-04 --backend uniform-grid --execution cuda \
  --device 0 --block-size 128 --refine-timestep 4 --steps 480 --checkpoints 0,1,120,240,480 \
  --format json --output cuda-run.json
./target/release/maelstrom replay cuda-run.json --format json --output cuda-replay.json
```

Device zero and 128 lanes are defaults; 32/64/128/256 lanes are supported. CUDA requires the grid
and rejects CPU worker options. Records distinguish physical input/configuration identity from
CUDA arithmetic identity, ordinal, lanes, embedded target and runtime device context. Public replay
restores execution settings and reruns the request; it neither resumes the final snapshot nor
certifies the result. An ordinal can identify different hardware on another machine.

Invalid option combinations exit 2. Missing feature/device, driver or PTX incompatibility during
construction exits 3; check the diagnostic, rebuild with the feature or correct the selected
environment/device. Runtime simulation failure exits 4 and preserves the last accepted snapshot;
cancellation exits 130. Input rejection and allocation exhaustion permit retry, while uncertain
driver failures poison the resource and require a new solver. There is no automatic CPU fallback,
device reset or qualified device-loss recovery. Output failure exits 5 and can supersede an earlier
status while retaining failures. Inspect both exit status and the complete record.

The [evaluation verification record](/docs/project/development/milestones/03/assets/evaluation-v1/README.md)
retains fresh local checks and reproduction commands for the campaign report and independent audit.
Rechecking retained PC data locally supplies evidence integrity, not a new hardware measurement.
Compute Sanitizer memcheck and racecheck previously exited 90 because the WDDM debugger interface
could not initialise; both remain unavailable diagnostics. Native ASan/UBSan and fault injection
passed their host paths, without replacing device memory/race checks.

## Application-integration handoff

The existing library already provides the integration boundary. Application work must preserve
these obligations without making presentation responsible for solver correctness.
Library callers select `Simulation::from_scene_with_execution` with `SearchBackend::UniformGrid`
and `ExecutionMode::Cuda { device, threads }`, then advance through `step` or
`step_with_cancellation`. The [constructor and acceptance path](https://github.com/Mahkrab/Maelstrom/blob/afb8ffbf6482d7d70fe01d03d6c32ce2277ad96b/src/simulation/mod.rs)
own this interface.

| Responsibility | Handoff obligation |
| --- | --- |
| Accepted observations | Consume `Simulation::snapshot()` and [`Snapshot::particles()`](https://github.com/Mahkrab/Maelstrom/blob/afb8ffbf6482d7d70fe01d03d6c32ce2277ad96b/src/simulation/state.rs). They expose immutable, ascending-identity particles in metres and metres per second, with a completed-step counter. Clone a snapshot to retain it while stepping; a renderer must not borrow device scratch or mutate solver state |
| Ownership and synchronisation | Construct, use and destroy the CUDA solver on its owning thread: its context is neither `Send` nor `Sync`. Successful calls complete before returning and restore the previous context. If a future application uses a simulation thread, construct the solver there and pass owned accepted snapshots to presentation; do not add unsafe sharing to bypass ownership |
| Presentation and scheduling | Render or export only accepted observations. Presentation cadence, interpolation, dropped display frames and camera state must not change fixed timesteps, iterations, membership, projection order, CFL handling or acceptance. A failed/cancelled attempt leaves the previous accepted state available |
| Cancellation and shutdown | Keep cancellation latched until observed, allow pending synchronous work to finish, and apply the resource invalidation policy. Preserve partial accepted results and publication failures; an application shutdown deadline cannot assume immediate stage interruption |
| CPU/GPU controls | Keep brute force, serial grid and explicitly configured threaded grid independently selectable with independently owned state. Record effective execution/device settings; any future automatic selection policy needs separate evidence |
| Fixtures and comparison | Retain the [frozen manifest](https://github.com/Mahkrab/Maelstrom/blob/afb8ffbf6482d7d70fe01d03d6c32ce2277ad96b/reference/manifest.json), independent equations/geometry tests, complete component reports, rejected arithmetic controls and raw PC evidence. Apply the [comparison policy](/docs/project/development/milestones/00/reference-verification.md) to every required observation; unchanged arithmetic requires exact agreement |
| Measurement | Preserve completed solver work, construction/teardown, fresh audits, snapshot copies, rendering/export and invocation costs as explicitly declared boundaries. Report end-to-end application timing separately. Rendering must not enter inherited solver comparisons silently |
| Graphics interoperability | No graphics API, shared graphics buffer, asynchronous snapshot stream or zero-copy presentation path is implemented. Any future interoperability must define ownership, completion and buffer lifetime, retain atomic acceptance, and undergo new correctness and timing qualification |

The [numerical contract](/docs/project/development/milestones/00/phases/phase-00-design-contract.md)
continues to own the simulation semantics. Changed arithmetic, workload or acceptance must follow
the plan's revision procedure and requalify affected controls, fixtures and comparisons. This handoff
does not implement the application or complete the final cross-backend project evaluation.

## Gate and checkpoint status

The evaluation and handoff are implemented locally. **G03 remains pending its separately authorised
completion checkpoint.** Existing annotated `milestone-03/phase-02/complete` and
`milestone-03/phase-03/start` tags identify the starting boundary in both repositories. The current
EPQ gitlink already pins the assessed Maelstrom commit; this work changes no simulator bytes or Git
metadata. Intended final tags are `milestone-03/phase-03/complete` and `milestone-03/complete` in both
histories, following implementation-first verification and checkpointing when authorised. Remote
publication and hosted validation remain separate.
