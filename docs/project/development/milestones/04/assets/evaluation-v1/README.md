# Application verification and handoff evidence

Collected locally and through `ssh pc` on 21 October 2026. This supports the
[application evaluation](/docs/project/development/milestones/04/application-visualisation.md) and
[phase record](/docs/project/development/milestones/04/phases/phase-03-evaluation-handoff.md).
It is correctness, usage and retention evidence, not a performance campaign or hosted verification.

## Source and environment

[Source context](/docs/project/development/milestones/04/assets/evaluation-v1/source-context.json)
records clean collection-time EPQ/Maelstrom commits, all 138 tracked simulator file hashes, toolchain
and local environment. The implementation is Maelstrom
[`9336ee42104badb1b5e439edc1df5e8488c32987`](https://github.com/Mahkrab/Maelstrom/tree/9336ee42104badb1b5e439edc1df5e8488c32987).
Subsequent local changes affect three simulator guides, the parent native-window harness, its two
new unit checks and the assessment documents. Production Rust/native sources are unchanged.

Local checks use x86_64 Ubuntu 24.04.5 on WSL2, Rust/Cargo 1.98.1 and llvmpipe LLVM 20.1.2,
Mesa 25.2.8 (`0ubuntu0.24.04.4`). The native harness uses WSLg Xwayland. Its
[temporary native runtime](/docs/project/development/milestones/04/assets/evaluation-v1/native-runtime.json)
extracts the same two package hashes as the earlier display inventory, without global installation.

The [PC transfer record](/docs/project/development/milestones/04/assets/evaluation-v1/pc-transfer.json)
identifies a new isolated temporary source directory and archive hash. All 138 copied files matched
before execution. No existing PC source checkout or Git state was changed. The
[PC context](/docs/project/development/milestones/04/assets/evaluation-v1/pc-context.json)
records WSL2, Rust/Cargo 1.96.0, CUDA 13.3.73, driver 610.88 and RTX 4070. Display variables were
removed and `CUDA_HOME=/usr/local/cuda` was explicit. Software graphics remains independent of CUDA.

## Automated checks

[Local command records](/docs/project/development/milestones/04/assets/evaluation-v1/checks.json)
and [PC command records](/docs/project/development/milestones/04/assets/evaluation-v1/pc-checks.json)
retain argument arrays, environment overrides, exits and log basenames. Durations are monotonic
verification-job diagnostics. The [summary](/docs/project/development/milestones/04/assets/evaluation-v1/summary.json)
counts completed test groups from those logs.

| Check | Result |
| --- | --- |
| Release CPU/headless, no display and deliberately invalid toolkit/compiler paths | 224 passed, none ignored; dependency tree has no graphics/windowing/CUDA dependency requirement. |
| Release render-only library | 22 passed; its two device tests run in the full explicit graphics suite. |
| Release viewer | 257 passed; eight opt-in checks separately run and all passed, serially, without display variables. |
| Formatting, strict Clippy across viewer targets, warning-denied Rustdoc | Exit 0. |
| Python root, baseline and verification suites | 16 + 26 + 7 = 49 passed, including focus refusal/delivery checks. |
| Release PC CUDA/viewer | 257 passed; all 20 opt-in hardware/graphics checks separately run and passed. |

The eight local opt-in checks cover decoded-pixel repetition, observation hashes, frozen falling-block
and small-lattice requests, projection/depth/orientation, publication/cancellation/mismatch/interruption
failures, device/encoding fault injection and saved-pixel drawing. PC checks additionally exercise
CUDA arithmetic, rollback, replay, controller lifetimes and live snapshot transport to independent
software Vulkan. Ordinary suite ignored counts denote opt-in checks subsequently executed, not passes.

## Real windows and usage

[Display commands](/docs/project/development/milestones/04/assets/evaluation-v1/display-checks.json)
retain both initial and corrected-harness attempts. The first live journey timed out after sending N:
the title remained paused at zero. Cleanup exited the owned viewer. Its log and initial image remain
in `live-display/`; it is not a pass. The initial saved-player journey passed. The corrected harness
establishes and verifies focus before sending native keys, as the locked winit X11 handler requires.
The [focused live journey](/docs/project/development/milestones/04/assets/evaluation-v1/live-display-focused.log)
then passed all CPU modes, pause/step/reset, completion, invalid draft, explicit unavailable CUDA,
prior outcome, camera/audit, resize/minimise, surface recreation and close while running. The
[focused player journey](/docs/project/development/milestones/04/assets/evaluation-v1/saved-display-focused/result.json)
passed seeking, endpoints, pause/resume, speed, restart, final hold, resize and close, with all saved
files unchanged. Both corrected runs exited 0. Screenshots were inspected locally.

![Live viewer after resize, with an explicitly labelled earlier audit](/docs/project/development/milestones/04/assets/evaluation-v1/live-display-focused/x11-10-restored.png)

![Saved fixed-camera image letterboxed after square resize](/docs/project/development/milestones/04/assets/evaluation-v1/saved-display-focused/resized.png)

[Usage commands](/docs/project/development/milestones/04/assets/evaluation-v1/usage-checks.json)
retain an initial rejected stride-120 request: sparse golden observations do not include step 360,
and no destination was created. The corrected documented stride-240 request exports 0/240/480.
Manifest replay then starts a fresh numerical run, and saved-export of that result reproduces every
frame entry and observation/PNG/pixel hash. The
[round-trip report](/docs/project/development/milestones/04/assets/evaluation-v1/usage-roundtrip.json)
records that equality and graphics/build identity; the completion manifest is retained separately.
The temporary sequences themselves are outside Git.

## Retention and limits

[Handoff integrity](/docs/project/development/milestones/04/assets/evaluation-v1/handoff-integrity.json)
compares 55 numerical/input/timing files with the CUDA campaign revision and checks 431 historical
assets and 11 frozen fixture hashes. It does not repeat the original full statistical audit.
Historical evidence directories were left untouched. New file hashes and document checks are
retained alongside this inventory; they identify local evidence without claiming a committed boundary.

No hardware-Vulkan qualification, PC interactive window, alternate-platform test, performance
measurement, physical validation, hosted check or new Compute Sanitizer result is claimed.
Injected device destruction does not establish recovery from a hung or physically lost GPU.
Same-environment decoded-pixel repetition does not establish cross-driver equality. Completion
commits, exact parent gitlink and annotated completion tags still require separate authority.
