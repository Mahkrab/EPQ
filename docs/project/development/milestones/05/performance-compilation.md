# Compilation and PC graphics repair

The user reported that a roughly 100k-particle scene compiled slowly, with brief GPU
activity separated by long idle periods, despite much faster headless execution.
Most graphics commands required `--software`, and the PC also had windowing errors.
This investigation concerns the complete image-producing command, separately from
the [solver optimisation programme](/docs/project/development/milestones/05/performance-plan.md).

## Cause and decision

`compile` does more than `run`: it advances the solver, renders each scheduled
observation, reads its pixels back, encodes a PNG and publishes it before continuing.
The default stride is 1, so timestep refinement can mean many images per simulated
second. Its synchronous image boundary deliberately preserves every requested frame.

Maelstrom previously enabled only Vulkan. On the PC, that exposed CPU rendering,
while CUDA could still use the RTX 4070 for physics. Supplying `--software` therefore
made compilation spend most of its time drawing particles on the CPU. This explains
why the headless improvements did not carry through to the user's normal workflow.

The repair enables the existing wgpu OpenGL ES backend alongside Vulkan. Hardware
Vulkan remains preferred; accelerated OpenGL is also usable, and software rendering
still requires an explicit request. The PC now selects `D3D12 (NVIDIA GeForce RTX 4070)`
through OpenGL. The added lockfile entries belong to that backend's loaders/bindings;
no numerical dependency or solver equation changed.

Windowed graphics now receive the compositor connection belonging to their window.
Device limits request drawing capabilities without unnecessary compute requirements,
which also permits the laptop's Intel graphics. Hardware tests exposed a Mesa cleanup
crash when a worker unloaded the driver before its thread-local callbacks ran. A
process-lifetime loader fixes that lifetime, while each renderer keeps its own context;
sharing one context failed the concurrent checks with `EGL_BAD_ACCESS`.

## Primary-PC evidence

The [retained results](/docs/project/development/assets/compile-graphics-v1/README.md)
include separate exploratory campaigns and verification of the installed repair.
The installed comparison used 110,592 particles, CUDA, eight steps with timestep
refinement 4, stride 1 and nine fitted-camera images at 1280×720. The PC had a Ryzen
9 7900X and RTX 4070, driver 610.88, under WSL2. These are short diagnostic requests,
not a replacement for the 480-step solver baseline.

| Installed executable, one matched pair | Software graphics | Hardware graphics |
| --- | ---: | ---: |
| Complete command wall time | 39.698 s | 2.435 s |
| Graphics and readback | 36.524 s | 0.126 s |
| PNG encoding and publication | 0.334 s | 0.335 s |
| Solver step intervals | 0.971 s | 0.146 s |

Both bundles completed, passed independent bundle validation and contained identical
inputs, accepted diagnostics and all nine accepted-state hashes. The exploratory
three-pair campaigns also showed the large rendering difference. Solver intervals
within compilation are affected by the surrounding workload; they are not evidence
of a new numerical optimisation. Different graphics drivers need not produce identical
pixels, so image hashes were not used to demand cross-driver equality.

## Window repair and verification

New PC shell sessions receive conditional WSLg display variables and select Mesa's
D3D12 driver and NVIDIA adapter. `MAELSTROM_WINDOW_BACKEND=x11` selects X11 for
Maelstrom alone. Native Wayland testing encountered a connection reset and a reported
Weston crash; that underlying compositor problem remains unresolved. X11 viewing and
saved playback passed checks for mapped windows, varied rendered pixels and clean
close events, including through the installed `maelstrom` command without `--software`.

The broader local viewer-enabled suite passed 271 tests before the follow-up repairs.
Final targeted checks passed all 36 library tests, including device-failure cases,
18 export/CLI tests, explicit software drawing and two hardware checks on the laptop.
The PC also passed both hardware checks, including independent rendering threads.
Strict Clippy passed. No hosted verification or full new CUDA solver campaign is claimed.

The installed executable was built from an uncommitted repair based on Maelstrom
`8c5fc2d815f6e6c1d17b8eeed17cd7bf22b43fce`; its build source hash is
`1a3286f6cf2daf6d1feea6ac0d10a1560e6a899f694458d8c7527d9668162a99`.
That hash matches the local implementation with the unrelated custom scene excluded.
The previous installed executable and shell configuration were backed up. Neither
repository history nor the parent gitlink was changed.

The retained change removes the measured software-rendering bottleneck. Compilation
still includes rendering, synchronous readback, PNG encoding, hashing and file output.
Frame stride and dimensions remain explicit presentation choices; no frames or solver
steps were silently dropped, and these results do not qualify long or settled trajectories.

## Large compiled runs: 25 October follow-up

The user's later 800,000-particle compilation completed 360 steps and published all
361 images. Its 271,654,072-byte manifest exceeded the player's independent 64 MiB
limit. Compilation consequently reported that the completed manifest was not playable.
The images were intact; another simulation or rendering pass was unnecessary.

Playback now reads the manifest from a buffered stream and skips numerical provenance,
retaining only dimensions, timing and the frame index. The one-million-frame ceiling
is enforced while reading the index. Existing schedule, safe filename, schema, image-size
and hash checks remain. There is no replacement aggregate manifest-size cutoff.
`runs list` also streams completion metadata. `runs validate` separately reads typed
numerical input and validates every image, while `runs show` and numerical reruns still
need memory for the selected input. Existing bundles need no format migration.

The old installed PC executable reproduced the size-limit rejection. The fixed release
build validated every image in the existing bundle in 4.42 s, with 162.7 MiB peak resident
memory. This includes numerical-input validation, not just opening the playback index.
An X11 WSLg check then displayed the saved image at 1280×720, observed varied pixels and
closed cleanly, without software rendering or simulation. The original manifest and
images were left untouched. The saved run retains its original numerical warnings.

Regression tests cover manifests above 64 MiB, ignored provenance, trailing corruption,
library listing, inspection, input reruns and corrupted images. Evidence and the distinction
between the tested build and installed executable are retained under
[large playback](/docs/project/development/assets/large-playback-v1/README.md).
