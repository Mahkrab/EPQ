# Interactive viewer verification

This dataset assesses the optional viewer against the
[application contract](/docs/project/development/milestones/04/application-contract.md).
It contains correctness, graphics and interaction evidence; it is not a performance campaign
or an offline image-sequence export. Sources remain uncommitted and are identified by the
[source manifest](/docs/project/development/milestones/04/assets/viewer-v1/source-manifest.json).

## Checks and environments

| Boundary | Evidence and observed result |
| --- | --- |
| Default headless build | [Full regression](/docs/project/development/milestones/04/assets/viewer-v1/headless-tests.txt): 223 checks passed; display variables removed and deliberately unusable CUDA/compiler paths |
| Optional viewer build | [Full regression](/docs/project/development/milestones/04/assets/viewer-v1/viewer-tests.txt): 237 checks passed, one explicit Vulkan integration check excluded from the routine suite and subsequently run separately |
| Final presentation surface | [Focused checks](/docs/project/development/milestones/04/assets/viewer-v1/focused-final.txt): 29 passed, including the later zero-extent and graphics-failure checks; [three final CLI checks](/docs/project/development/milestones/04/assets/viewer-v1/private-feedback-final.txt) cover the subsequent path-redaction repair |
| Real Vulkan drawing | [Final local device check](/docs/project/development/milestones/04/assets/viewer-v1/render-device-final.txt): asymmetric geometry, top-left orientation, background colour, depth occlusion, empty output, same-context repeated pixels and explicit device destruction passed |
| Controller and CUDA on the PC | [Final PC checks](/docs/project/development/milestones/04/assets/viewer-v1/pc-final.txt): nine viewer checks and two real Vulkan checks passed, including CUDA observations drawn by an independent graphics device |
| Build quality | Strict Clippy for default and viewer builds, warning-free Rustdoc, formatting and the render-only build passed; commands and exits are in [checks.json](/docs/project/development/milestones/04/assets/viewer-v1/checks.json) |
| Invalid launch environments | [Negative launch checks](/docs/project/development/milestones/04/assets/viewer-v1/negative-launches.json): missing display, missing X11 keyboard support, unavailable graphics adapter and invalid dimensions each returned exit 3 |

Routine full regressions ran locally on x86_64 Ubuntu/WSL2, Rust/Cargo 1.98.1. Final focused
checks followed the last presentation changes; the full numerical regression was not repeated
for those changes. No solver equations, workloads, goldens, acceptance or replay semantics changed.

Local graphics used explicit software Vulkan: llvmpipe, LLVM 20.1.2, Mesa
25.2.8-0ubuntu0.24.04.4, and a BGRA8 sRGB window surface. The PC used the RTX 4070 for CUDA
and independently selected llvmpipe/Mesa 25.2.8-0ubuntu0.24.04.2 for graphics. Its
[context](/docs/project/development/milestones/04/assets/viewer-v1/pc-context.json) retains
Rust, toolkit and device information plus hashes of every compiler input. These match the local
assessed sources. No display was available on the PC; its checks were offscreen and non-visual
controller checks, not an interactive CUDA display journey.

## Native display journey

The [complete journey transcript](/docs/project/development/milestones/04/assets/viewer-v1/final-display/journey.txt)
records native X11 events addressed to the window belonging to the launched verification process.
The [harness](/tests/verification/viewer_display.py) never sends desktop-wide keyboard input or
controls another person's viewer. Its
[display source manifest](/docs/project/development/milestones/04/assets/viewer-v1/display-source-manifest.json)
identifies the binary assessed by that complete journey. Only CLI path redaction changed afterwards;
window, renderer and controller sources are byte-identical. Three final CLI checks and an additional
[real error window](/docs/project/development/milestones/04/assets/viewer-v1/private-feedback-display/external-configuration-failure.png)
assess that repair in the current source manifest; the PC's three CLI checks passed too.
The complete journey verified step, run/pause, reset, draft editing/rejection,
serial-grid/threaded-grid/brute-force selection, explicit CUDA rejection in a CPU-only build,
retained prior state, camera fit/orbit/zoom, density-audit request, surface recreation,
resize/minimise/restore, cancellation and clean close during running work.

[Selected-step warnings](/docs/project/development/milestones/04/assets/viewer-v1/final-display/x11-02-step-warning-camera-audit.png),
[rejected input](/docs/project/development/milestones/04/assets/viewer-v1/final-display/x11-04-invalid-draft.png),
[unavailable CUDA](/docs/project/development/milestones/04/assets/viewer-v1/final-display/x11-06-cuda-unavailable.png),
[retained prior outcome](/docs/project/development/milestones/04/assets/viewer-v1/final-display/x11-07-prior.png)
and [restored window](/docs/project/development/milestones/04/assets/viewer-v1/final-display/x11-10-restored.png)
were inspected as rendered images. The request explicitly used `cfl_factor=0.000001` to expose
warning feedback; it is not a replacement benchmark or changed default. Fixed-step numerical
independence is established by the separate exact-bit tests, not screenshots or elapsed delays.

The ordinary environment lacked X11 keyboard libraries. The
[native context](/docs/project/development/milestones/04/assets/viewer-v1/x11-native-context.json)
identifies Ubuntu package versions and hashes extracted into a temporary runtime. No system
package installation was made. To repeat on an environment with the native prerequisites:

```sh
cargo build --locked --manifest-path Maelstrom/Cargo.toml --features viewer
mkdir /tmp/new-viewer-evidence
python3 tests/verification/viewer_display.py --binary Maelstrom/target/debug/maelstrom --output /tmp/new-viewer-evidence
```

For the extracted-runtime arrangement, add `--runtime-lib-dir` naming its `usr/lib/x86_64-linux-gnu`
directory. The harness requires `libX11.so.6`, `xwininfo`, `xprop`, an X11 display, and explicit
software Vulkan support. It refuses previous X11 output rather than overwriting evidence.
Screenshots are read from the client's X drawable and written by the verification harness;
this is separate from the simulator's future exporter.

## Failures, provenance and limits

The initial X11 launch failed inside upstream keyboard loading. The final launcher probes through
that library's safe API and reports the missing packages explicitly. The retained
[initial failure](/docs/project/development/milestones/04/assets/viewer-v1/initial-x11-failure.txt)
and final negative launch check establish before/after behaviour. The first Wayland automation
attempt returned exit 1 because the user was manually testing the same window concurrently.
Its [transcript](/docs/project/development/milestones/04/assets/viewer-v1/display-journey.txt)
and screenshot remain inconclusive; it is not counted as a passed control sequence. Wayland
rendering itself was observed. The targeted X11 sequence and final repeated journey passed.

The first local/PC explicit-destruction checks failed because the callback ignored `Destroyed`.
Their transcripts remain retained. The corrected callback and final checks report that graphics
failure while retaining accepted solver state. A Rustdoc failure interpreting a depth interval
as a link was corrected and its failed and successful transcripts are retained. Personal source
and invocation paths in transcripts are replaced with labels; substantive failures are preserved.

The [dependency licence inventory](/docs/project/development/milestones/04/assets/viewer-v1/dependency-licences.json)
records 144 resolved Linux packages, including build dependencies. Maelstrom retains their shipped
notices in `THIRD-PARTY-NOTICES.txt`; two crates have no standalone licence file and retain their
manifest declarations and repository references instead. Default runtime dependencies contain no
wgpu, winit or CUDA toolkit boundary. Render-only runtime dependencies contain no winit.

Hardware Vulkan presentation, an interactive CUDA-plus-display journey, physical device loss,
hung-driver recovery, other operating systems and graphics backends remain unqualified. Zero
extent/occlusion guards are deterministic tests; the real window was minimised/restored and resized.
Tests impose no shutdown deadline or cross-device image-equality guarantee. No hosted check,
publication or durable completion checkpoint is claimed. The
[completion audit](/docs/project/development/milestones/04/assets/viewer-v1/completion-audit.json)
maps the required outcomes to their evidence.
