# CUDA entry-point specialisation

The published starting point was Maelstrom
[`4a9675b5f9e3b7aa90335f5a77bdb3e82093a1b5`](https://github.com/Mahkrab/Maelstrom/tree/4a9675b5f9e3b7aa90335f5a77bdb3e82093a1b5),
pinned by EPQ `e6c5795b982e0079b1bb8ef212fac47114cf5947`.
I tested whether dedicated CUDA entries could improve per-operation resource allocation
without changing the solver's work. The
[protocol](/docs/project/development/milestones/05/performance-kernel-specialisation-protocol.md) was recorded
before collection; its later diagnostic and targeted follow-ups are identified separately.

## Implementation and verification

The first candidate exported one named entry for each of the thirteen device operations.
Checked geometry and pass calculations were separated by responsibility, with one operation
registry supplying both device names and driver lookups. The original pass body was retained
byte-for-byte behind compile-time specialisation. The bridge selected the appropriate function;
host operation 13 still batched the original cell-sort launches.

Each candidate passed 18 explicitly enabled CUDA library tests, two hardware application-boundary
tests, strict CUDA Clippy and native ASan/UBSan checks on the primary PC. Native tests exercised
every function-lookup failure, partial-initialisation cleanup, operation mapping and existing
grouped failures. Seven bundled 64–8,000-particle trajectories agreed exactly with the control,
as did paired results, warning schedules and diagnostic traces. Larger-run CFL warnings remain.

Local verification passed 69 CPU/library checks, 47 CLI/export checks and strict viewer-enabled
Clippy; one existing graphics-dependent CLI check remained ignored. The parent tooling suite
passed 62 tests. Independent audits recompute raw timing totals, medians, physical JSON and
named-kernel component durations. These are local/PC checks, not hosted candidate verification.

## First result: lower registers did not mean faster execution

Driver-loaded function queries reported 12–43 registers per thread, compared with 46 for the
shared entry. All reported zero local and shared allocation. Function attributes describe resource
requirements, not achieved occupancy.<sup><a href="#ref-s053">S053</a></sup>

Both sizes used CUDA device 0, 128 lanes, 480 steps, refinement 4 and eight iterations on the
Ryzen 9 7900X/RTX 4070 PC. Each campaign had one warm-up per variant and five alternating pairs.
The small workload retained checkpoints 0/1/120/240/480; the 110,592-particle workload omitted audits.

| Candidate | Particles | Control median | Candidate median | Candidate change |
| --- | ---: | ---: | ---: | ---: |
| All operations specialised | 8,000 | 1.713 s | 1.822 s | 6.4% slower |
| All operations specialised | 110,592 | 10.085 s | 10.124 s | 0.38% slower |
| Numerical passes specialised; search shared | 8,000 | 1.720 s | 1.710 s | 0.59% faster |
| Numerical passes specialised; search shared | 110,592 | 10.079 s | 10.109 s | 0.30% slower |

Every first-campaign pair was slower. Constructor and first-step measurements did not locate
the loss in one-time loading. A separately declared small trace instead found fill/sort device
time rising from 0.126 to 0.225 s, accounting for most of the added device work. Idle gaps were
almost unchanged. Several numerical passes improved slightly. This justified a targeted follow-up,
rather than treating register usage or the first median as the decision.

## Targeted follow-up and assessment

The follow-up kept keys, cell sorting, counting and filling on the shared entry while retaining
dedicated numerical entries. It used the same calculations and a new source identity. Shared
function handles were resolved once and reused; native tests covered that aliasing and all eleven
lookups, including the probe. Fresh qualification, warm-ups, pairs and full-motion traces were
collected. The unchanged control executable was byte-identical across campaigns.

Four small pairs improved and one slowed. Four large pairs slowed and one improved slightly.
Invocation medians changed from 2.720 to 2.696 s at the smaller size and from 10.676 to 10.720 s
at the larger size. The large diagnostic window also increased, with no sustained saving in
the dominant multiplier/correction work. Launch, transfer and completion counts were unchanged.

My decision is **do not retain either candidate as a performance optimisation**. The targeted
version removed the substantial small-scene regression, but its modest, mixed trade-off did not
establish a useful benefit for the larger workload. The extra entry mapping and maintenance cost
therefore lack a measured payoff. This follows the
[engineering assessment policy](/docs/project/development/milestones/05/performance-assessment.md), not a minimum
percentage, range-overlap veto or an assumption that specialised kernels cannot help.

The hardware cause of the fill kernel's code-generation sensitivity remains unresolved. No new
hardware counters were obtained, and the traces are diagnostic observations rather than primary
timing samples. The later small-trace reader needed SQL-quoting and working-directory corrections;
its first trace was reused, and no primary sample was replaced.

The [evidence](/docs/project/development/assets/kernel-specialisation-v1/README.md) preserves both
patches against the published starting commit, exact source/executable identities, all samples
and separate assessments. Reconstruction matches every assessed source file. The production solver
was restored to that commit; the earlier graphics/playback repairs and custom scene were preserved.
The next implementation target is cooperative integer neighbour-row sorting, using the existing
attribution while preserving identity order and unrestricted row lengths.

## References used

<a name="ref-s053"></a> **S053** — NVIDIA, *CUDA Driver API*, CUDA 13.3, `cuFuncGetAttribute`.
[Source record](/docs/research/sources/053-nvidia-cuda-driver-api.md).
