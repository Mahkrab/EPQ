# Error-only mapped diagnostic observations

Four device u64 records retain the original stage and particle/quantity minima.
Every write to those records passes through `record_diagnostic`. The original
atomic minimum still executes first. Only a strict decrease also executes a
GPU-scope atomic minimum into the corresponding mapped host word.

Initially both packets contain UINT64_MAX. Every strict decrease of a device
record contributes the same value to the host minimum. The final device minimum
must be one such contributing value unless no error occurred; no contributor can
be smaller than that final minimum. Thus after all threads complete, each host
word equals its device counterpart, irrespective of the arrival order of mirror
updates. Stage selection remains a separate ordered CPU scan; it is not a global
minimum across records. Successful lanes do not access host memory. The device
reads used to skip dependent work still use fast device records.

Only GPU threads contend on mapped words. CPU reads follow successful stream
completion; CPU resets follow completed checked observations. The host does not
poll or perform concurrent RMW operations. Unchecked submissions have no diagnostic
pointer and cannot update the mirror. A checked call that cannot establish
completion poisons the resource, so subsequent calls cannot read or reset it.
This uses no CPU/GPU system-scope atomic interoperability. The reported
HostNativeAtomicSupported=0 therefore does not contradict the GPU-only reduction.
NVIDIA distinguishes mapped-memory GPU atomics from host/other-device atomicity
and requires stream/event ordering around host accesses:
https://docs.nvidia.com/cuda/cuda-programming-guide/02-basics/understanding-memory.html

The existing stream completion remains before any caller result is published.
Completion errors retain precedence over submission errors, context-pop failures
retain their final priority, and no mapped packet escapes on failure. Native
mocks allow a failed completion to have dirtied private mapped words and check
that caller output remains untouched. Numerical faults remain retryable; the
existing begin-attempt reset clears both packets while preserving the appended
device address. All four original GPU diagnostic-writing sites use the helper.
Plane containment's separate velocity trailer remains unchanged.

`cuMemAllocHost` allocates the private32bytepacket under its owning CUDA context.
`cuMemHostGetDevicePointer` supplies its device address. The bridge appends that
eight-byte address to its device diagnostic allocation and uploads it once during
construction, outside solver steps. The device layout gains8bytes; existing
kernel arguments and Rust/CUDA interfaces do not change. Reset covers only the
first32devicebytes, never the address. Context destruction owns the pinned
allocation as well as device storage, including after uncertain completion; no
borrowed stack/Vec pointer is queued asynchronously. CUDA's context API explicitly
includes cuMemAllocHost allocations among resources cleaned up by cuCtxDestroy:
https://docs.nvidia.com/cuda/cuda-driver-api/cuda_driver_api/group__CUDA__CTX.html

Each context has its own packet. Context push/pop, !Send/!Sync ownership,
accepted/working swaps, cancellation polls and host validation stay unchanged.
There is no extra kernel, stream, thread, allocation per step, approximation,
changed floating-point expression or ordering, or fixed capacity. Normal
non-empty steps replace21diagnosticCudaMemcpyDtoHcalls(26witheffects) with ordinary
host reads. Five data copies remain: two summaries, the neighbour total and two
final vectors. Explicit stream waits and GPU launches are unchanged.

Counts describe explicit CUDA copy events. Error-only mapped accesses are real
system-memory traffic and are not counted as memcpy events; transaction/line
traffic is not measured. Memory sizes are requested capacities, not allocator
or page-granularity footprints. The supported device must provide mapped host
memory; no driver/security setting is modified to obtain it. Real device-loss
recovery and worst-case cancellation latency remain unqualified.
