# CUDA solver code audit

## Scope and assessment

This audit was requested on 26 October 2026 after the performance discussion. It follows the
CUDA execution path, including Rust state ownership, numerical contracts and observations.
It does not assess CPU-only backend performance or implement the proposed changes.

**The remaining gap is substantial, and the current design still carries the shape of a checked
CPU reference executed through GPU stages.** The retained optimisations removed real costs, but
the next investigation needs to consider timestep ownership, neighbour construction and device
arithmetic together. Neither a larger block nor adding CPU threads is a credible complete answer.

Both repositories were on `phase/05-03-optimisation`. Maelstrom's committed base was
[`87145510a9e5d812066138c35f1fac82e4f593b0`](https://github.com/Mahkrab/Maelstrom/tree/87145510a9e5d812066138c35f1fac82e4f593b0),
with uncommitted prefix and cooperative-sort changes. All 180 files matched the measured
control fingerprint `0383da2a3781bfe8e7a4e1518fa38e258611a2502d7194c822a0ad9236b1c4e0`.
The [reconstruction](/docs/project/development/milestones/05/assets/host-coordination-v1/source-reconstruction.json)
and its patches identify that working state; a link to the base commit alone does not.
The [file review](/docs/project/development/milestones/05/performance-cuda-file-review.md) covers every
native implementation file, the Rust CUDA and simulation modules, and relevant application paths.
Its [evidence](/docs/project/development/milestones/05/assets/cuda-code-audit-v1/README.md) records file hashes and calculations.

## What the measurements actually require us to explain

The recent primary-PC control took 8.675 s for 110,592 particles, 480 refined timesteps and eight
iterations: approximately one simulated second, without rendering or checkpoint audits. Real time
under that same request needs about 8.7 times the present solver throughput. The 259 warning-bearing
steps also prevent treating completion as a satisfactory fluid-quality result. These observations
come from the [coordination investigation](/docs/project/development/milestones/05/performance-coordination.md),
not a new campaign conducted for this audit.

Its separate control-only GPU trace gives the following ranking. Percentages use that trace's
8.888 s window, never the ordinary solver median.

| Work | Device time | Share of trace window |
| --- | ---: | ---: |
| Correction | 2.566 s | 28.9% |
| All neighbour construction: keys, cell sort, count, fill and row sort | 2.050 s | 23.1% |
| Density and multipliers | 1.395 s | 15.7% |
| Separate active-distance validation | 0.498 s | 5.6% |

Device activity occupied 6.744 s; gaps occupied 2.144 s. Even removing every gap would bound this
particular window at about 1.32 times faster. Removing the entire correction kernel instead would
bound it at about 1.41 times faster. Neither is an available optimisation or a prediction. They
show why blaming host arithmetic, WSL or one power function cannot explain away the whole gap.

## Main findings

Priorities describe performance investigation, not newly demonstrated correctness failures.
Measured costs, source observations and unmeasured hypotheses are distinguished below.

### F01 — High: accepted state forces a host round trip every timestep

[Simulation](/Maelstrom/src/simulation/mod.rs) owns an ordinary host `Snapshot`.
[CudaSolver](/Maelstrom/src/cuda/solver.rs) receives those particles every step, packs fresh position
and velocity arrays, uploads them and the unchanged planes, and later downloads final positions
and velocities. It downloads accelerated velocities for CFL and predicted positions for bounds.
Counted neighbour rows make another device-to-host-to-device trip through a CPU prefix.

This is a coherent rollback design, but device allocations surviving across steps are not the
same as simulation state staying resident. The trace contains 4 uploads and 26 downloads per
step: about 3.54 MB and 6.19 MB respectively. Downloads include 21 small diagnostic packets and
five full array reads. Their aggregate bandwidth does not establish a saturated link; the
dependencies and blocking boundaries matter.

The larger opportunity is device-owned accepted/working buffers, validation before a device
commit, and host materialisation at actual observation boundaries. CFL/bounds reductions and
checked integer scans fit that design. It must preserve cancellation, retry, overflow and error
precedence; the existing synchronous snapshot API cannot simply be declared resident without
addressing when callers obtain its host contents. The earlier small CPU percentages justify
deferring isolated reductions, not dismissing this combined ownership problem.

### F02 — High: the bridge repeatedly drains work that stream order already sequences

[The bridge](/Maelstrom/native/bridge.cpp) wraps storage and solver calls in `solver_call`, which
pushes the context, executes the action, synchronises the stream, optionally downloads a result,
then pops the context. Each step has 51 stream completions, plus the campaign's initial reset.
Jacobi and projection still return to the CPU separately for each of eight iterations.
Successful diagnostics are copied back even though later kernels already know how to suppress
dependent writes after an earlier device failure.

This is an application boundary to redesign, not evidence that Rust's calling convention is slow.
Test a larger checked submission segment, device-visible failure state and fewer completion
observations; evaluate graph replay only after that dependency model is clear. A graph alone
does not remove the required readbacks or host prefix. More CPU submitter threads would not
parallelise a dependent single-stream timestep.

### F03 — High: global cell sorting still uses a launch-heavy bitonic algorithm

The cell-key array contains 32-byte records with three signed 64-bit coordinates and an index.
At 110,592 particles it is padded to 131,072 entries. [Operation 13](/Maelstrom/native/bridge.cpp)
issues 153 bitonic passes, each a separate kernel over the padded array, every timestep.
These account for 73,440 of 99,840 launches in the trace. Batching already removed per-pass host
completion, but did not remove these passes, comparisons or global exchanges. Sorting took
0.509 s of device time; it is meaningful without being the largest measured cost.

A device radix sort or a justified cell-binning design deserves a bounded comparison. Establish
its real key domain, deterministic ties, temporary memory and dense/extreme-coordinate behaviour.
Do not silently replace the general 64-bit domain with a truncated packed key. Sorting the cell
metadata also does not spatially reorder particle attributes; that is a separate decision.

### F04 — High: neighbour construction repeats its searches and loses spatial locality afterwards

[discover_row](/Maelstrom/native/neighbours.cuh) performs nine binary lower-bound searches per
particle, then scans up to 27 adjacent cells. Count and fill repeat this geometry and distance work.
The bounds-selected power-of-two width is conservative; for the usual radius 0.1 m it becomes
0.125 m, admitting more candidates than a radius-width grid. The exact excess requires observation.

Numerical lanes subsequently walk variable-length, identity-sorted rows and gather positions by
index. Particle positions remain in identity order rather than following the sorted cell records.
The 12-byte vector layout and row-major neighbour storage are concrete locality candidates,
but cache misses, bandwidth saturation and the best replacement are not measured facts here.
Repeated block-local reuse must be demonstrated before adding shared-memory staging.<sup><a href="#ref-s065">S065</a></sup>
The trace's peak tracked allocation was about 59.7 MB, so this workload does not show VRAM
capacity exhaustion. Improving access is a throughput question, not proof that all buffers need shrinking.

Compare cell-run indexing and reusable lookup information before redesigning every buffer.
Then test device spatial permutation, component storage or a neighbour layout matched to warp
access. Keep stable identity separate from physical storage and preserve the required row-sum
order through an explicit mapping. Dense cells and the rare all-pairs overflow-validation path
remain resource risks; a sparse benchmark is not proof of a universal linear bound.

### F05 — High: the correction path pays for a CPU-library-compatible power operation

[ordered_power](/Maelstrom/native/power.cuh) performs table-indexed binary64 logarithm/exponential
arithmetic inside the pair loop to reproduce host `powf` rounding. The default exponent is 4,
yet it still takes the general path. [Correction](/Maelstrom/native/solver.cu) executes this for
active pairs across eight iterations whenever artificial-pressure weight and strength are non-zero.

This is a clear precision/compatibility cost to attribute, not proof that all 2.566 s of correction
belongs to power. Squaring twice, CUDA `powf`, or changing contraction can alter results and error
behaviour; none is an equivalent drop-in replacement. The earlier constant-to-global table trial
was unsuccessful and must not be repeated as though it were new. A separately qualified arithmetic
comparison should measure generated instructions, runtime and fluid-quality consequences, with
the current compatibility path as its control.

### F06 — Medium to high: numerical rows are revisited to preserve detailed reference order

[Operation 5](/Maelstrom/native/solver.cu) checks every fixed neighbour distance before multiplier
work; operation 6 filters again for density, owner gradients and the remaining squared-gradient
suffix; operation 7 revisits rows for correction. Prefix reuse is present and should stay.
Repeated source-level distance expressions within an individual loop were already shared in the
inspected generated PTX, so source call counts overstate the available saving. Cross-loop work remains.

Density/owner fusion or reusable per-iteration pair geometry merit targeted evaluation, accounting
for registers and cache/storage traffic. Positions change after each projection, so caching across
iterations without invalidation changes the simulation. The completed global multiplier snapshot
must precede correction. The separate operation 5 exists for global failure precedence; removing
it requires preserving that precedence or explicitly revising the contract.

The Poly6 and Spiky helpers also express radius powers, normalisation coefficients and divisions
inside pair evaluation. Inspect the remaining generated instructions before precomputing them;
loop-invariant work may already have moved. Any explicit coefficient cache must preserve the
binary32 evaluation and the point at which an invalid intermediate becomes observable.

### F07 — Medium: allocation, validation and invariant setup are repeated on the host

[native.rs](/Maelstrom/src/cuda/native.rs) allocates and initialises each download vector before the
driver overwrites it. The solver then copies accelerated velocities and predicted positions into
another vector representation. `prepare` reserves all 14 slots and each upload reserves again;
even satisfied native reservations enter the completion wrapper. Settings recreate validated PBF
parameters and the reference Poly6 weight, while host acceptance rechecks identities, finiteness
and every plane after the GPU's checks. Private accepted state is also revalidated before a step.

Reuse owned host staging buffers, cache immutable validated settings/planes, and distinguish
structural invariants from mutable numerical results. Avoid introducing uninitialised Rust values
merely to remove a zero-fill. The measured bounds/CFL/prefix CPU calculations together cost about
0.172 s per large run, not several seconds. The historical reservation-only trial found no clear
whole-run benefit; these are supporting changes, not an explanation of the full shortfall.

### F08 — Medium: launch resources and diagnostic traffic lack current attribution

The shared operation entry still handles unrelated stages with one block-size setting. A complete
and a targeted entry-point specialisation were already tested without useful larger-run gains;
splitting files or removing dispatch alone is not an established optimisation. There is no current
performance sweep proving 128 better than 256. The measured shared entry's 45 registers and zero
reported local/shared allocation do not establish achieved occupancy.<sup><a href="#ref-s065">S065</a></sup>

The constraint array is written but has no production numerical consumer; component tests inspect
it. The full error array is written by ordinary particle operations, although production row-sort
uses it only after fill. These are specific avoidable-write candidates, not a reason to disable
`Checked`. Prove which stores and finite checks are redundant and keep observable failures.

### F09 — High for compilation: observations are copied and serialised on the critical path

[Export](/Maelstrom/src/export/mod.rs) captures an entire portable snapshot at every step, even
when the schedule does not need an image. [FrameWriter](/Maelstrom/src/export/offscreen.rs) copies
it back into particles, renders, waits for pixels, encodes and publishes a PNG, then serialises
the whole snapshot to JSON for a hash. [Drawing](/Maelstrom/src/render/gpu.rs) transforms particles
on the CPU and creates fresh GPU geometry buffers; colour, depth and readback resources are also
recreated per offline frame. CUDA and graphics exchange data through host arrays, not shared device storage.

The growing complete frame list is converted and written to `progress.json` after every frame:
over F frames this processes F(F+1)/2 frame records. Publication synchronously flushes files.
The manifest's `encoding` interval ends before publication, snapshot JSON hashing and progress
updates; the existing three timing fields therefore do not cover the command's complete cost.

This is a stronger compilation finding than the generic claim that one CPU core is busy.
Capture only necessary observations, reuse graphics resources, and measure a bounded render/
readback/encoding pipeline with ordered output and backpressure. Progress can remain recoverable
without repeatedly rewriting its complete history. Preserve the existing hashes and failure
semantics or version any format change. These savings belong to command throughput, not solver time.

### F10 — Medium for headless observation: a GPU run can invoke a quadratic CPU audit

[Requested workflow checkpoints](/Maelstrom/src/workflow/mod.rs) call
[audit_density](/Maelstrom/src/diagnostics.rs), which deliberately builds brute-force CPU rows.
That independence is useful for small correctness fixtures, but O(N²) discovery is an expensive
observation at large N. It remains outside primary solver timing. Large-run timing protocols
correctly disabled checkpoints; an ordinary user's command can still incur this cost. Separate
independent verification from routine large-scene observation explicitly. It is not on the
ordinary compilation path and does not explain its frame-by-frame stalls.

## WSL2, language boundaries and Windows presentation

**Rust/C++:** this is an in-process C ABI over plain buffers and an opaque handle. It is not RPC,
does not marshal a particle into C++ on every neighbour interaction, and never calls Rust from
each CUDA lane. The cost visible in source is what the boundary requires: copies, allocation,
context binding, blocking transfers and repeated driver completion. Rewriting Rust orchestration
in C++ while keeping that protocol would retain those costs. The direct FFI-call cost has not
been isolated. Keep the safe ownership boundary; improve submission granularity behind it.
Context push/pop binds the calling CPU thread; it does not itself prove a GPU context switch.
The context uses flags zero (`CU_CTX_SCHED_AUTO`), whose documented waiting policy can spin.
A saturated CPU core can therefore include driver waiting; it does not prove one core is doing
useful arithmetic throughout. A blocking policy could trade waiting CPU use for latency, but
requires measurement and would not remove the dependent GPU work.<sup><a href="#ref-s053">S053</a></sup>

**WSL2 CUDA:** NVIDIA's historical performance analysis identifies short submissions and repeated
launch/completion as sensitive paths across the guest/host driver boundary. That makes our many
small operations a plausible sensitivity, not a measured WSL penalty. Its 2021 results do not
quantify this 2026 PC. A same-hardware native-Linux run is needed to assign an overhead.<sup><a href="#ref-s068">S068</a></sup>
CUDA 13.3 also documents restricted pinned memory and unsupported OpenGL/CUDA interop. Any pinned
staging or direct graphics-sharing proposal needs platform qualification; managed memory is not
a blanket replacement for explicit ownership.<sup><a href="#ref-s043">S043</a></sup>

**WSLg:** Microsoft documents a compositor/remoting path for Linux windows and describes a
system-memory presentation cost for its initial implementation. That is background, not a current
percentage for our machine.<sup><a href="#ref-s069">S069</a></sup> Windowed viewing can pay presentation and
desktop-sharing costs. Headless CUDA uses no window. Offline compilation uses `surface=None`,
renders offscreen and reads pixels itself; it does not present each frame through a Windows
window. WSL graphics translation/driver costs can still apply to its selected adapter, but
window piping cannot explain its whole delay. The earlier software-rendering slowdown was
measured separately and repaired; it must not be presumed to have returned.

## What should change in the investigation

First re-establish a complete same-source headless/compile timing boundary, with block-size
controls and actual graphics-adapter identity. Measure pipeline work omitted by current compile
timers. Obtain usable generated-code/resource evidence; prior counter access failed, so there
is no measured cache/occupancy diagnosis to cite as a pass.

Then plan two substantial comparisons: device-resident timestep ownership with reduced host
observations, and a neighbour-construction replacement with better cell indexing/locality.
Continue the bounded correction-arithmetic investigation alongside them. Assess complete runs,
early and evolved motion, enabled effects, memory, failures and dense cases. Keep controls and
use the [assessment policy](/docs/project/development/milestones/05/performance-assessment.md).

The numerical workload also needs a documented quality-versus-cost study. Eight iterations at
480 steps per simulated second are not equivalent to the original PBF paper's three-iteration
examples.<sup><a href="#ref-s004">S004</a></sup> Detailed CPU-compatible intermediate rounding and error order
are useful verification choices, but they should be examined deliberately when selecting a
production performance contract. A revision needs measured accuracy, stability and reproducibility;
neither fewer iterations nor weaker checking is automatically a satisfactory improvement.

The 100k real-time target has published precedent. This audit does not establish when Maelstrom
will reach it, or excuse its gap through WSL. It finds concrete work to remove and makes clear
that a series of isolated small edits is insufficient evidence of reaching the whole target.

## Verification and limits

This was source inspection and a read-only re-audit of retained primary-PC evidence. Source hashes
matched all 180 control files. The independent trace reader rechecked launch dimensions, operation
windows, 99,840 kernels, 24,481 completions and transfer counts; arithmetic in the audit receipt is
reproducible. No simulator code was changed and no fresh benchmark, Rust test suite, native
sanitiser, counter run or hosted check is claimed. Earlier verification remains identified by its
own record. No new memory-safety defect was established by this review; that is not a certification.
Both histories, branches, tags and the parent gitlink were preserved.

## References used

<a name="ref-s004"></a> **S004** — Macklin and Müller (2013), *Position Based Fluids*, §8 and Table 1.
[Source record](/docs/research/sources/004-macklin-muller-position-based-fluids.md).

<a name="ref-s043"></a> **S043** — NVIDIA, *CUDA on WSL User Guide*, 13.3, §§5.1–5.2.
[Source record](/docs/research/sources/043-nvidia-cuda-on-wsl.md).

<a name="ref-s053"></a> **S053** — NVIDIA, *CUDA Driver API*, 13.3, context management and scheduling flags.
[Source record](/docs/research/sources/053-nvidia-cuda-driver-api.md).

<a name="ref-s065"></a> **S065** — NVIDIA, *CUDA C++ Best Practices Guide*, 13.3, §§10–12.
[Source record](/docs/research/sources/065-nvidia-cuda-best-practices-13-3.md).

<a name="ref-s068"></a> **S068** — Boissel and Sundaram (2021), *Leveling up CUDA Performance on WSL2 with New Enhancements*.
[Source record](/docs/research/sources/068-nvidia-wsl-launch-performance.md).

<a name="ref-s069"></a> **S069** — Microsoft, *WSLg*, architecture and OpenGL acceleration documentation.
[Source record](/docs/research/sources/069-microsoft-wslg-architecture.md).
