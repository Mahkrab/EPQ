# Live viewer performance

This separately requested application investigation preserves the experimental application
default: 240 Hz, eight Jacobi iterations, correction 0.25 and relaxation 20. No numerical,
native CUDA, compilation, encoding or hashing change is in scope. Work is uncommitted;
the starting Maelstrom HEAD is `c40fc627549ad34120a39a1103218192a2b4b6b4`, with the user's
default-selection changes already present. The PC checkout is older and is not the baseline.
Matched source copies are built separately there without changing either Git history.

## Protocol specified before comparison

Use the primary RTX 4070 PC through SSH and a real 1280×720 hardware OpenGL/D3D12
X11 window. The earlier native-window failure is not reproduced: the existing PC binary
opens successfully. No drivers, clocks, power policy or global display settings are changed.

The [inputs](/docs/project/development/milestones/05/assets/live-viewer-v1/) use 8,000
(20³), exactly 32,000 (40×40×20), and 110,592 (48³) particles, identical spacing,
effects and container, and a fitted, stationary camera. Each run starts paused, then
executes 1,200 accepted steps (nominally five simulated seconds). There is a 180 s
run ceiling. A pilot checks the environment and measurement boundary; one warm-up
and three alternating baseline/candidate pairs per size decide retention. No build,
test or GPU trace overlaps an ordinary measured sample. Every requested sample,
failure and slow run is retained. Report medians and individual pairs, without a
statistical-significance claim.

Presentation measurements use successful surface presentations in the actual window,
with mean and nearest-rank p95/p99 inter-presentation intervals. They are not physical
scan-out or compositor acknowledgements. Confirm actual window contents separately.
Simulation throughput uses accepted index and simulated-time differences over that
same running interval. Complete-command timings and stage instrumentation are separate.
CPU draw timings include driver waits and must not be labelled GPU execution time.
Detailed CUDA/graphics traces are explanatory, not ordinary performance samples.

The first candidate hypothesis is that replacing the 1,152-vertex-per-instance
non-indexed sphere with an indexed representation of exactly the same triangles
will reduce redundant vertex work. The camera, shader, mesh coordinates, triangle
order, colour, radius, particle count and accepted states must stay unchanged.
Pixel comparison must include overlapping particles, boundaries and camera changes.
Further candidates require a specific measured bottleneck and their own paired comparison.

### Native-input limitation and revised launch boundary

The first reference pilot used the external scene's saved reference schedule; it is
retained separately and excluded. All admitted runs explicitly select `experimental`.
The external-scene loader intentionally defaults to its scene policy, independently
of the application's built-in-scene default.

WSLg focus did not reliably deliver keyboard events. Raising the owned window made
core focus queries succeed, but later key attempts still did not reach winit. An
XTest diagnostic and an XInput focus diagnostic also failed. The Windows session
contained LogonUI and the X11 host frames were off the root display; whether the
physical desktop was visible could not be confirmed. No session was unlocked and
no system policy was changed.

Before collecting comparison samples, the protocol was revised to launch running,
then send the owned window's `WM_DELETE_WINDOW` after the fixed step target completed.
This close path works without focus and preserves cooperative worker shutdown and
trace publication. Running-frame statistics exclude setup and terminal frames;
the first accepted index differs slightly between invocations because the worker
starts before graphics construction finishes. Complete launch-to-completion time is
also retained. These are real hardware-rendered client-window presentation timings,
**not verified desktop FPS or an end-to-end input-latency result**. Failed paused
pilots remain identifiable and do not enter comparison statistics.

The second candidate reuses the centres, line and overlay GPU upload buffers,
growing only when needed. Compare it against the indexed build with the same
one warm-up and three alternating pairs at each size. There is no snapshot,
shader, camera, timestep, observation frequency or particle-count change.

### Capacity and diagnostic follow-up

After the paired campaigns, test 48,000 (40×40×30) and, if it keeps pace, 64,000
(40³). If 48,000 falls short, test 40,000 (40×40×25), then bracket between the
passing and failing counts in increments of 1,600 particles (one lattice layer).
Use one warm-up and three ordinary candidate runs at admitted counts, the same
five simulated seconds and fixed 240 Hz schedule. Report the highest tested count
and the tested bracket, rather than claiming an exact universal capacity.

Separately compare the unchanged headless solver with the live path to bound
the removable graphics contention. Trace the first 240 steps at the three required
sizes with Nsight, and measure GPU draw timestamps in separately instrumented
baseline/indexed builds. Those timestamp builds deliberately wait for query readback
and cannot supply ordinary FPS or throughput results.

The first 48,000-particle capacity series overlapped a CPU pixel audit and is retained
as exploratory evidence. The later 40,000/38,400 bracketing series ran independently.
The latter count exceeds real time on its five-second average but falls below it in
late one-second windows. Extend validation to 20 simulated seconds at 38,400 and
36,800 particles (three runs each); continue down a layer if required. Distinguish
average capacity, sustained-window capacity and practical headroom.
