# Selectable fast numerical mode

**Retain the implemented fast mode as an explicit option; do not make it the universal default.** It provides a measured **2.27× large-scene solver speedup and 2.18× complete headless-command speedup**, improves compression and separation in the main falling-block workloads, and remained finite and contained without observed coincidences. However, it adds energy in collision and initially resting fluid, worsens unforced shear, and gives no sustained large-scene compilation benefit at matched 60 Hz output. The current default selection remains unchanged and the reference mode is an explicit fallback.

This decision weighs the complete practical trade-off. The earlier 5% compression screen is an experimental target, **not a product requirement or adoption veto**. Its historical outcome remains in the [numerical-work assessment](/docs/project/development/milestones/05/performance-numerical-work.md); it does not decide this integration.

## Application behaviour

`--numerical-mode fast` selects 240 Hz, eight Jacobi iterations, correction 0.5 and relaxation 2. `--numerical-mode reference` selects 480 Hz, eight iterations, correction 0.0625 and relaxation 20. Both work with run, view, compile, inspect and validate. The viewer also exposes an editable Numerics field and displays the selected generation's actual numerical values. [Usage and commands](/Maelstrom/docs/usage.md#numerical-modes).

Selection fills the command-line numerical layer before scene validation and solver construction. It preserves geometry, gravity, mass, support, boundaries, effects and other scene-owned inputs. Explicit `--set` values win. Presets reset inherited refinement to one; explicit refinement N still divides timestep by N and correction by N², without changing relaxation. Thus fast/refinement-two means 480 Hz, correction 0.125 and relaxation 2. A modified preset is a distinct resolved input.

CFL handling remains warning-only, with no inserted steps, hidden refinement or automatic mode switching. Errors, cancellation polls, rollback and accepted-buffer promotion use the existing solver code. Changing the viewer mode applies a fresh generation; it never mutates a running solver's configuration or resident accepted state. The entered step count remains fixed, so equal-duration comparisons require 1,200 fast versus 2,400 reference steps for five seconds. Recorded reruns use the saved resolved values rather than reapplying a preset. No production default, kernel, dependency, system setting or Git history changed.

## Matched method and identities

The primary device was the RTX 4070 PC, CUDA device 0, block 128, driver 610.88. The all-features release executable was built from an isolated export of the working Maelstrom source, based on `250932784790ba26cdc55fc38a877ccefacbf054`, including the pre-existing test relocation. Its source manifest, binary hash and implementation patch are retained. All 13 production native files remained byte-identical to the assessed baseline, preserving the ten retained CUDA optimisations.

Fresh application runs compared both modes on each of six unchanged scenes. Falling blocks at 8,000 and 110,592 particles, the 3,200-particle hydrostatic tank and spreading free surface, and the 3,456-particle collision ran for five simulated seconds. Unforced 8,000-particle shear ran for 0.2 s. All twelve resolved inputs and endpoints exactly matched their corresponding validated experimental trajectories. No parameter search was repeated. Each fresh run also had an exact native recorder replay and an independent binary64/current-neighbour audit, sampled at the established cadence.

Only **within-scene** reference/fast comparisons are claimed. The two falling-block sizes have different geometries; their clocks are not a pure particle-count scaling result. Physical inputs, output cadence and camera were held fixed within each pair. Both effects were disabled for these performance/quality workloads. Enabled-effect arithmetic and cancellation were covered by regression tests, but their fast-mode sustained quality/performance was not measured.

## Sustained application throughput

Headless timings used one warmup and five alternating measured pairs per scene. Solver totals include all coordinated stepping and accepted host-state installation. Complete CLI wall time additionally includes process startup, parsing, scene construction, device acquisition, JSON output and teardown. Compression of retained JSON and independent audits ran outside that timer.

Compilation used one warmup and three alternating measured pairs per scene, five seconds of simulation, hardware graphics, 640×480 PNGs and **301 frames per run**. Strides eight/reference and four/fast preserve 60 Hz simulated observation times; reduced image count is not counted as a numerical speedup. Compilation includes graphics/readback, snapshot hashing, PNG encoding, publication, progress and catalogue work. Graphics used Mesa GL's `D3D12 (NVIDIA GeForce RTX 4070)` adapter, without software fallback. No builds, tests, audits or other campaign GPU jobs ran concurrently with admitted timing pairs.

| Workload and boundary | Reference median wall s / simulated s | Fast median wall s / simulated s | Ratio of medians |
|---|---:|---:|---:|
| 8,000: solver calls | 0.900 | 0.435 | **2.068×** |
| 8,000: complete headless CLI | 0.969 | 0.498 | **1.947×** |
| 8,000: complete 60 Hz compilation | 3.419 | 2.361 | **1.448×** |
| 110,592: solver calls | 3.827 | 1.684 | **2.272×** |
| 110,592: complete headless CLI | 3.956 | 1.815 | **2.179×** |
| 110,592: complete 60 Hz compilation | 9.278 | 9.327 | **0.995×** |

Large-scene headless paired solver speedups ranged 2.251–2.282×; complete-command ratios ranged 2.167–2.194×. Every headless pair improved. Large compilation ratios were **0.955, 0.995 and 1.000×**, retaining all three slower samples. Small compilation ratios were 1.767, 1.435 and 1.355×, showing substantially more variability than headless timing. Every sample and range is in [the performance summary](/docs/project/development/milestones/05/assets/fast-mode-v1/performance-summary.json).

For the large five-second compilation, median solver intervals fell from 19.38 to 16.52 wall seconds, while graphics/readback rose from 3.05 to 6.48 s. Frame hashing remained about 17.9 s and PNG encoding about 2.5–2.6 s. These coordinated intervals include packing, transfers, waits and scheduling effects; they do not identify a kernel or driver cause. Component medians need not sum to the median command total. The observations establish that the headless solver gain does not carry through this rendered-output workflow. Live viewer FPS and wall-clock simulation progress were not measured; compilation includes costs the live viewer does not pay.

![Measured solver, complete-command and compiled-output costs.](/docs/project/development/milestones/05/assets/fast-mode-v1/throughput.png)

## Physical improvements and regressions

Entries below are **reference → fast on the same scene and interval**. Compression and energy are peak sampled values. Volume is the existing occupied particle-support-union proxy, not an exact reconstructed fluid interface. Particle count and mass were unchanged. Energy excess is normalised by each scene's own initial mechanical energy; percentages in different rows are not equivalent absolute energy budgets.

| Scene | p95 compression | Maximum compression | Minimum separation / spacing | Occupied-volume-proxy error | Excess mechanical energy |
|---|---:|---:|---:|---:|---:|
| Falling block, 8,000 | 19.77% → **5.27%** | 42.08% → **14.95%** | 0.544 → **0.659** | 33.77% → **29.84%** | 0.24% → **5.85%** |
| Falling block, 110,592 | 46.34% → **9.77%** | 69.50% → **21.74%** | 0.403 → **0.538** | 33.47% → **21.42%** | 0.19% → **1.18%** |
| Hydrostatic tank | 11.61% → **6.18%** | 16.15% → **14.80%** | 0.722 → 0.721 | 30.08% → **28.95%** | 0.96% → **42.48%** |
| Collision | 11.50% → **6.94%** | 28.81% → **14.94%** | 0.577 → **0.671** | 36.27% → **29.93%** | 0.44% → **18.51%** |
| Spreading free surface | 10.29% → **6.19%** | 18.07% → **14.74%** | 0.711 → **0.721** | 43.70% → **27.43%** | 0.96% → **42.54%** |
| Unforced shear, 0.2 s | 3.07% → **5.28%** | 9.35% → **15.03%** | 0.742 → **0.721** | 11.89% → **17.02%** | 107.11% → **805.76%** |

Fast improves compression and the volume proxy in all five gravity-driven scenes, and improves separation in both falling blocks and the collision. It does not improve every observable: hydrostatic separation changes slightly downward; shear compression, separation and volume all worsen. No fresh trajectory produced non-finite state, observed coincidence or loss of containment. This is a useful stability result for these bounded cases, not a general guarantee of liquid accuracy.

Tank-centroid error against the mass/area hydrostatic reference improves **29.90% → 24.61%**, but both equilibria remain wrong. Retained unforced shear amplitude changes **1.050 → 0.768**, so fast damps the tested mode more strongly and injects substantially more unwanted mechanical energy. The earlier physical and convergence limitations remain; no formulation diagnosis was repeated or declared repaired.

CFL diagnostics also expose a trade-off. At 8,000 particles, warnings changed from **0/2,400 to 68/1,200** steps; at 110,592, from **404/2,400 to 288/1,200**. The large fast run has fewer warning steps but a higher warning fraction. Counts and denominators are both reported; no warning was suppressed or treated as automatic refinement.

Actual application frames show both modes falling, colliding, spreading and settling. Fast produces a more rounded/cohesive collision body, a pronounced wall sheet and central jet during the large impact, a persistent domed tank surface, and more visible shear-body deformation. These are qualitative observations from matched cameras and times, not physical validation from appearance. Both modes retain artificial cohesion and incorrect equilibrium behaviour.

![Matched large-scene application frames.](/docs/project/development/milestones/05/assets/fast-mode-v1/large-frames.png)

The evidence includes [collision](/docs/project/development/milestones/05/assets/fast-mode-v1/collision-comparison.gif), [tank](/docs/project/development/milestones/05/assets/fast-mode-v1/hydro-comparison.gif), [large impact](/docs/project/development/milestones/05/assets/fast-mode-v1/large-comparison.gif) and [shear](/docs/project/development/milestones/05/assets/fast-mode-v1/shear-comparison.gif) animations, plus contact sheets for every scene. Shear playback is approximately quarter speed; timestamps remain authoritative. All 24 compiled bundles and 5,148 encoded PNG hashes passed validation. Both modes had identical initial images and cameras; repeated same-mode image sequences were bit-identical.

## Verification and default recommendation

The primary PC's `cargo test --locked --release --all-features -- --include-ignored` passed **395 tests, zero failures, zero ignored**, including opt-in CUDA and hardware/software graphics checks. Coverage includes explicit preset equivalence, overrides, refinement scaling, exact numerical reruns, viewer draft resolution, and every cancellation poll/rollback/retry for both modes. Strict all-target/all-feature Clippy, formatting, native ASan/UBSan fault-injection checks and the exhaustive CUDA power test passed; the latter tested 2,147,483,648 input words with zero mismatches. The local CPU regression also passed, and the new CLI mode test passed separately.

The wider parent tooling run, using its declared NumPy/SciPy versions through `uv`, passed **244 of 245 tests**. One legacy coordination-profiler fixture fails because it expects a removed solver anchor. The same failure was reproduced against Maelstrom HEAD and the unchanged working solver; the test, overlay and solver files were byte-identical to their initial state. It was retained, not weakened or silently skipped. The first bare-Python attempt's missing SciPy errors are also retained separately from the managed rerun.

**GO for the selectable fast mode; keep the current default and explicit reference fallback.** The sustained headless gain and better bulk compression/separation justify retaining the option despite exceeding the historical 5% target. A universal default change is not justified by this evidence: low-excitation energy and shear regress, and the large rendered compilation workload gains nothing. This assessment uses the overall practical benefit and regressions, not a single threshold. Both policies retain known physical limitations; reference is a comparison/fallback, not a physical ground truth.

No installed executable, remote checkout, gitlink, branch, tag or commit was changed. The tested CUDA/viewer release binary and raw observations remain in the primary PC's durable `fast-mode-v1` root. [Evidence, source identities and reproduction](/docs/project/development/milestones/05/assets/fast-mode-v1/README.md).
