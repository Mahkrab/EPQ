# Selection after fresh profiling

The fresh retained-build large diagnostic root is7.314881ms/step. GPU-idle API
intervals are0.832477msinDtoH and0.788774msinStreamSynchronize, reproducing1.621251ms.
Small values are0.629589+0.681011ms. Most observation boundaries are required
for checked error/cancellation or host CFL,bounds and capacity dependencies.

The standalone same-context diagnostic shows32-byte DMA execution well below
one microsecond but two driver/host round trips. Pinning alone offers little;
copy-before-wait and pinned-async-before-wait regress. Graphs with a copy also
regress; kernel-only graphs save only a few microseconds and need argument/cache
updates while retaining the dominant readback round trip. No production code
for those approaches was added. The first graph collector corrected a record
count assertion and reused hash-verified completed raw output; no micro sample
was replaced.

An error-only mapped host mirror avoids the diagnostic-copy command entirely.
A separate proof-of-mechanism passed1920pattern/block/count/slot/repeat cases,
including reversed contention order,zero counts and110592lanes, comparing mapped
and device minima to an independent CPU expectation. CanMapHost=1,UVA=1,
HostNativeAtomicSupported=0. Only GPU threads compete with these device-scope
atomics; CPU reads/resets occur at completed stream boundaries, so host/GPU
system-scope atomic interoperability is neither used nor assumed.

Control versus mirror boundary medians are53.729/26.404us(oneemptykernel),
55.395/32.727us(fouremptykernels),158.897/125.618us(one250kcyclekernel),
429.857/400.278us(four250kcyclekernels). These are diagnostic costs, not a solver
speedup. A production candidate is justified for qualification and matched
whole-solver measurement.

Keep device diagnostic records and all existing GPU ordering guards. Append one
mapped-host address to the device allocation, load it only on errors, and mirror
only winning minima. The private context owns a32bytecuMemAllocHost allocation;
cuCtxDestroy releases it along with context-owned device storage. CPU resets both
packets only after prior checked observations completed. Keep every explicit
stream completion, cancellation poll, stage/numerical error priority and accepted
buffer swap. There are no shared host packets, deferred borrowed host pointers,
new launches or numerical-operation changes. Normal diagnostic DtoH calls should
fall21->0(without effects),while five data downloads remain. Confirm rather than
assume the complete-solver improvement and device resource impact.
