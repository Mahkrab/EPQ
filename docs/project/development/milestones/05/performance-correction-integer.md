# CUDA position-correction integer quartic assessment

**Retain.** Reconstructing the retained quartic guard with integer products reduced
large-workload position-correction GPU time by 18.51% and complete-solver median time
by 4.26%. The 8,000-particle median improved by 2.88%, with one slower pair and a
wide control range. The change adds no allocation, launch, host transfer or register
requirement. Its extra bit manipulation is justified by exhaustive equivalence checks
and the consistent large-workload saving, within the measured platform and workloads.

The [evidence](/docs/project/development/milestones/05/assets/correction-integer-v1/README.md)
retains the [prospective protocol](/docs/project/development/milestones/05/assets/correction-integer-v1/protocol.md),
source identities/deltas, raw samples, profiles, negative controls and independent
readers. Control exactly matches the retained 189-file
[active-distance candidate](/docs/project/development/milestones/05/performance-active-distance.md),
including its uncommitted density/validation work. Candidate also has 189 files;
only `native/power.cuh`, its exhaustive native test and CUDA documentation change.
Both are reconstructible from Maelstrom `1e0085926d05c42949bb76b55d177d42a1f8f94f`
and recorded patches. EPQ remains at `1f76097a218266822cdf344c38db75ed128628a8`.
Previous work is preserved; no Git history, branch, tag, remote or gitlink changed.

## Fresh diagnosis

Before implementation, ordinary-control warm-ups and full 480-step profiles measured
correction at 0.289883 GPU ms per small step and 1.880707 ms per large step, summed
across eight iterations. Source inspection suggested repeated geometry and invariant
kernel coefficients. Generated PTX showed one square root in the correction loop:
the compiler already shared the repeated roots. Radius products and the owner
position were outside the loop, while coefficient, distance-scale and pressure-ratio
divisions remained inside. This is PTX evidence before driver lowering, not a dynamic
instruction count or proof of a hardware bandwidth bottleneck.

Three private diagnostic exports inserted a probe before original correction. Each
visited the same rows, stored observable sums/errors in finished scratch, then ran the
original correction and diagnostics. Large-step GPU probe intervals were:

| Probe | GPU ms/step across eight iterations |
| --- | ---: |
| Geometry/traversal and checked sum | 1.018411 |
| Also Spiky and Poly6 | 1.062752 |
| Also artificial pressure | 1.852321 |

Original correction after those probes took 1.8950, 1.8875 and 1.8704 ms respectively.
All six diagnostic warm-up/profile outputs matched ordinary control exactly. Every
probe used the same 52-register solver requirement, but added eight launches per step
and changed cache/scheduling conditions. Their differences are indicative attribution,
not additive production costs or complete-solver speedups. They identified pressure
as the largest removable arithmetic increment; traversal/geometry remained substantial.
No hardware cache, bandwidth or achieved-occupancy counters were collected.

The retained pressure fast path still evaluated two binary64 products for its quartic
and midpoint guard. An exact integer replacement was tried first. Both exploratory
large pairs improved (2.85% and 4.98%); the two small pairs were mixed (-1.17% and
+1.54%). Those twelve records remain separate from final measurements. No second
candidate or speculative neighbour-layout redesign was needed.

## Exact substitution

The [implementation argument](/docs/project/development/milestones/05/assets/correction-integer-v1/integer-quartic-proof.md)
derives the accepted input range and both rounding stages. A binary32 input's 24-bit
significand squares exactly into 48 bits. Squaring that integer produces a 96-bit
product, retained through its low/high halves. Integer ties-to-even rounding recreates
the original 53-bit binary64 significand, then the same binary32 result and midpoint
guard. The input/output endpoint tests and strict guard threshold remain equivalent.

This preserves the old guard's acceptance set as well as its accepted values. Rejected
inputs and other exponents still use the unchanged approximation; this does not replace
it with the mathematical fourth power. The current correction loop, ratio division,
pressure multiplication, neighbour traversal and ordered vector accumulation are
unchanged. Identical shaped-value bits preserve finite/non-finite checks and error
priority. No stage, diagnostic, cancellation, publication, rollback, buffer lifetime or
thread-ownership boundary changes. No per-neighbour cache or fixed capacity is added.

## Final measurements

The primary PC used a Ryzen 9 7900X, RTX 4070, driver 610.88, CUDA 13.3.73,
GCC 13.3 and Rust 1.96.0. Separate precise `compute_89` release builds used locked,
offline dependencies. Fresh PTX was found inside each executable; source hashes were
checked before and after collection. The exploratory and final production PTX also
matched, while final tests/documentation were frozen independently.

Every request started a new CUDA0/block128 simulation with refinement four, eight
iterations, 480 unpaced steps and no graphics. Each primary workload had one warm-up
pair followed by five alternating pairs, first measured candidate/control. The small
scene retained checkpoints 0,1,120,240,480; the counted 48-cubed scene had none.
Effects enabled XSPH 0.01 and confinement 0.1. No sample was replaced or pooled with
exploration or earlier campaigns. Own task audits/probes ran outside timed collection;
clock locking, affinity and exclusive-machine isolation were not qualified.

Completed-step clocks include preparation, validation, transfers, launches, completion,
cancellation and acceptance. Construction, teardown, output, storage and correctness
audits are separate. These are descriptive medians, not a significance test.

| Workload | Control (s/480 steps) | Candidate | Less solver time | Speedup |
| --- | ---: | ---: | ---: | ---: |
| 8,000 | 1.154039 | 1.120780 | 2.88% | 1.030x |
| 110,592 | 3.789553 | 3.628116 | 4.26% | 1.044x |
| 110,592 with effects | 4.158197 | 4.030203 | 3.08% | 1.032x |

Small paired reductions were 11.33%, 5.06%, 0.72%, 2.88% and **-2.52%**.
The slower candidate took 1.145436 s against 1.117273 s. Controls ranged from
1.110935 to 1.291573 s; no cause is assigned to that spread or the slow pair.
Large paired savings were 2.21–4.75%, and effects savings 1.89–4.23%, with all ten
improving. Individual samples/order and construction/teardown clocks remain available.

Separate ordinary-binary profiles covered complete trajectories. The following values
sum GPU intervals across eight iterations per step, excluding host gaps; they are not
primary medians or isolated synthetic-kernel measurements.

| GPU stage (ms/step) | 8,000 control | Candidate | 110,592 control | Candidate |
| --- | ---: | ---: | ---: | ---: |
| Validation/density/lambda | 0.260401 | 0.254481 | 1.793492 | 1.804956 |
| Publication | 0.011306 | 0.011064 | 0.023824 | 0.023996 |
| **Position correction** | **0.303689** | **0.292251** | **1.874922** | **1.527869** |
| Physical-density check | 0.011960 | 0.011687 | 0.021024 | 0.021138 |
| Candidate position | 0.010987 | 0.010735 | 0.025972 | 0.026087 |
| Projection | 0.015922 | 0.015589 | 0.035186 | 0.035380 |
| **All numerical iterations** | **0.614265** | **0.595807** | **3.774420** | **3.439426** |

Correction saved 3.77% and 18.51% (1.039x and 1.227x); all numerical stages saved
3.00% and 8.88%. Large correction improved early (steps 1–120: 1.544384→1.110659 ms)
and late (241–480: 1.998342→1.786294 ms). Per-iteration data is in the audit. Small
unchanged stages also ran about 2% faster in these single captures, so the small
correction interval cannot wholly isolate the integer path. Several large unchanged
stages regressed slightly, including density/lambda (+0.011464 ms); no hardware-counter
or repeated-profile evidence establishes their cause or uncertainty.

Solver resources remain 52 registers per thread with zero reported local/shared bytes;
other functions' attributes match. Allocated capacities and host movement are unchanged.
Traces reconstruct 48 numerical launches per step, 65/69 complete-step launches,
21 explicit waits, 26 downloads and zero steady uploads. Steady bytes remain
196,480/2,709,952 per step; three initial uploads are separate. The trade-off is more
integer code and two explicit rounding stages, rather than additional memory. Other
exponents retain their implementation but have no new performance qualification.

## Validation and decision limits

All 50 final regression/warm-up/measured physical/configuration outputs and ordered
diagnostics matched control exactly, excluding only timings/build revision. Seven
regression sizes covered 64–8,000 particles. All four final profile outputs, four
initial records, six diagnostic records and twelve exploratory records also matched
within their respective workload groups. This qualifies recorded observations and
diagnostics, not independent fluid quality or every unobserved intermediate state.

The native test compares all 2,147,483,648 non-negative words with the original
approximation and an independent retained binary64 guard, at blocks 32/64/128/256.
Candidate and correctly selected retained-header builds reported zero result/guard
mismatches, 529,216,975 accepted words and the unchanged 354,191 raw-quartic negative
controls. Negative words cannot enter the new unsigned interval; other exponents
follow the unchanged branch. Existing CPU intermediate-bit oracles also passed.

PC verification passed 292 ordinary release tests (37 intentionally ignored),
31 explicit CUDA library tests, two boundary tests, seven execution tests, strict
Clippy, formatting and native ASan/UBSan. Local CPU feature isolation passed 290 tests
with invalid CUDA/toolchain settings. Cancellation, rollback/retry, diagnostic priority,
fixed membership, support boundaries and alternate exponent tests remain intact.

An initial control-labelled native test selected the candidate's local quoted header
before its `-I` path. Those commands are retained but excluded as control evidence.
The corrected overlay lives outside both source directories, checks dependency output
for the intended header and reruns both variants at all four blocks. No production
change or timing replacement followed that test-harness correction.

Compute Sanitizer exited 97 with sixteen WDDM debugger/device-support errors despite
two passing functional tests. This is **not** a device-memory pass; racecheck was not
run. Other GPUs/compilers, block-size performance, actual device loss and worst-case
cancellation latency remain unqualified. Primary gains do not establish statistical
significance or the instruction-level mechanism on other hardware.

Under the [assessment policy](/docs/project/development/milestones/05/performance-assessment.md),
the exact exhaustive result, unchanged surrounding solver and resources, consistent
large-workload gain and focused source delta justify retention. Small-workload noise,
one regression, unchanged-stage timing shifts and unavailable diagnostics remain
explicit limits. Geometry/traversal and the rare pressure fallback remain costs;
they were not removed or approximated to obtain these savings.
