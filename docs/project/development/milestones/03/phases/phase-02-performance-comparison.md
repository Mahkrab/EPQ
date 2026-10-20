# Phase 2 primary-PC GPU performance comparison

## Starting point

Work began from clean EPQ `abc441e2c278eb48c4828c2536bfea2a6b36f2b4` and Maelstrom
[`80cce8a8b8bb604ed988b176298211c6fed491f0`](https://github.com/Mahkrab/Maelstrom/tree/80cce8a8b8bb604ed988b176298211c6fed491f0).
The [solver qualification](/docs/project/development/milestones/03/phases/phase-01-cuda-solver.md)
established hardware correctness but supplied no timed GPU comparison. The measurement path already synchronised CUDA operations before returning, but lacked
separate construction and destruction costs.

## Scope and outcome

The [GPU measurement extension](/docs/project/development/milestones/03/measurement-protocol.md)
was written before collection. It preserves the seven sizes through 8,000 particles, 480 steps,
refinement, checkpoints, warm-up, three primary samples, separate profiles and timeout/grace rules.
The [retained collection](/docs/project/development/milestones/03/assets/performance-comparison-pc-v1/README.md)
contains **105 complete benchmark attempts**, three full golden checks and 21 separate profiles.
All attempts completed without warnings, failures or timeouts. All 108 component comparisons passed
exactly, including signed zero, over 8,439,552 snapshot components.

| Particles | Serial median (s) | Twelve-worker median (s) | CUDA median (s) | Serial/CUDA | Twelve-worker/CUDA |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 64 | 0.328366 | 8.426217 | 1.993456 | 0.165× | 4.227× |
| 216 | 1.255364 | 8.417105 | 2.307267 | 0.544× | 3.648× |
| 512 | 3.181563 | 7.330407 | 2.586743 | 1.230× | 2.834× |
| 1,000 | 6.815932 | 6.948293 | 3.033133 | 2.247× | 2.291× |
| 1,728 | 12.484920 | 7.997439 | 3.401524 | 3.670× | 2.351× |
| 4,096 | 31.378775 | 12.681015 | 4.694764 | 6.684× | 2.701× |
| 8,000 | 63.791997 | 21.519382 | 7.611185 | 8.381× | 2.827× |

These are completed solver totals for 480 steps. CUDA loses to serial grid at 64 and 216 particles;
the observed crossover lies between 216 and 512. Twelve workers incur substantial small-input
overhead. Their ratios describe this fixed setting, not the fastest possible CPU configuration.

## Decisions and implementation

### Fixed controls and numerical admission

Fresh serial-grid controls run first, then twelve-worker grid controls, then CUDA device zero
with 128 lanes per block. Twelve workers were the preceding CPU study's best observed large-input
setting; 128 lanes is the qualified CUDA default. Both settings stay fixed across every size.
No worker/launch search or brute-force series was collected; historical ratios cannot supply
an original-method denominator.

The collector extension selects CUDA and retains compressed full observations alongside compact
hashes. The report checks every clean complete observation against its same-size serial-grid
warm-up using the exact component verifier. Physical identity, signed zero, checkpoints,
audits, CFL values, warnings and status remain acceptance obligations. Device/build/execution
context is checked separately. No tolerance, arithmetic, kernel, fixture or dependency changed.

### Completed work and visible setup

The common step timer includes validation, scratch reservation/growth, packing, transfers,
launches, stream completion, solver work and atomic host acceptance. The first
step pays for device-buffer allocation. There is no deferred work or cross-step batching.
Independent density audits, snapshot recording and output remain outside the solver timer.

Measured records now expose construction and consuming destruction separately. CUDA construction
combines validated host state, context/module loading, any driver JIT and stream setup. Destruction includes
the persistent buffers and context. Invocation elapsed time includes setup, audits, output and
process costs. Profiles retain synchronised host elapsed stage sums and residuals; they are not
isolated device timings or evidence of GPU utilisation, bandwidth or memory use.

At 8,000 particles the CUDA profile spends 69.35% in Jacobi and 19.22% in discovery, compared
with serial grid's 85.38% and 11.48%. Host CFL/bounding checks, error inspection, transfers and
acceptance remain serial coordination responsibilities. The profile cannot separate kernel
computation from driver, transfer or synchronisation costs. No tuning was introduced. CUDA
construction is about 0.15 s and destruction about 0.04 s per invocation; at 8,000 the invocation
median is 8.624 s against 7.611 s of solver work. Setup alone does not explain the small-input
solver slowdown, since it is outside that timer.

## Verification

Before collection the PC passed **219 feature-enabled release Rust tests**, including explicitly
selected device cases and two doctests, strict all-target Clippy and **41 parent tooling tests**.
An initial parent-test attempt failed because the isolated PC copy omitted the older scaling
protocol. Its raw failure is retained; copying that required fixture resolved the failure.
Locally, all **208 CPU Rust tests**, formatting and strict Clippy passed. Seven focused
collector/auditor tests passed locally and on the PC, including a false-median control with
coherently updated hashes. Four historical reports and both comparative JSON summaries regenerate unchanged.

Independent audits verify raw/full hashes, source/collector identities, physical outputs, statistics,
throughput, lifecycle medians, profiles/residuals and ratios without importing collector code. Reports regenerate byte for byte on the PC and locally.

A real forced 1.5-second timeout at 8,000 particles exited 130 after 76 accepted steps, within
the 30-second grace period. The accepted snapshots, checkpoint audits and CFL prefix matched a
fresh CPU control exactly. A subsequent CUDA correctness run matched the frozen golden. Each
invocation is waited for and reaped before the next begins.

## Limitations and Gate G02

**G02 passes locally on the recorded primary PC.** The PC exposed a Ryzen 9 7900X,
24 logical CPUs, an RTX 4070 with 12,282 MiB, CUDA 13.3.73, driver 610.88 and Rust/Cargo 1.96.0
under Ubuntu 24.04.5/WSL2. One release binary served all series, without custom Rust flags,
affinity, priority or frequency changes. Fixed order, shared host activity, scheduling,
thermals and three samples limit interpretation. No tuning, larger-input study, memory measurement or device-loss recovery
qualification is included. Earlier unavailable Compute Sanitizer diagnostics are not converted
into passes by these timings.

The assessed simulator is now committed as Maelstrom
[`afb8ffbf6482d7d70fe01d03d6c32ce2277ad96b`](https://github.com/Mahkrab/Maelstrom/tree/afb8ffbf6482d7d70fe01d03d6c32ce2277ad96b),
with the parent gitlink advanced to that exact instrumentation revision for publication and PC
synchronisation. Original source hashes and raw evidence retain their collection-time provenance.
The existing `milestone-03/phase-02/start` tags are unchanged. Subsequently authorised annotated
`milestone-03/phase-02/complete` tags identify the local completion checkpoints in both histories.
The original campaign is unchanged; publication of these new checkpoints remains separate.
