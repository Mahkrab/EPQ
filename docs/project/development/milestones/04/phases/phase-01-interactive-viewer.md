# Phase 1 interactive viewer

## Starting point

Work began with clean EPQ `5d145c265c6e3148476535f2da79a3e814e2a3c1` and Maelstrom
[`423ac5c6cd0a1939eea9225cad8d7dda2197c0c2`](https://github.com/Mahkrab/Maelstrom/tree/423ac5c6cd0a1939eea9225cad8d7dda2197c0c2).
The latter is the completed non-visual controller. Its worker ownership, accepted snapshots and
bounded controls remain the numerical boundary; the
[application contract](/docs/project/development/milestones/04/application-contract.md) owns the
presentation behaviour.

## Scope and outcome

The optional viewer draws opaque particle spheres and clipped plane outlines, exposes scene,
configuration and execution selection, and reports accepted progress, warnings and failures.
Pause/resume, single-step, reset, cancellation, prior-outcome inspection and camera controls work
through the existing controller. Strict presentation settings remain separate from physical input
identity. Headless commands, numerical source, goldens and result/replay schemas are unchanged.

The implementation is now committed as Maelstrom
[`52d7bffe3923e8d16477a7227c28245777fc4a34`](https://github.com/Mahkrab/Maelstrom/tree/52d7bffe3923e8d16477a7227c28245777fc4a34).
All 117 simulator hashes and both display-harness hashes in the retained
[source manifest](/docs/project/development/milestones/04/assets/viewer-v1/source-manifest.json)
match the assessed files. EPQ's gitlink pins that implementation, and annotated
`milestone-04/phase-01/complete` tags identify the subsequently authorised local completion checkpoints
in both histories. Original verification records retain their collection-time provenance unchanged;
remote publication and hosted verification remain separate.

## Decisions and implementation

### Separate drafts, selected runs and prior outcomes

The keyboard panel edits a draft without modifying the selected physical request. Apply resolves
it using existing file/scene/command-line precedence before submitting a new paused run. Invalid
input leaves the selection intact. Worker resource failure creates a visibly failed generation
with no accepted snapshot or invented effective device. The retained prior outcome can be inspected
under a distinct PRIOR label; ordinary controls still address the selected generation.

Receipts are polled instead of waited on in the event loop. Reset uses the selected original inputs,
so unapplied edits cannot change it. Cancellation bypasses queue capacity. Close and graphics failure
request cooperative teardown and keep processing events until the solver worker and any requested
density audit have finished. Density auditing uses one separate thread and an owned accepted
snapshot, labelled with its generation and step; redraw never triggers it.

### Optional graphics and world-space interpretation

The agreed winit/wgpu design is implemented behind `viewer` and `render`, with default features
still empty and CUDA independent. Shared drawing accepts a supplied texture view, so offscreen builds
need no window library. PNG encoding remains deferred. A small bitmap font avoids adding another
application scheduler. The locked Linux dependency graph, including build dependencies, has a
[licence inventory](/docs/project/development/milestones/04/assets/viewer-v1/dependency-licences.json)
and retained upstream notices in Maelstrom.

Camera calculations use f64 world metres and convert view-relative data to graphics f32. They never
write accepted particles. Fit is explicit, uses initial bounds and handles empty input; invalid
camera changes preserve the previous view. Triangle spheres use fixed tessellation, directional
lighting and depth testing. Infinite planes appear only where they cross the frozen display box.
The panel can be hidden to inspect occlusion. Redraw FPS is labelled separately; no solver timing
or simulation-throughput measurement is claimed.

Resize replaces depth resources, zero extent/occlusion skip drawing, and surface recreation retains
the selected graphics device. Asynchronous graphics errors are retained and polled. A device test
exposed that explicit device destruction was initially ignored by the callback; the final callback
reports that resource loss too, and both local and PC checks verify the corrected path.

## Verification

The [evidence directory](/docs/project/development/milestones/04/assets/viewer-v1/README.md) retains
commands, exits, environments, source and image hashes, transcripts and the completion audit.
The full CPU-only and viewer regression suites passed without display variables and with deliberately
unusable CUDA/compiler paths. Final focused tests cover the changed presentation and input surfaces;
strict Clippy, formatting, warning-free Rustdoc and the window-free render build also passed.

CPU checks compare every particle identity and all six binary32 components against direct execution
for brute force, serial grid and threaded grid. Display cadence, dropped observations, camera motion,
draft edits, stepping and reset leave those results unchanged. Independent camera probes establish
screen orientation, metre scale and depth. Real software-Vulkan readback checks background colour,
asymmetric geometry, depth occlusion, empty output and repeatable same-context pixels.

A separate X11 window received native events addressed to its own process. Retained screenshots and
observations establish controls, cumulative warnings, input rejection, unavailable CUDA feedback,
prior-outcome labelling, surface recreation, resize, minimise/restore, cancellation and clean close
during running work. Wayland also rendered successfully. The initial desktop-wide automation attempt
was inconclusive because the user was testing the same window concurrently; its failed transcript
was retained and does not support the final control claim. A final review also found that a
scene-selected configuration error outside the invocation directory could reveal its absolute
directory. The repaired feedback passed three CLI checks locally and on the PC, and a separate
native error-window inspection confirmed the directory was replaced with a label. Renderer and
window sources did not change after the complete interaction journey.

On the primary PC, CUDA viewer tests passed exact comparisons with direct execution, camera changes,
reset and teardown. A further test drew CUDA-worker snapshots on an independently selected software
Vulkan device while preserving exact serial-reference bits. Deliberate graphics destruction then
cancelled the worker while retaining its accepted state. This exercises owned snapshot transport,
not zero-copy interoperability or a physical device-loss event.

## Limitations and Gate G01

**G01 is satisfied for the implemented viewer and the recorded qualification boundaries.** Local
interaction used WSLg and llvmpipe software Vulkan. X11 initially lacked native keyboard libraries;
the final launcher reports this explicitly. The X11 journey used identified Ubuntu packages extracted
into a temporary runtime without changing the system installation. Wayland needed no such extraction.

Hardware Vulkan presentation and an interactive CUDA-plus-display journey remain unqualified; the
PC had no display session. Physical device loss and hung-driver recovery were not forced. Native
Windows, macOS, browsers and other graphics backends are not qualified. Synchronous graphics calls,
solver stages and density auditing have no shutdown deadline. These limits do not imply a benchmark
result or support for reproducible offline sequence export, which remains subsequent work.
