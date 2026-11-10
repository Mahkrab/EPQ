# S083 — Blender Foundation and contributors (2025)

## Full reference:

Blender Foundation and contributors (2025) *Blender 4.5.0 Mantaflow cache implementation*.
Revision `8cb6b388974a817afedf1317ce26f0c75aa5f181`, tag `v4.5.0`.

#### https://github.com/blender/blender/tree/8cb6b388974a817afedf1317ce26f0c75aa5f181

## Relevance:

Concrete evidence for separate baked data, derived geometry and additional restart fields.
Supports Maelstrom's render-cache/checkpoint distinction without importing a grid-fluid schema.

## Reliability:

Primary, version-pinned implementation. Inspected source establishes code paths; Blender was
not executed and no speed, crash-recovery or render-equality result is inferred. The manual page
fetch failed; source inspection supplies the detailed claims rather than an unread manual.

## Tags

`cache`, `blender`, `mantaflow`, `checkpoints`

## Reading notes

- Read `source/blender/blenkernel/intern/fluid.cc`, `intern/mantaflow/intern/MANTA_main.cpp`,
  and generated Python templates `strings/fluid_script.h` and `strings/liquid_script.h`.
  The modifier distinguishes modular/all/replay and reads data, mesh and particle caches separately.
  It resets an outdated Replay cache at the start frame and uses paused bake counters to select
  the preceding frame for resumable baking; derived bake products cannot advance beyond base data.
- `liquid_save_data` and `liquid_load_data` select final fields or final plus resume fields using
  a `resumable` argument. Mesh and secondary-particle products have separate functions.
- `fluid_file_export` normally skips intermediate subframes. It dispatches combined VDB or mesh
  saves and falls back to per-object files. Native formats and precision choices are not universal
  lossless particle archives. Template multiprocessing options are conditional.
- The inspected Python import/export helpers catch exceptions and log them. This is an observed
  implementation detail, not a failure policy recommended for Maelstrom.

#### Date added

10/11/26
