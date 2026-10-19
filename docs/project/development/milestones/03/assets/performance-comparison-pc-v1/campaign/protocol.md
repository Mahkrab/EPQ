# CUDA and CPU completed-step measurement protocol

This extension freezes `cuda-comparison-v1` before collection. It inherits the
[measurement policy](/docs/project/development/milestones/00/measurement-protocol.md):
64, 216, 512, 1,000, 1,728, 4,096 and 8,000 particles in that order; 480 steps;
factor-four refinement; eight Jacobi iterations; checkpoints 0, 1, 120, 240 and 480;
one complete ordinary warm-up, three fresh-process total-only samples and one separate
profile per size. The 120-second invocation timeout and 30-second SIGINT grace apply
unchanged. An unclean warm-up prevents primary sampling; one bounded profile is still
attempted. Failed samples stop that size's primary sequence. Preserve all attempts.

Run sequentially through `ssh pc`, without concurrent project checks on that device.
Collect **serial uniform grid**, then **threaded uniform grid with twelve workers**,
then **CUDA device zero with 128 lanes per block**. Twelve workers were the best
observed large-input setting in the preceding CPU study; 128 lanes is the qualified
default CUDA launch. These are fixed comparisons across every size, not a selection
of each size's most favourable observation. No launch study or tuning is planned.
No brute-force series is included, so no original-method speedup may be claimed.

Build one shared feature-enabled release binary with locked offline dependencies,
default Cargo optimisation and no custom Rust flags. Use `CUDA_HOME=/usr/local/cuda`
and `MAELSTROM_CUDA_ARCH=89`; native flags remain those in the build script (including
disabled contraction and preserved denormals). Record actual source, native kernel,
embedded PTX and executable hashes, both base commits, dirty state, toolchains,
target and flags. Record CPU identity/topology/affinity, guest-visible memory,
GPU identity/memory/capability, driver, toolkit, environment and UTC order. Do not
change affinity, priority, frequency, drivers or host configuration. GPU memory and
guest memory are context, not a working-set measurement.

The primary denominator is the sum of completed transactional step elapsed times,
using the existing common outer monotonic timer. Each CUDA step includes host input
validation, settings, scratch reservation/growth (including first-step device
allocation), packing, all uploads, acceleration and host CFL checks, prediction,
bounding checks, cell construction/sort/discovery, every configured Jacobi stage,
error downloads, projection, reconstruction, final downloads, host validation,
cancellation polls and atomic host acceptance. Native operations synchronise their
stream before returning. There is no work deferred across returned steps and no
cross-step batching. CPU steps include the corresponding validation, discovery,
solver, dispatch/barrier and acceptance work. Failed attempts never enter successful
totals. Checkpoint copying, fresh brute-force density audits, hashing, input loading,
record allocation, formatting and publication stay outside these timers for all
backends. Invocation wall time includes these costs and is reported separately.

Measured records also time solver construction and consuming destruction separately.
Construction includes validated host state and, for CUDA, driver/context creation,
module loading (including any driver JIT) and stream creation; it is a combined
observed setup cost, not an estimate of its individual components. Device buffers
are allocated inside the first step, not hidden in construction. Destruction includes
the context and its persistent buffers. No module compilation or buffer setup is
omitted from both these boundaries and invocation time. Failed construction need
not yield these successful-lifecycle fields. Ordinary warm-ups remain uninstrumented.

Stage profiles are synchronised **host elapsed** intervals, including transfers and
host checks belonging to each stage. They partition completed work without overlap;
the residual is retained. They do not measure isolated GPU kernel time, utilisation,
bandwidth or transfer-only cost. Additional device-event clocks are unnecessary for
this comparison and are not substituted for primary totals.

Before each series, retain the full 64-particle ordinary correctness result and
compare it exactly with the frozen golden. Retain compressed full results for every
benchmark observation, alongside compact sign-sensitive hashes, raw per-step timings,
audits, CFL values, warnings, failures, commands, exits and invocation times. Recheck
every clean complete observation against the same-size fresh serial-grid warm-up
using the component verifier in exact mode. The qualified arithmetic remains
unchanged; no tolerance is used. Check backend, build, device and execution context
separately, excluding only declared execution/build context from physical equality.
A disagreement rejects the report and supplies no accepted ratio. Missing clean
controls or incomplete primary sets supply no ratio. Partial or warning-bearing
results remain visible but never supply full-workload timings.

On timeout send SIGINT and wait for the current synchronised operation/stage and
accepted-prefix publication. If grace expires, kill and reap the process before
starting another invocation. The solver owns an isolated context; its destruction
is the abandonment boundary, with no borrowed asynchronous host storage. Retain
timeout, signal/exit, accepted steps and failed-attempt time. A killed process is not
evidence of successful cancellation or device-loss recovery. Stop the campaign if
the collector itself is interrupted; never overlap outstanding invocations.

Report all three primary totals, median, min/max, mean, sample standard deviation,
median step time, particle updates/s, invocation median, construction/destruction
medians and separate stage sums/proportions/residuals. Ratios are fresh serial median
/ CUDA median and fresh fixed-twelve-worker median / CUDA median. Never multiply
historical ratios. Retain fixed-order, shared-host, thermal, scheduling and three-sample
limitations. A slowdown satisfies the experiment; no optimisation is required.

Collect with `python3 -m tools.cuda.performance collect NEW_DIRECTORY`; verify and
regenerate with `python3 -m tools.cuda.performance report DIRECTORY`. Keep these
pre-collection protocol bytes with the campaign. An independent raw-data audit must
recompute acceptance, statistics, profile sums and ratios without importing the
collector. Missing primary-PC hardware leaves the campaign incomplete; provisional
local timings cannot replace it.
