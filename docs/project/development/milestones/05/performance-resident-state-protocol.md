# Accepted-device-state comparison protocol

The [timing follow-up](/docs/project/development/milestones/05/performance-compilation-profile.md)
provides the 181-file control. This first residency slice keeps an up-to-date host snapshot and
all existing stage cancellation polls. It retains accepted device position/velocity buffers and
static planes across steps, initialises fixed storage once, and promotes working buffers only
after final host checks. It does not introduce lazy snapshots, larger cancellation segments,
device bounds/CFL/prefix calculations, graph replay, changed arithmetic or neighbour algorithms.

## Ownership and failure boundaries

Simulation configuration, particle count/identity order and planes are fixed for its lifetime.
The first attempt still allocates and uploads inside the completed-step timer. Later attempts
reuse device accepted inputs. Acceleration/prediction write working buffers; accepted buffers
remain unchanged until Simulation has validated the downloaded output, planes and final
cancellation poll. Promotion exchanges device pointers/capacities without a driver call, then
installs the host snapshot. It must reject poisoned or unopened attempts and repeated acceptance.

Numerical failure, allocation exhaustion, cancellation and predicate panic must leave accepted
host/device values unchanged. Retry restarts from accepted device buffers, never partial work.
Uncertain driver failures still poison the resource. Native ownership/fault tests must demonstrate
that promotion makes no CUDA calls, swaps both vector buffers and capacities, and cannot partly
promote on rejection. Independent CPU/hardware tests must cover repeated acceptance, empty/tail
counts, all supported blocks, uncommitted output, every existing cancellation poll and retries.

All streams remain synchronous at the existing boundaries. Successful warm preparation omits
fixed reservations and unchanged uploads rather than merging numerical stages. Larger checked
submission segments require their own cancellation/failure design; this experiment does not
claim full device-owned execution or removal of final host downloads.

## Primary-PC comparison

Use immutable source exports and separate targets/binaries; leave ordinary checkouts and installed
commands alone. Build locked offline release with CUDA, target 89 and precise arithmetic. Check
both binaries contain freshly compiled, identical PTX, since device arithmetic is unchanged.
Require 4 GiB free guest RAM and 2 GiB GPU memory, with 120-second request ceilings and 30-second
cancellation grace. Retain failures and stop an incomplete comparison without replacement samples.

Keep device zero and block 128. Run the seven existing fixture sizes for 480 refined steps with
checkpoints 0/1/120/240/480. Then compare 8,000 particles with those checkpoints, 110,592 without
checkpoints, and 110,592 with XSPH 0.01 and confinement 0.1 m/s. All use refinement 4, eight
iterations and 480 unpaced steps. Give each variant one warm-up and five measured runs per
workload, alternating pair order. Require exact complete physical records and warning schedules;
allow only build identity and measurement metadata to differ.

Qualify release source/tests, explicit CUDA library/application/integration tests, strict Clippy,
formatting and native injected faults with address/undefined-behaviour sanitisation. Keep the
retained prefix, row sorting and export timings in both variants. Run separate disabled-effect
full-motion traces after timings to verify unchanged launches/readbacks and reduced uploads and
completions. Validate counts from raw trace tables; instrumented times are not primary speedups.

Reconstruct sums, medians, paired effects and physical agreement independently; reject altered
reports/results and retain commands, exits, environment, source/binary/tool/input hashes, all
samples and trace failures. Keep private profiler metadata out of shared evidence. Make a written
engineering assessment under the existing policy, including slower pairs, uncertainty and cost.
No automatic percentage/range rule decides retention. No commit, tag, push, branch or gitlink
change is authorised. Compilation throughput remains a separate follow-up, not a claim here.
