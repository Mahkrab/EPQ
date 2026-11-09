# GPU particle rendering

**Retain analytic sphere impostors as the live default.** At 110,592 particles on
the primary RTX 4070 PC, matched hardware viewer runs improved simulation advancement
from **0.3096 to 0.4729 simulated seconds per wall second**, a **52.7%** increase.
Separate timestamp profiles reduced the GPU draw interval from **5.9775 to 0.1695 ms**
per frame, **97.2%**. Every large-scene pair improved. Indexed spheres remain
selectable and provide the automatic fallback for difficult clipping/precision cases.

The initial campaign qualified **38,400 particles**, 9.09% above the previous
verified 35,200. A later session on the same PC was slower for both renderers:
**28,800** is the highest count verified under those resumed-session conditions.
The rendering gain replicated, but 38,400 is not a current guaranteed capacity.
The renderer does not make 110,592 real-time physics.
Client-window presentation remains approximately 62.4/s; physical desktop FPS and
native input latency remain unqualified. None of these rates are interchangeable.

## Matched hardware comparison

The [prospective protocol](/docs/project/development/milestones/05/assets/particle-rendering-v1/protocol.md)
uses the previous 1280×720 scenes, fitted camera, energy colours and hardware
OpenGL/D3D12 X11 window. The PC has a Ryzen 9 7900X, RTX 4070, driver 610.88,
Mesa 25.2.8, CUDA 13.3.73 and Rust 1.96.0 under WSL2. All runs explicitly select
experimental: 240 Hz, eight Jacobi iterations, correction 0.25 and relaxation 20,
CUDA device 0/block 128. Simulation remains unpaced with unchanged observation and
render scheduling. Each candidate/count has one warm-up per variant and three
alternating pairs, computing all 1,200 steps. No build, test or other GPU experiment
overlapped the ordinary campaign. GPU timestamp/readback profiles are separate.

| Particles | GPU draw, ms/frame, indexed → impostor | Complete solver call, ms/step | Simulated s/wall s | Surface presentations/s | p95 / p99 interval, ms |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 8,000 | 0.3557 → 0.0298 | 1.828 → 1.812 | 2.3091 → 2.3316 | 62.781 → 62.751 | 16.819 / 17.072 → 16.872 / 17.095 |
| 32,000 | 1.5670 → 0.0607 | 3.273 → 3.062 | 1.2754 → 1.3619 | 62.554 → 62.571 | 16.545 / 16.825 → 16.589 / 16.791 |
| 110,592 | 5.9775 → 0.1695 | 13.361 → 8.732 | 0.3096 → 0.4729 | 62.335 → 62.391 | 17.244 / 17.580 → 16.693 / 16.965 |

These are medians, not significance tests. Large-scene paired physics ratios are
1.481×, 1.548× and 1.537×. The smaller gains are approximately 1.0% and 6.8%.
No measured ordinary interval exceeded 33.3 ms. The
[full tables](/docs/project/development/milestones/05/assets/particle-rendering-v1/results.md)
retain mean intervals, step rates, paired spread, CPU stages, clocks and memory.
Large-scene whole-device GPU activity fell from 83.8% to 76.5%, while solver
throughput rose; process CPU was 1.199 → 1.225 logical-core equivalents and GPU
memory 1,269.6 → 1,262.9 MiB. Those sampled activity/memory readings include the
desktop and are not exclusive process occupancy. The timestamp interval includes
clear, particles, lines and overlay, including any GPU preemption; it is not a
counter-derived exclusive particle cost.

After session resumption, default smoke tests with the **identical final executable**
were 20–25% slower. A separate bounded comparison tested whether the retained gain
survived: one diagnostic pair at each smaller count and three alternating large
pairs. Large-scene medians were **0.2423 → 0.3842**, a **58.6%** physics improvement,
with every pair positive. GPU clocks were similar, but whole-device graphics memory
was approximately 2.6 GiB rather than 1.2 GiB. The exact cause of the changed absolute
performance remains unverified. Neither campaign replaces the other. The
[post-resume tables and capacity traces](/docs/project/development/milestones/05/assets/particle-rendering-v1/post-resume/README.md)
retain this material uncertainty; no system changes were made to recover a faster result.

## Representation decision

| Representation | Geometry per particle | Large-scene GPU draw | Large-scene physics gain against its paired control | Assessment |
| --- | ---: | ---: | ---: | --- |
| Indexed control | 384 triangles | approximately 5.98 ms | control | Preserve for comparison, export and fallback |
| Low sphere | 96 triangles | 2.137 ms | 34.9% | Useful improvement, but more visible facets under zoom |
| Analytic impostor | 2 triangles | 0.170 ms | 52.7% | Retain as live default |
| Adaptive mesh | 96 / 192 / 384 triangles | 3.275 ms | 25.3% | Retain explicit comparison; additional selection work does not justify default |

The impostor bounds each exact perspective sphere silhouette with a rectangle.
Fragments reconstruct the nearest ray/sphere intersection, surface depth and
the existing world-space Lambert lighting. Spheres remain opaque with depth writes;
there is no blending or surface reconstruction. At 110,592 the submitted particle
triangles fall from 42,467,328 to 221,184. Extra fragment arithmetic, silhouette
discard and overlapping rectangles are real costs, but did not offset the gain in
these densely overlapping scenes. No hardware-counter claim about early depth,
bandwidth or occupancy is supported.

All representations share the original 16-byte instance layout, accepted-state
conversion, colour calculation, ordering and uploads. Immutable meshes and pipelines
are created once per device. The extra mesh/index payload is only a few KiB; no
new dependency or CUDA/wgpu interoperability is needed. Adaptive selection scans
all projected radii without regrouping particles; the large scene selected 192
triangles and CPU preparation was approximately 2.23 ms/frame, versus 1.18 ms for
impostors. An individual-particle LOD hierarchy was unnecessary after the stronger,
simpler analytic result.

The 110,592-particle instance upload is still 1,769,472 bytes per frame. Rendering
uses one instanced particle draw in every mode, so the retained benefit does not
come from fewer particle draw calls or omitted buffer updates.

Near/eye-plane intersections use indexed geometry for the entire frame, preserving
views from inside a sphere. Ill-conditioned analytic coordinates also fall back.
The established indexed vertex calculations and triangle order are preserved.
Offline rendering retains indexed output; only live windows default to impostors.
Set `MAELSTROM_PARTICLE_RENDERER=indexed`, `low`, `impostor` or `adaptive` to compare.

## Visual and numerical evidence

The [local comparison gallery](/docs/project/development/milestones/05/assets/particle-rendering-v1/visuals/index.html)
contains a divider for 144 matched stills and labelled four-way animations at
[8,000](/docs/project/development/milestones/05/assets/particle-rendering-v1/visuals/8000-comparison.mp4),
[32,000](/docs/project/development/milestones/05/assets/particle-rendering-v1/visuals/32000-comparison.mp4) and
[110,592](/docs/project/development/milestones/05/assets/particle-rendering-v1/visuals/110592-comparison.mp4).
Animations sample identical accepted states every eight timesteps at 30 observations
per simulated second, including impact, dense overlap, orbit and zoom. They are
visual comparisons, not wall-clock FPS recordings. Stills additionally cover a
settled five-second state and close views. These scenes do not establish every
possible thin sheet or fine-spray appearance.

Impostors retain rounded silhouettes and plausible shading/occlusion in the inspected
views; low meshes show more faceting at close range. Impostors are not pixel-equivalent:
median changed image pixels are 2.15%, 4.02% and 6.30% at the three counts;
foreground RGB root-mean-square error is 5.88, 5.74 and 5.68 out of 255. Edge changes
can reach 255 in an individual channel. The
[visual metrics](/docs/project/development/milestones/05/assets/particle-rendering-v1/visuals/comparison.json)
include every still and the gallery exposes close comparisons. Adaptive LOD can
change mesh at its thresholds; no temporal hysteresis or universal flicker guarantee
is claimed for that comparison mode.

Independent f64 ray/depth tests cover overlap, off-axis silhouettes, near clipping
and inside-sphere fallback on hardware GL and explicit software Vulkan. Eighteen
matched legacy indexed pixel/state digests are exactly unchanged. Every representation
uses the same immutable accepted states; all native CUDA files and the embedded
218,499-byte PTX match the previous indexed implementation. Numerical configuration,
solver kernels, replay, cancellation and acceptance semantics are unchanged.

## Sustained capacity and remaining limit

Three runs per count compute 4,800 complete steps, nominally 20 simulated seconds.
An opt-in worker trace records every successful solver-return timestamp before the
observation copy, buffers in memory and writes after teardown. The independent
reader evaluates the step-count difference across all full one-second windows at
every discontinuity and its neighbours. This includes intervals between displayed
observations, without interpolation or skipped steps.

All three 38,400 runs pass: average factors 1.0607, 1.0638 and 1.0587, with minima
247, 247 and 248 steps in any second. At 40,000 the overall means exceed one, but
repeat two has only 237 steps (0.9875 simulated seconds) in its worst second and
fails. Thus 38,400 was the initial campaign's highest verified count, bracketed below 40,000 in
1,600-particle layers, not a universal exact maximum.

The resumed-session qualification repeated the previous 35,200 reference and then
lower lattice layers. All three 35,200 runs failed; 32,000 and 30,400 each failed one
interval despite means above one. **28,800 passed all three runs**, with average
factors 1.2024, 1.2158 and 1.1921 and worst-second counts 268, 273 and 266.
It is the current-session verified capacity, bracketed below 30,400. This material
environment sensitivity prevents claiming a universal capacity increase from the
earlier result. It does not erase the matched renderer benefit in either session.

At 110,592 the remaining 8.732 ms complete solver call still exceeds the 4.167 ms
timestep budget, and complete viewer throughput needs approximately 2.11× more
capacity. The previous no-render control reached only 0.547× real time. Rendering
contention was substantial and is now much smaller; CUDA timestep/host acceptance
work remains the principal limit. Further renderer complexity has little credible
room to close this gap. No numerical retuning or unrelated CUDA work was undertaken.
The resumed-session result of 0.3842× needs approximately 2.60× more throughput;
the earlier no-render control is not a new control for that changed machine state.

The [evidence receipt](/docs/project/development/milestones/05/assets/particle-rendering-v1/README.md)
owns source identities, reproduction, actual regression results and environment
limitations. This is a local retention assessment of uncommitted work, not a tagged
milestone or hosted verification.
