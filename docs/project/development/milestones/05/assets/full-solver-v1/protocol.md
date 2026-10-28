# Full CUDA solver reprofiling, 28 October 2026

Control is the retained 189-file integer-quartic candidate, including all eight
existing optimisations and prior uncommitted density/validation/power work.
Maelstrom HEAD1e0085926d05c42949bb76b55d177d42a1f8f94f;EPQ HEAD
1f76097a218266822cdf344c38db75ed128628a8. No history/gitlink changes.

Tool configuration was explicitly authorised. Record initial failures, changes,
original settings and rollback instructions. The initial registry key-creation
command erroneously removed driver subkeys; stop other work, recover and verify
all affected keys/values/ACLs before profiling. The recovery receipt is separate
from performance evidence. No hives/private registry data enter public evidence.

Establish current precise compute_89 release source/binary/PTX identities.
Workloads: CUDA0/block128/refinement4/eight iterations/480 unpaced steps/no graphics;
8000 bundled falling block with checkpoints0,1,120,240,480 for primary benchmarks;
110592 counted48-cubed block and110592 XSPH.01/confinement.1 without checkpoints.
Run one warm-up plus five ordinary control samples per workload before diagnostic
profiling. Admission4GiBhost/2GiBGPU; ordinaryruns120s;qualification600s;traces240s;
selective counter captures600s. Completed-step clocks include all preparation,
checks,transfers,submission,completion,cancellation/acceptance; construction,
teardown,output/audit/storage separate. Preserve every slow/failing record.

Profile ordinary control and diagnostic markers separately. Full480-step Nsight
CUDA/API timelines at both sizes including velocity effects; retain stage and
step boundaries, kernel and copy activity/APIcorrelation, queue gaps, waits,
CPU work and driver calls. Use explicit non-overlapping categories/interval unions;
do not sum overlapping GPU work and host synchronisation as separate costs.
Collect CPU samples/software/hardware counters where supported; distinguish
active CPU from scheduled-out/wait/poll, kernel-launch gaps and shader execution.
Use NVTX/host clock diagnostic exports only as needed and measure their overhead
against equivalent ordinary source. Verify physical/config/ordereddiagnostic
identity excluding only measurements/build_revision.

Investigate NsightCompute hardware counters, achieve occupancy/cache/DRAM/stall
metrics where accessible; use selected early/late launches/iterations and record
replay/cache/clock settings and pass counts. Counter captures are not whole-solver
speedups. Attempt appropriate memory/race/synchronisation diagnostics after setup.
Quantify trace and annotation/frame-pointer overhead against ordinary samples.
Windows-native whole solver is not currently supported; investigate available
compiler/runtime tools and a separately labelled driver-boundary control if useful.
Do not silently equate WSL and native Windows, or infer an unmeasured conversion.

Only implement a candidate after measured attribution identifies a convincing
opportunity. Preserve all eight retained optimisations, exact numerical/error
semantics, stage boundaries, cancellation/rollback and resource/thread ownership.
No fixed neighbourcap, approximations or changed accumulation order. If warranted,
up to three focused trials (one warm-up,two alternating pairs,size) before final
source/test/doc freeze. Final benchmark one warm-up plus five alternating pairs
per primary workload; firstmeasuredcandidate/control. Seven64..8000regressions.
Keep campaigns separate/no replacements; fullrelease/CUDA/boundary/execution,
Clippy/fmt,nativeASan/UBSan,CPUfeatureisolation,devicechecks proportional to change.
Finalordinary full480step profiles both variants/sizes/effects plus stage/counter
comparisons with matched settings where available. Report regressions, ranges,
ranked contributions, overhead, uncertainty and engineering retention decision.
If no convincing beneficial candidate, leave production untouched and document
the measured bottlenecks and limits; absence of change is a valid outcome.
Independent readers,source reconstruction,raw archives and integrity readback.
