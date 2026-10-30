# Reducing PBF numerical work

This is the historical experimental assessment. The subsequent authorised
[application integration and matched comparison](/docs/project/development/milestones/05/performance-fast-mode.md)
implements the 240 Hz × 8 selector and evaluates the overall practical trade-off,
with the 5% compression target explicitly excluded as an automatic product veto.
The measurements and experimental outcomes below are preserved.

**NO-GO for a practically accepted faster solver.** A selectable 240 Hz, eight-iteration control achieved **2.06× sustained throughput at 8,000 particles and 2.28× at 110,592**, but failed compression, volume and collision-energy screens. The less compressible 480 Hz, four-iteration control achieved **1.53× / 1.71×** and also failed practical acceptance. These remain explicit experimental controls; production defaults and all ten retained CUDA optimisations are unchanged. No new formulation or kernel optimisation was attempted.

## Reuse and independent scheduling controls

The [existing frontier](/docs/project/development/milestones/05/performance-frontier.md) already covered 120/8, 240/2, 240/4, 240/8 and 480/8 at correction 0.5 and relaxation 2, at both requested particle counts. Their ten trajectories and original clocks were reused. Only the seven missing combinations per size were collected. The [matrix CSV](/docs/project/development/milestones/05/assets/numerical-work-v1/matrix.csv) contains all 24 size/configuration rows, exact accepted steps and simulated durations, iterations, neighbour-entry visits, kernel counts, device execution times, solver clocks and quality measurements. Reused clocks are explicitly labelled.

Every matrix case held geometry, initial state, mass, rest density, support, gravity, artificial pressure, boundary projection, neighbour rebuilding and disabled velocity effects fixed. The invariant audit also matched the earlier campaign's resolved physical inputs. Each run used schema 2 and refinement one, with timestep and iterations independently overridden. Actual accepted steps were 120/240/480 for the one-second large screen and 240/480/960 for the two-second small screen. CFL warnings did **not** insert steps or cause hidden refinement.

The normal refinement transformation divides timestep by its factor and correction by the factor squared. Thus the established factor-four production control resolves to 480 Hz, correction 0.0625 and relaxation 20. The independent matrix deliberately pins correction 0.5 and relaxation 2 instead; it is not a physically invariant timestep-refinement sequence. With support 0.1 m, relaxation 2 corresponds to approximately 200 m⁻², versus production's 2,000 m⁻². Corrections also contribute to reconstructed velocity through division by timestep. These known dependencies were accounted for explicitly rather than treating a rate change as an otherwise equivalent physical trajectory.

The large-screen results below use wall seconds per simulated second. Kernel times come from separate fresh production CUDA traces; solver times are ordinary, unprofiled single-run clocks. An asterisk marks a reused solver clock. Tracing changes execution overhead and is not the speedup measurement.

| Hz | Iterations | Actual Jacobi iterations / simulated s | Solver s/s | Traced kernel s/s | Peak p95 compression | Minimum separation / spacing |
|---:|---:|---:|---:|---:|---:|---:|
| 120 | 2 | 240 | 0.425 | 0.304 | 95.37% | 0 |
| 120 | 3 | 360 | 0.472 | 0.348 | 60.52% | 0 |
| 120 | 4 | 480 | 0.529 | 0.391 | 40.63% | 0 |
| 120 | 8 | 960 | 0.781* | 0.603 | 24.47% | 0 |
| 240 | 2 | 480 | 0.815* | 0.558 | 25.22% | 0 |
| 240 | 3 | 720 | 0.919 | 0.656 | 18.20% | 0 |
| 240 | 4 | 960 | 1.088* | 0.753 | 15.55% | 0 |
| 240 | 8 | 1,920 | 1.550* | 1.173 | 9.77% | 0.538 |
| 480 | 2 | 960 | 1.630 | 1.095 | 10.25% | 0.440 |
| 480 | 3 | 1,440 | 1.830 | 1.301 | 6.18% | 0.527 |
| 480 | 4 | 1,920 | 2.077 | 1.506 | 5.11% | 0.546 |
| 480 | 8 | 3,840 | 3.107* | 2.333 | 3.77% | 0.622 |

The fastest cases obtain large workload reductions by sacrificing separation and compression. They were rejected, including cases that complete faster than real time. At fixed correction/regularisation, halving iterations removes half the Jacobi work but retains prediction, neighbour construction, checks, transfers and acceptance on every step. Halving step rate also removes half those per-step costs. This explains why the two 1,920-iteration schedules have different costs; the counters and traces establish the work, rather than an assumed linear speedup.

![Measured independent scheduling costs and compression.](/docs/project/development/milestones/05/assets/numerical-work-v1/workload-frontier.png)

## Sustained performance and quality

Measurements used the primary RTX 4070 PC, CUDA device 0 and block size 128, the pinned Maelstrom `250932784790ba26cdc55fc38a877ccefacbf054` executable, and the retained ordinary `Simulation` measurement harness. Each comparison ran for five simulated seconds with 60 Hz snapshot access, one warmup pair and **five alternating measured pairs**. Per-step host snapshot materialisation remains inside the solver calls. The cadence accesses those host snapshots; it does not render, encode or independently copy particle frames. Construction, teardown, JSON output and physical audits are excluded. No build, audit or other GPU workload ran alongside the paired measurements.

| Policy | 8,000 cost s/s, median [range] | Speedup | 110,592 cost s/s, median [range] | Speedup |
|---|---:|---:|---:|---:|
| Production control | 0.894 [0.887, 0.923] | 1 | 3.809 [3.805, 3.822] | 1 |
| 240 Hz × 8, correction 0.5, relaxation 2 | 0.434 [0.433, 0.441] | **2.06×** | 1.670 [1.664, 1.672] | **2.28×** |
| 480 Hz × 4, correction 0.5, relaxation 2 | 0.585 [0.579, 0.586] | **1.53×** | 2.227 [2.218, 2.241] | **1.71×** |

Each candidate has its own control series. The displayed production row is the half-rate comparison; the half-iteration controls have medians 0.893 and 3.805 s/s. No pair regressed. Large-scene paired speedups ranged 2.278–2.292× and 1.696–1.746× respectively. These are numerical-policy comparisons: correction and regularisation also differ from production. The fastest control advances **0.599 simulated seconds per wall second**, requiring another **1.67×** gain for real time even before physical qualification.

The practical screen retained the existing 5% p95 / 25% maximum compression budgets, separation ≥0.5 spacings, finite contained state without coincidences, ≤10% occupied-volume-proxy error and ≤10% excess mechanical energy. Hydrostatics, shear and convergence are reported separately below.

| Five-second large case | Peak p95 / maximum compression | Minimum separation / spacing | Peak occupied-volume-proxy error | CFL-warning steps |
|---|---:|---:|---:|---:|
| Production | 46.34% / 69.50% | 0.403 | 33.47% | 404 / 2,400 |
| 240 Hz × 8 | 9.77% / 21.74% | 0.538 | 21.42% | 288 / 1,200 |
| 480 Hz × 4 | 5.11% / 19.31% | 0.546 | 20.06% | 181 / 2,400 |

The reduced-work controls remained contained without coincidences in these trajectories, and improved compression relative to production. Neither passes the unchanged practical screen. At 8,000 particles their peak p95 compression was 5.27% / 5.35%; peak occupied-volume-proxy errors were 29.84% / 28.11%. The separate collision cases reached 6.94% / 7.54% compression and **18.51% / 56.73% excess mechanical energy**. The half-iteration free-surface case reached **127.52% excess energy**. Those failures independently reject practical adoption; the conclusion does not rest on the volume proxy or stricter hydrostatic/shear errors alone.

The occupied-volume diagnostic unions particle-sized cubes. It has representation bias and is not an exact free-surface reconstruction; its earlier resolution-sensitivity study was reused. Neither particle count nor mass was lost. Central slices show coherent falling, spreading and settling in the two controls, with persistent ordered particle patterns. Those pictures do not establish acceptable liquid dynamics or erase the measured contraction and collision failures.

![Same large-scene central particle slice at 0.25, 1 and 5 simulated seconds.](/docs/project/development/milestones/05/assets/numerical-work-v1/particle-slices.png)

Two bounded stronger-correction/lower-regularisation candidates, 240 Hz with four/eight iterations, correction 1 and relaxation 0.02, were implemented as isolated input overrides and rejected immediately. Large-scene p95 compression exceeded 13,600% / 39,600%, with coincidences and explosive energy. They were not extended or promoted.

Stricter errors remain visible: half-rate / half-iteration five-second tank-centroid errors were **24.61% / 16.78%**; unforced shear retained **0.768 / 0.664** of its initial mode at 0.2 s. The existing two-second timestep comparison changes the tank centroid by 12.67% between 240 and 480 Hz at eight iterations. These are not converged hydrostatic or shear solutions. No earlier mathematical diagnosis or spatial-consistency investigation was repeated or reclassified as passing.

## Counted work and adaptive stopping

The private replay counted prediction-neighbour entries on every step and matched production endpoints exactly. Each Jacobi iteration traverses two complete directed rows and the upper-identity suffix of another, giving 2.5 directed-entry visits per stored entry across symmetric rows. Self-density visits are recorded separately. Discovery candidate tests and row-sort comparisons are additional work, not included in that Jacobi-entry count. The unchanged production CUDA traces independently verified every launch count.

| Large five-second policy | Accepted steps | Actual Jacobi iterations | Neighbour entries / simulated s | Jacobi entry visits / simulated s | Kernel launches / simulated s |
|---|---:|---:|---:|---:|---:|
| Production | 2,400 | 19,200 | 1.871 billion | 37.424 billion | 33,120 |
| Half-rate | 1,200 | 9,600 | 0.852 billion | 17.037 billion | 16,560 |
| Half-iterations | 2,400 | 9,600 | 1.692 billion | 16.922 billion | 21,600 |

Thus both controls halve scheduled Jacobi iterations and eliminate about **54.5% of actual Jacobi-entry visits** relative to production. Evolving neighbour counts account for the difference from exactly 50%. Their measured solver speedups remain distinct from those workload reductions.

A bounded residual probe inspected all iterations of the unchanged five-second 480 Hz/eight-iteration trajectories. Its prospective rule allowed stopping after two applied iterations when p95 positive constraint ≤3%, maximum ≤15%, and optionally maximum remaining correction ≤0.0005 m, or 1% of spacing. Density alone suggested mean counts 2.03 / 2.17 at small/large size. Adding the displacement safeguard gave **2.20 / 7.38**. At large size it retained all eight iterations on 2,139 of 2,400 steps and offered only **7.8% iteration removal** before checking overhead. Even assuming all solver time scaled with iterations gives only an optimistic 1.085× opportunity on that trajectory.

These are oracle estimates on fully iterated trajectories, not an adaptive implementation, changed trajectory or measured speedup. The residual is also evaluated on the frozen prediction list, unlike the independent quality audit's current neighbours. A density-only stop would discard large remaining corrections; its apparent saving was not promoted as safe unused work. The safeguarded rule cannot plausibly deliver the requested gain, so no adaptive branch was developed.

CFL-only bins on the same large trajectory would allow 120 Hz at 1,805 of 2,400 sampled instants, 240 at 165 and 480 at 273; 157 required finer steps. This is not a stability-controlled simulation. The actual coarse-step tests show why a velocity bound alone cannot admit density relaxation or volume behaviour. Changing timestep would also need an explicit correction-scaling policy and fresh trajectory qualification.

## Implementation and decision

The [selectable controls](/Maelstrom/experiments/numerical-work/README.md) run through the existing solver API. They preserve its errors, cancellation and atomic acceptance because no production solver code was changed. All 13 production native files matched the measured source. Existing test relocation, investigations and both Git histories were preserved. No system settings, defaults, gitlink or history were changed.

**Retain the controls and evidence for reproduction; do not adopt either policy for practical fluid simulation.** The fastest measured trade-off meets the 2× throughput target while violating compression and collision/volume budgets. The closer density result misses 2× and still fails cross-scene quality. The specific limit is the pressure response and physical behaviour retained with fewer steps/iterations, not an unmeasured CUDA arithmetic opportunity. This bounded task ends with NO-GO; it does not initiate another formulation or optimisation investigation.

Fifteen deterministic Python/oracle/retention tests passed locally. All 25 fresh production/native trajectory endpoints, 30 work-counter replays, 24 production traces, two residual probes and 48 sustained/warmup endpoints matched their corresponding controls. The three configuration files passed local CLI resolution checks. Production CUDA kernels and Rust solver logic were not modified; no new full Rust/CUDA regression suite, adaptive-policy qualification, renderer-cost benchmark or hosted verification was performed. Exact inputs, failures, individual timings, source identities, traces and observations are retained in the [evidence directory](/docs/project/development/milestones/05/assets/numerical-work-v1/README.md).
