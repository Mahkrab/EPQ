# Phase 3 application evaluation and final-comparison handoff

## Starting point

Work began on the existing `phase/04-03-evaluation-handoff` branches with clean EPQ
`47f5d2c3f0d24c3edc4057f18b8849a83bfa3b13` and Maelstrom
[`9336ee42104badb1b5e439edc1df5e8488c32987`](https://github.com/Mahkrab/Maelstrom/tree/9336ee42104badb1b5e439edc1df5e8488c32987).
The annotated `milestone-04/phase-03/start` tags identify that pairing. Live viewing, PNG export
and saved-image playback were already implemented. The
[application contract](/docs/project/development/milestones/04/application-contract.md) owns the
interaction, lifecycle, frame and publication obligations assessed here.

## Scope and outcome

The [application evaluation](/docs/project/development/milestones/04/application-visualisation.md)
assesses usability, numerical independence, failure retention and output reproducibility separately.
It provides supported launch paths and recovery guidance, explains cost boundaries and hands the
retained CPU/CUDA controls to the final research comparison. Fresh local and primary-PC checks
support the recorded environment qualification. No numerical implementation, tolerance, golden,
dependency or benchmark changed, and no new performance campaign began.

## Decisions and implementation

The earlier records own the worker and synchronous-export decisions; this assessment explains their
consequences rather than inventing retrospective alternatives. A coalesced display observation can
skip states while fixed solver work continues. Export must retain every scheduled observation and
wait for each frame's publication. The final manifest distinguishes completed image output from the
original numerical outcome, including explicit partial prefixes.

Review corrected the controller guide's obsolete no-export sentence and clarified shared feature
builds, initial-fit camera clipping and the player's separate manifest-size limit. These are existing
behaviours and limitations, not new numerical or rendering features.

The first fresh native-viewer journey timed out on its first step key. Inspection of the locked
winit event path found that core key delivery requires a focused active window; the harness addressed
its own drawable without establishing focus. The parent test harness now requests and verifies focus
on its own window before sending keys. Two unit tests check refusal without focus and addressed
press/release delivery. Both real viewer and player journeys then passed. The application itself
still leaves the person's existing keyboard focus alone. The failed attempt remains evidence.

A launch-example check also rejected stride 120 against the sparse falling-block golden: step 360
is not stored. It created no output. The new guide uses stride 240, selecting stored steps 0/240/480.
Its saved-export, manifest-replay and saved-export round trip preserves every frame entry, including
observation, PNG and decoded-pixel hashes. This verifies the actual command rather than guessing
that an apparently suitable stride is available.

## Verification

The [evidence inventory](/docs/project/development/milestones/04/assets/evaluation-v1/README.md)
retains commands, exits, logs, source identities, screenshots and failures. Local x86_64 Ubuntu/WSL2
checks used Rust/Cargo 1.98.1. All **224 headless tests** passed with display variables removed and
invalid CUDA/compiler paths. The viewer suite passed **257 tests**, followed by all **eight** explicit
software-Vulkan checks, with no ignored device check left unexercised. Render-only library checks,
formatting, warning-denying Clippy and Rustdoc passed. The three parent Python suites passed
**49 tests**, including the two harness checks.

The primary PC used an isolated source copy whose 138 tracked files were hash-verified before
testing; no existing PC checkout or Git metadata changed. Rust/Cargo 1.96.0, CUDA 13.3.73 and the
RTX 4070 with driver 610.88 passed **257 ordinary tests** and all **20 explicit device checks**.
These include worker-owned CUDA lifecycle, direct-result agreement, camera/cadence independence,
rollback and independent software-Vulkan drawing. Local WSLg Xwayland windows exercised controls,
resize/minimise, resource failure, retained outcomes and close during work. Saved playback left
all sequence files unchanged. The evidence distinguishes native events and inspected screenshots
from deterministic clock/model tests.

The handoff integrity check found 55 existing numerical/input/timing files byte-identical to the
CUDA campaign revision, all 431 indexed historical qualification/campaign assets intact, and all
11 frozen input/golden hashes matching. This establishes retention rather than a new audit of
every historical statistic. Verification-job durations are not application performance samples.

## Limitations and Gate G03

**G03 is satisfied within the qualification limits below.** The authorised local checkpoint retains
Maelstrom [`a881145a373fe2a4c9a25b0ca10f3b89c2b1db9e`](https://github.com/Mahkrab/Maelstrom/tree/a881145a373fe2a4c9a25b0ca10f3b89c2b1db9e),
then EPQ's exact gitlink, harness tests and evidence. Annotated `milestone-04/phase-03/complete`
and `milestone-04/complete` tags identify the completion in both histories. Only the three reviewed
Maelstrom guides differ from the tested starting commit; numerical and rendering code are unchanged.
The [checkpoint audit](/docs/project/development/milestones/04/assets/evaluation-v1/checkpoint-verification.json)
records the fresh parent checks and evidence-integrity review. Original collection inventories retain
their pre-checkpoint context. No remote publication or hosted verification is claimed.

Qualification covers the recorded WSL2/WSLg/software-Vulkan paths and RTX 4070 CUDA integration.
Hardware Vulkan, a fresh PC interactive-display journey, other platforms/devices and zero-copy
graphics sharing remain unverified. No shutdown deadline, cross-driver pixel equality, crash
durability, real-time performance, physical validation or hosted verification is claimed. Final
cross-backend research synthesis remains subsequent work.
