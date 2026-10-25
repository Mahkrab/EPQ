# Performance comparator specification

This accompanies the [diagnosis protocol](/docs/project/development/milestones/05/performance-protocol.md).
Its purpose is to make the external comparison reproducible and the remaining differences visible,
not to turn a published particle count into a universal speedup ratio.

## Primary runnable comparator: SPlisHSPlasH PBF

Use revision `7586ffa25948c6ce3bc6c238cda30ad8d35f60a0`. The pinned
[method registration](https://github.com/InteractiveComputerGraphics/SPlisHSPlasH/blob/7586ffa25948c6ce3bc6c238cda30ad8d35f60a0/SPlisHSPlasH/Simulation.cpp#L249)
places PBF at `simulationMethod = 2`; the upstream double-dam-break scene selects DFSPH instead.
Its headless simulator accepts `--no-gui`, `--no-initial-pause` and `--stopAt`.
Verify the resolved method and number of steps from the actual run.<sup><a href="#ref-s060">S060</a></sup>

The proposed fixed-work request is:

| Setting | Declared value or required check |
| --- | --- |
| Machine | Same primary PC as Maelstrom; sequential, no overlapping benchmarks |
| Build | Release, single precision, OpenMP enabled; record compiler, AVX/performance options and dependency revisions |
| Solver | PBF, minimum and maximum iterations both eight; first-order velocity update |
| Timestep | Fixed resolved Maelstrom timestep after refinement by four; disable adaptive CFL selection |
| Particle geometry | Exact Cartesian counts and positions from `capacity-block-v1`; verify imported/generated count and initial-coordinate hashes before timing |
| Scale | Particle radius 0.025 m; verify support radius 0.1 m and observed neighbour counts |
| Kernel | Poly6 density and Spiky gradient where supported; record selected identifiers |
| Forces | Gravity [0, −9.81, 0]; zero initial velocity; optional viscosity, vorticity and surface tension disabled |
| Boundary | Static enclosing box with declared dimensions; record boundary sampling/density model and additional boundary-particle count |
| Work | 480 steps for the fixed-work diagnostic; retain the actual count and simulated endpoint rather than assuming a time-based stop executes exactly 480 |
| Output | No rendering, particle exports or per-frame console output in steady timing; report setup/output separately |

The inspected upstream registration maps Poly6 to kernel 2, Spiky to gradient 3 and no adaptive CFL
to mode 0; setting particle radius establishes support at four times that radius. The PBF loop
supports fixed work through equal minimum/maximum iterations. These source-level configuration
findings alone do not establish a successful launch or equivalent benchmark.<sup><a href="#ref-s060">S060</a></sup>
The subsequent [diagnosis](/docs/project/development/milestones/05/performance-diagnosis.md) records the actual
same-PC runs and the differences which remained.

Before a run is admitted, retain a complete effective request, exact point count/ordering, resolved
parameters, source/binary/build identities and timing boundaries. A block generator with different
spacing or inclusive endpoints fails admission even if the scene looks similar. Use a fresh output
directory. The upstream headless stop condition uses simulated time, so count steps explicitly.

## Differences which remain even after those settings match

| Difference | Consequence for interpretation |
| --- | --- |
| Density constraint | SPlisHSPlasH clamps under-density in its PBF constraint; Maelstrom's contract differs |
| Relaxation and artificial pressure | Match the mathematical policy only where it is genuinely equivalent; do not silently remove Maelstrom's stabilisation |
| Mass/volume normalisation | Record actual resolved particle volume/mass and rest-density conventions, not just the same density label |
| Boundary physics | Boundary-density coupling/sampling is not Maelstrom's centre-based plane projection |
| Arithmetic | Single precision alone does not establish equal rounding, reduction order, power approximation or SIMD behaviour |
| Execution | CPU PBF plus GPU search is not automatically a GPU-resident PBF solver |
| Timing | The upstream `SimStep` region is not automatically Maelstrom's complete transactional step boundary; map included work before calculating ratios |

The constraint, stopping and timing distinctions are visible in the pinned PBF and simulator
implementation.<sup><a href="#ref-s060">S060</a></sup> Treat the first run as an architectural/throughput
comparison with this mismatch table, not an exact physics control. Use the protocol's separately
declared density, stability, boundary and sustained-duration criteria for any later quality study.

## Other implementation lessons

CompactNSearch's pinned `PointSet.h` exposes per-point neighbour counts and neighbour vectors;
its documentation also offers optional spatial reordering. This provides a concrete alternative
to scanning every possible particle word, without implying that its CPU containers are the right
CUDA layout.<sup><a href="#ref-s061">S061</a></sup>

GPUSPH's developer explanation constructs neighbour indices after hashing, sorting and reordering.
Its CUDA iterator uses strided neighbour-list offsets. These are useful layout/traversal ideas,
not a licence to change Maelstrom's stable summation order or adopt unchecked neighbour caps.
The inspected iterator is GPL-3.0-or-later; no code is being copied into Maelstrom.<sup><a href="#ref-s062">S062</a></sup>

## References used

<a name="ref-s060"></a> **S060** — Bender and contributors, *SPlisHSPlasH*, pinned PBF, simulation registration, simulator and build files.
[Source record](/docs/research/sources/060-splishsplash-pbf-implementation.md).

<a name="ref-s061"></a> **S061** — Koschier and contributors, *CompactNSearch*, pinned README and `PointSet.h`.
[Source record](/docs/research/sources/061-compactnsearch.md).

<a name="ref-s062"></a> **S062** — GPUSPH developers, *GPUSPH*, pinned neighbour-construction documentation and CUDA iterator.
[Source record](/docs/research/sources/062-gpusph-cuda-fluid-solver.md).
