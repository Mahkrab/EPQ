# Complete CUDA timestep critical path

**Retain tiled neighbour rows for inputs of at least 32,000 particles.** Adjacent
CUDA lanes read adjacent neighbour indices, while each particle retains its exact
identity-sorted row and ordered arithmetic. Compact rows remain the small-input
path. This is a useful structural improvement, but 110,592 particles remain below
real time. No numerical retuning or replacement fluid method was used.

The [evidence receipt](/docs/project/development/milestones/05/assets/timestep-critical-path-v1/README.md)
identifies source/binary/PTX versions, raw samples, prospective protocol, rejected
work, regression logs and independent readers. This is local, uncommitted work
against Maelstrom `6bf2682325b7665e48f8a8647ce087d48ff13f0b`; no Git boundary or
hosted verification is implied.

## Complete application comparison

Measurements use the primary RTX 4070/Ryzen 9 7900X PC through `ssh pc`, WSL2,
driver 610.88, CUDA 13.3.73, Rust 1.96.0 and hardware Mesa D3D12/OpenGL. Each run
opens a 1280×720 X11 window with the retained impostor renderer, energy colouring
and fitted camera. Experimental remains 240 Hz, eight Jacobi iterations,
correction 0.25 and relaxation 20. Each invocation computes all 1,200 accepted
steps, nominally five simulated seconds. One warm-up pair precedes three measured
alternating pairs at each size. Build, test, profiling and hash work do not overlap
ordinary samples. Startup and completed frames are outside running-frame rates;
complete launch-to-completion times remain in the raw results.

| Particles | Complete live solver ms/step, before → after | Viewer simulated s/wall s, before → after | Viewer change |
| ---: | ---: | ---: | ---: |
| 8,000 | 2.159708 → 2.182823 | 1.956585 → 1.934411 | -1.13% |
| 32,000 | 3.546143 → 3.273847 | 1.169292 → 1.272584 | +8.83% |
| 110,592 | 9.838930 → 8.029561 | 0.420063 → 0.511983 | +21.88% |

These are medians of three measured invocations per variant. Individual viewer
ratios at 110,592 are 1.2464×, 1.2321×, 1.1811×.
The full sample ranges, command times and frame tails remain in the
[reviewed comparison](/docs/project/development/milestones/05/assets/timestep-critical-path-v1/reviewed-comparison.json).

At 8,000 the reviewed median is 1.13% lower and two pairs are slower; this is a
small-scene cost rather than an established gain. The 32,000-particle threshold
is a conservative choice from the measured counts, not a universal crossover
for other hardware, scenes or formulations. Other modes receive correctness
qualification, not a new throughput claim.

The earlier size-selective implementation, before the final empty-row pointer
guard, independently measured 0.367770 → 0.446292 simulated s/wall s at 110,592,
with 11.208277 → 9.243820 ms complete solver calls. All three large pairs improved
(1.1962×, 1.2142×, 1.2305×). Its small result was 1.713568 → 1.705768 and middle
result 1.051136 → 1.118152. These are a separate measurement block, not extra
samples pooled into the reviewed implementation's medians.

The unchanged control binary itself speeds up materially between measurement
blocks. Therefore the improvement in absolute rates between blocks is **not**
credited to the pointer guard. Telemetry, every requested slow run and original
summaries remain retained. Realtime timestamps also adjusted during collection;
all solver, frame and command intervals use monotonic clocks. Neither the source
of machine variation nor physical desktop scan-out was established. Client-window
presentations do not prove compositor acknowledgements or input latency.

Separate headless alternating comparisons of the pre-review implementation gave:

| Particles | Complete solver ms/step, control → tiled | Complete CLI seconds, control → tiled |
| ---: | ---: | ---: |
| 8,000 | 1.930824 → 1.889229 | 2.617304 → 2.559858 |
| 32,000 | 3.192403 → 2.928457 | 4.195643 → 3.873048 |
| 110,592 | 8.403348 → 6.894212 | 10.702546 → 8.909075 |

These are total-only `run --unpaced --measure` timings with no checkpoint audits.
All final states and every accepted CFL diagnostic agree across all 24 headless
invocations. The headless/live difference supports continuing graphics/host
contention, but their different collection blocks do not isolate its exclusive
cost. No viewer FPS is inferred from headless timing.

## What is on the critical path

The complete path is host input validation, accelerated-velocity/CFL observation,
prediction/bounds observation, cell keys/sort/count/checked prefix/allocation/fill/
row sort, eight Jacobi/projection groups, reconstructed velocity/containment,
final vector readbacks, host materialisation/validation and accepted-state
publication. The worker then copies and publishes an immutable observation; the
viewer consumes the latest one on its own cadence. Rendering does not require a
queue of one presentation per physics step.

Full-motion traces cover all 1,200 steps, including evolved motion. They use
separately instrumented scoped CPU ranges and are not primary speedup samples.
Both diagnostic executables contain the expected source identity, and their PTX
matches the corresponding ordinary build. Earlier prefix and pre-review traces
remain separately retained. The reviewed full-motion attribution is:

| GPU work, ms/step | Compact control | Reviewed tiled rows |
| --- | ---: | ---: |
| Density and multipliers | 2.8574 | 1.3771 |
| Correction | 2.4837 | 1.8808 |
| Neighbour count + fill | 1.5476 | 1.6773 |
| Row identity sort | 0.1002 | 0.2819 |
| Spatial sort | 0.2366 | 0.2374 |
| Added tile prefix | 0 | 0.0661 |
| All solver GPU activity, including copies | 7.5176 | 5.8146 |
| Complete instrumented timestep | 11.0851 | 9.0232 |

All launches are assigned only after checking the complete per-step sequence
against the source: 69 → 70 at 110,592, with **21 stream waits unchanged**. The
added prefix and strided sorting cost real time; repeated numerical traversals
save more. Density/correction and evolved neighbour construction remain major
costs. The source establishes contiguous index access across lanes; no cache-hit,
bandwidth, stall or achieved-occupancy counter is claimed. The
[all-count components](/docs/project/development/milestones/05/assets/timestep-critical-path-v1/critical-path.md)
include 8,000/32,000-particle results and early/evolved windows.

Control/reviewed launch API costs are 0.282/0.290 ms per step;
portions without solver GPU activity are 0.232/0.205 ms. Stream waits occupy
8.708/6.941 ms inclusively, with only 1.418/1.403 ms outside recorded solver GPU
activity. Five D2H copies remain per step, carrying about 2.71 MB. Their actual
execution is about 0.12 ms, versus inclusive API costs of 0.563/0.527 ms. Those
inclusive API intervals must never be added to kernel time.

Host input/output validation measures 0.127/0.137 ms in the control and
0.129/0.138 ms in the reviewed trace. Materialisation is 0.826/0.644 ms;
accepted-state publication, including old-snapshot disposal, is 0.183/0.093 ms.
Separate worker observation publication is 0.535/0.368 ms after solver return.
These host functions are unchanged: their variation is not an independent
algorithmic saving. Scoped costs include tracing effects and differ from ordinary
snapshot-copy measurements. The reader clips intervals and subtracts the union
of solver GPU activity before reporting idle portions. It does not claim
device-wide idleness or separate CPU descheduling from active driver waiting.

Whole-grid dependencies between density, correction and projection are real.
Current error priority and cancellation semantics require completed group
observations; the host also needs CFL, bounds, an allocation total and its accepted
snapshot. These are obligations of the existing interface, not proof that every
present host round trip is physically unavoidable. Removing launches or waits
would neither preserve those obligations nor remove the remaining
5.815 ms of device activity above a 4.167 ms real-time budget. Earlier
residency/fusion work supplied no new reason to repeat those prototypes.

## Storage and ownership decision

The selected layout pads each group of 32 rows to its longest member, stores
successive members at stride 32, and preserves original CSR offsets as logical
lengths. One integer kernel calculates physical tile offsets after the checked
CSR prefix. It reuses the completed cell sort's scratch half. Count/fill share the
same geometry, sorting retains its cooperative networks and unrestricted dense
fallback, and all readers retain exact neighbour order and self insertion.
There is no neighbour cap, floating-point tree sum, new per-step allocation type,
new cancellation boundary or change to accepted/working vector ownership.

The physical allocation total still passes checked byte/capacity conversion and
geometric reservation. An empty row never forms a padded lane pointer, including
empty final tiles and the zero-allocation case. Private Rust/CUDA settings grow
from 96 to 104 bytes; both layouts are checked and compiled together.

Across the experimental trajectory, tile padding averages 21.50% at 32,000 and
15.64% at 110,592. Peak reserved neighbour storage changes 5,066,352 → 8,366,400
bytes and 26,972,280 → 28,785,024 bytes respectively. These are row allocations,
not whole-context memory. Small inputs retain the same 1,233,072-byte peak.
In pathological identity/degree distributions padding can approach 32× compact
storage; the measured scenes do not prove unchanged maximum capacity. Exhaustion
retains the existing recoverable allocation error and accepted-state rollback.

## Qualification and assessment

The reviewed source passed **356 ordinary tests** with **67 opt-in tests ignored**,
then **39 explicitly enabled CUDA unit tests**. The added cases check exact tiled
rows and padding against independent brute-force lengths/intermediates, dense
fallbacks, support changes, invalid-count rejection before scratch reuse, all four
block sizes, empty rows without allocation, and every cancellation boundary with
retry from the accepted state. Strict all-target CUDA/viewer Clippy and formatting
passed on this reviewed tree.

Nineteen source-identified trajectory pairs cover **7,440 accepted timesteps per
build**, plus initial states, with exact position/velocity/identity digests and
per-step CFL records. Experimental runs compute all 1,200 steps at each required
count. Reference, fast, paper-baseline and scene modes each compute 240 steps per
count; experimental/reference effects cases additionally cover 32,000 and 110,592
with XSPH 0.01 and vorticity 0.1. Every reviewed witness also matches its pre-review
control witness. Two recorded-input reruns recompute 1,200 steps at 32,000/110,592
and exactly match the saved final states and complete diagnostic records.

The reviewed impostor harness produces **27 exact hardware pixel/state matches**
against control, across all three counts, steps 0/240/1,200 and three cameras.
This checks the actual impostor shader with identical accepted states; it is an
offscreen hardware view comparison, not a scan-out witness. Compute Sanitizer
memcheck reports **zero errors** both for the empty-row test across block/tail
cases and for 16 complete 32,000-particle timesteps.

The earlier qualified build passed 356 ordinary tests with 66 opt-in tests ignored,
38 explicit CUDA unit tests, 24 CUDA/application/device integration tests and 12
viewer model tests. These groups overlap the ordinary suite. Native injected-driver
checks passed ASan/UBSan, including the extra prefix submission, draining,
completion/binding failure and poisoned-resource rejection. Strict all-target
CUDA/viewer Clippy and formatting passed. Nineteen parent reader/viewer checks
include negative controls for double-counted waits, wrong launch attribution,
stale executable identities and changed timing summaries.

The diagnostic-control build initially reused a stale shared Cargo artefact. Its
source-digest mismatch was caught, the captures were excluded and retained, and
the control was rebuilt before recapture. Ordinary binaries all matched their
expected source digests. Other retained preflight failures were an unsupported
u8 transfer in a new test and an incorrect viewer integration target; corrected
runs passed without changing numerical assertions. No failed sample was removed.

| Material change | Decision | Assessment |
| --- | --- | --- |
| Eight lanes per correction row | **REJECT** | Exact component checks passed, but the priority-size median viewer gain was only 1.8%; a middle-size pair regressed. Extra kernel, shuffles and maintenance do not earn retention here. |
| Tiled rows at every size | **REJECT as a universal policy** | Middle/large runs benefit; small inputs pay construction/traversal costs. |
| Tiled rows from 32,000 particles | **RETAIN** | Repeated complete viewer gains at both larger sizes, exact state/diagnostic agreement, bounded implementation and explicit memory trade-off. |
| Empty-row pointer guard | **RETAIN** | Avoids forming an out-of-allocation pointer when a row contains no members; explicit empty/tail/zero-allocation checks and reviewed-source measurements cover it. |
| Scoped trace and independent readers | **RETAIN as tools** | Diagnostic exports stay separate from production and reject stale identities and misleading additive timing claims. |

At 110,592 the reviewed build advances **0.5120 simulated seconds per wall
second**, requiring another **1.95×** complete viewer throughput to reach
real time. Its complete live solver takes **8.030 ms** against **4.167 ms**,
a gap of **3.863 ms per step** before observation costs. This remains
far from real time, so no 20-simulated-second/every-one-second qualification was
claimed. The five-second comparisons establish a useful throughput gain, not a
new sustained particle-capacity limit. Remaining numerical traversals and neighbour
construction, together with host observations/submission and graphics contention,
still need substantial improvement to meet the primary target.

No clocks, power policy, driver, installed CLI, ordinary PC checkout, branch,
commit, tag, remote or parent gitlink was changed. The ten retained CUDA
optimisations, impostor renderer, numerical presets, replay and observation
contracts remain. No new CFD/quality investigation, hardware-loss recovery,
other-platform performance or hosted validation is claimed.
