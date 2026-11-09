# Particle representation comparison protocol

Specified before candidate collection on 9 November 2026. Preserve the existing
uncommitted work and both repository histories. The previous indexed viewer is
the control; this investigation changes graphics representation only.

Use the previous exact 8,000/32,000/110,592 scene inputs, 1280×720 camera/colours,
experimental 240 Hz/eight iterations/correction 0.25/relaxation 20, CUDA ordinal 0
and block 128. All ordinary timing runs use the real hardware GL/D3D12 X11 window
on the primary RTX 4070 PC. No software performance samples or system changes.

Compare the indexed 384-triangle sphere, a 96-triangle sphere, analytic two-triangle
sphere impostors and a frame-wide adaptive mesh policy. Adaptive selection uses
the largest perspective-projected half-extent: 96 triangles at ≤3 pixels,
192 triangles at ≤6 pixels, otherwise the control. Preserve particle draw order;
do not sort, drop particles, reduce solver work or change observation frequency.
Near/eye-plane intersections retain indexed geometry. Analytic depth and lighting
must be independently checked before qualifying impostors.

Before timing, inspect matched stills at the three counts, accepted states and
camera distances. Render a three-second, 30 Hz sequence with matched accepted
states and camera motion for each representation/count. Label its video cadence
separately from viewer presentation measurements. Compare silhouettes, lighting,
depth/occlusion, dense overlap, splashes and zoomed particles. Retain failed
experiments and visual differences. Obvious persistent facets, depth faults,
holes or flicker disqualify a default even if it is faster.

For every candidate/count use one warm-up per variant followed by three
alternating control/candidate pairs (warm-up AB; measured BA/AB/BA), with 1,200
accepted steps and the existing 180 s ceiling. Retain all samples. Report medians,
ranges and paired effects; do not claim statistical significance. A clearly
unacceptable visual candidate may receive bounded diagnostic timings rather than
extended qualification. No build, GPU test, visual capture or trace overlaps
ordinary measured runs. Keep GPU timestamp query/readback builds separate.

Report GPU draw intervals, complete solver wall time, accepted-step and simulated
throughput, client presentations/s, mean/p95/p99 intervals, stutters, CPU/GPU
utilisation and memory. Physical desktop FPS and native input latency remain
unqualified unless independently established. Test fallback/indexed compatibility,
near clipping, off-axis projection, overlap/depth and resizing in proportion to risk.

Select the simplest visually credible renderer with a useful complete-viewer
benefit under the existing assessment policy. Keep indexed selection as a fallback.
Offscreen/export defaults and numerical/encoding/hashing paths retain their current
behaviour. Then qualify sustained capacity from the previous 35,200 reference,
using three 4,800-step runs per admitted count and every full one-second window.
Bracket in 1,600-particle lattice layers around a near-real-time pilot; a long-run
failure is retained, not silently discarded. Stop once the strongest credible
candidate and remaining large-scene limit have been established.


After comparing all candidates, analytic impostors had the strongest measured gain
and the best visual agreement among the cheaper representations. The qualified live
default is therefore impostor; indexed remains explicitly selectable and automatic
for near/eye-plane intersections or ill-conditioned analytic coordinates. Low and
adaptive meshes remain explicit comparison modes, not the default policy.
Capacity qualification repeats 35,200 for three 20-second runs, then uses 41,600 and
48,000 short pilots to choose a near-real-time bracket. Subsequent three-run,
20-second counts move in 1,600-particle layers until every-window passing and failing
counts are adjacent. Do not discard a failed interval because the overall mean passes.

For strict qualification, the coalesced frame trace is insufficient: add an opt-in
accepted-step timestamp buffer in the worker, before observation copying. Record step
zero after construction, retain all 4,800 completions and write only at teardown.
Evaluate all full sliding one-second windows at step-function discontinuities and
their neighbouring nanoseconds. Require the mean and every window to advance at
least one simulated second. This changes measurement precision, not solver work.

After resuming the session, the PC's `/tmp` experiment directory had disappeared.
The final binary survived with its exact hash; source and regression logs were restored
in an isolated cache directory. Default smoke runs were slower across all counts.
Preserve them separately, without replacing the original campaign. Test the specific
new hypothesis that the renderer's benefit persists under the changed machine state:
one indexed/impostor pair at 8,000/32,000 and three alternating large-scene pairs,
all 1,200 steps. Then reassess strict capacity with three 4,800-step repeats at
35,200 and 32,000; move by one 1,600-particle layer to 33,600 if 32,000 passes, or
30,400 if it fails. A further lower layer is admitted only if the same every-window
criterion fails again. Keep all failures and machine-state uncertainty visible.
