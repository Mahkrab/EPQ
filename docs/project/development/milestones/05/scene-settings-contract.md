# Scene settings and launch contract

## Status and scope

This completes the settings-design step of the
[scene-usability plan](/docs/project/development/milestones/05/scene-usability-plan.md).
The decisions below govern the new input formats. The
[resolution record](/docs/project/development/milestones/05/scene-settings-resolution.md) and
[authoring record](/docs/project/development/milestones/05/scene-authoring.md) distinguish the implemented
input features from the remaining presentation work.
The reviewed starting points are EPQ `812dea60d8527b8ed977c6bd5d865199397aa374` and Maelstrom
[`4a9675b5f9e3b7aa90335f5a77bdb3e82093a1b5`](https://github.com/Mahkrab/Maelstrom/tree/4a9675b5f9e3b7aa90335f5a77bdb3e82093a1b5).
Existing numerical inputs, equations and solver acceptance remain unchanged by this design record.

## Settings ownership

An editable scene package has `scene.toml`, `config.toml` and optional `render.toml` beside one another.
These are user inputs, not a prescribed Rust module layout. A scene may still refer to a shared
numerical configuration instead of its own `config.toml`.

| Concern | Authoritative home | Rule |
| --- | --- | --- |
| Numerical model | The selected configuration's `[numerical]` table | Owns timestep, refinement, particle spacing and fluid parameters; retains the existing field names, units and domains |
| Geometry and initial state | `scene.toml` | Owns particle sources, positions, velocities, identities and ordered boundaries; generated spacing inherits the numerical value |
| Reusable run length | Optional `[run]` in `scene.toml` | Selects either `steps` or `duration_s`; it does not select a timestep or backend |
| Presentation and image sampling | `render.toml` | Owns camera, particle colours, image dimensions, PNG format and accepted-step stride |
| Machine execution preferences | Existing application preferences | Owns backend, CPU threads, CUDA device and block size; never supplies physics or scene geometry |
| Measurement and publication | Explicit command options | Measurement, audits/checkpoints, pacing overrides and output destinations are not silently enabled by scene defaults |

Newly created packages store effective numerical primary values in their configuration, clear scene
overlays and omit duplicated lattice spacing. Editing `particle_spacing_m` then changes both lattice
construction and derived values. A supplied lattice `spacing_m` remains an exact binary32 assertion
against that effective value; disagreement is an error. It never overrides numerical spacing.
Advanced scene overlays remain supported and visible in inspection, rather than becoming a second
copy of every setting. Derived inputs are assertions, not independent values to merge.

## Resolution and conflicts

| Domain | Order, from lowest to highest precedence | Conflict behaviour |
| --- | --- | --- |
| Numerical primary values | Built-in numerical defaults → selected configuration → scene overlay → CLI `--set` | Omission inherits; duplicate assignments within a layer fail |
| Refinement | Built-in factor 1 → configuration → scene overlay → CLI | Select one factor, then apply it once after primary resolution |
| Run limit | Scene `[run]` → explicit `--steps` or `--duration` | Replace the whole limit selection; two limits in the same layer fail |
| Rendering | Built-in presentation defaults → selected render document → explicit presentation flags | `--render-config` replaces scene-local `render.toml`, rather than merging both files |
| Execution | Existing automatic selection → application preferences → explicit execution flags | Retain current resource-conflict checks and explicit-backend behaviour |

`--config` replaces the scene-selected base configuration, retaining its overlay. Environment
variables select storage roots only. Scene/configuration paths resolve against the scene file's
directory; explicit CLI paths resolve against the invocation directory. No parent-directory search
or working-directory fallback selects another scene's settings. Bundled inputs use their embedded
resources, never a neighbouring checkout file.

For new numerical inputs, resolve all primary overrides, select refinement `N` in `1..=16`, divide
the selected timestep by `N` and correction scale by `N²`, then validate and derive. `--refine-timestep`
and CLI `--set refine_timestep=...` are alternative spellings of one selection and conflict together.
A CLI factor of 1 overrides saved refinement. Supplied primary values must satisfy their individual
types, finite-value rules and domains even when shadowed. Every supplied derived assertion is checked against
the final derived values; contradictory assertions fail, including those in a lower layer.
Inspection records unrefined values, the selected factor and its origin, and effective values.
Recorded runs store effective values, not a recipe to apply again during rerun.

`[run]` accepts only `steps` (a non-negative TOML integer representable as `u64`) or `duration_s`
(finite, non-negative seconds).
An absent table supplies neither. An empty table or both fields is invalid. Without a saved or CLI
limit, execution asks for a limit; it never invents an unbounded run. Duration is rounded up to a
whole count of effective fixed timesteps, with representability checks. Zero observes initial state.
Scene creation retains a source's saved limit, or writes `duration_s = 1.0` when none exists.
`run` remains paced by default, `compile` runs without pacing and `view` retains live-view semantics.
Image stride never skips simulation steps; `play` uses saved images without reading current scene settings.

Only a missing optional `render.toml` uses presentation defaults. An unreadable or malformed selected
file fails; an explicit missing `--render-config` never falls back. `inspect` shows each domain's
effective values, origins and command applicability; `validate` checks the package without simulation
or graphics initialisation. Headless execution does not load presentation settings. Persisted
provenance uses portable package-relative labels and content identities, not personal absolute paths.

## Camera, colours and sampling

Rendering keeps `width = 1280`, `height = 720`, `format = "png"` and `step_stride = 1` as defaults,
with the current dimension and stride domains. `step_stride` controls offline images only; view redraw
cadence and solver timing remain independent. Width, height and stride flags override selected values.

The new render format adds `camera_mode = "fit"` by default. `"fixed"` requires a `[camera]` table;
an explicit camera table without a mode selects fixed behaviour. Its existing fields and validation
remain supported. An explicit `"fit"` with a fixed-camera table is contradictory and fails.
Fit uses finite declared domain bounds when available, otherwise initial particle bounds. If neither
provides a usable finite extent, use the documented existing fixed-camera fallback. It fits once, not every frame.
Explicit `--fit-camera` overrides a saved fixed camera. New `--no-fit-camera` selects the saved fixed
camera or that fallback; the two flags conflict. Saving the current viewer camera writes fixed mode
and its values to the scene's `render.toml`, preserving unrelated settings and reporting write failures.
Publish the saved document atomically; a failed save must leave the previously accepted file intact.
Saving is explicit; launch and temporary overrides never rewrite input files. Bundled scenes require
an editable copy before saving, and an alternative render file is changed only if explicitly selected
as the save destination.

An optional `[particles]` presentation table adds `colour_mode = "fixed"` or `"kinetic_energy"`.
Fixed mode defaults to `colour = "#2b9fd9"`; colours are six-digit sRGB hex values. Energy mode requires
finite `min_energy_j` and `max_energy_j`, with `0 ≤ min < max`, and rejects a fixed `colour` field.
Fixed mode rejects energy bounds. Per-particle energy is `½m|v|²` from accepted velocity and mass;
the clamped position within the saved range maps blue `#0000ff` to red `#ff0000` by linear-RGB
interpolation before lighting. Fixed bounds avoid frame-by-frame rescaling. Rendering must not write
back to solver state, and image-only compiled runs cannot be recoloured or re-framed by `play`.

## Compatibility and migration

| Document | Existing inputs | New inputs |
| --- | --- | --- |
| Scene | Schema 1 keeps required lattice spacing and identities, and existing numerical resolution | Schema 2 adds `[run]`, inherited lattice defaults, named groups and container boxes |
| Numerical configuration | Schema 1 retains per-layer refinement and per-layer derived checks | Schema 2 uses single refinement and final derived assertions as specified above |
| Render settings | Schema 1 remains accepted with its existing fixed-camera defaults | Schema 2 adds camera mode and particle colour settings |
| Application preferences | Schema 1 is unchanged | No physics, presentation or run-limit fields are added |
| Recorded results and compiled bundles | Existing supported versions remain readable | Input revisions do not silently change result or bundle formats |

Scene and numerical configuration versions must match, including an explicit `--config` replacement.
Built-in numerical values are the same for both readers. Render versions are independent of scene
versions. Missing or unsupported versions and unknown fields fail with the document and field named.
Automatic render discovery and fit-by-default are deliberate presentation changes for fresh launches;
an explicitly selected schema-1 render file preserves its fixed camera, and saved images stay unchanged.

Migration is explicit and writes a new package without overwriting its source. Resolve the old scene
and configuration under their original rules, write the effective numerical primary values without
a refinement recipe or scene overlay, and preserve particle order and geometry. Check source assertions
under their original rules, then emit final effective assertions for the explicitly asserted fields;
do not introduce unrelated derived assertions. Report any replaced assertion and its original layer
rather than silently dropping or reinterpreting it.
Omit redundant lattice spacing only after checking it. Copy any selected legacy render settings into
schema 2 with fixed mode. A copied scene without a saved limit receives the visible one-second creation
default. Do not implement a second migration command: extend `scenes create NAME --from SOURCE`.
Simply replacing a version number is not migration when refinement or assertions change meaning.
Old reruns use recorded effective inputs and do not consult new scene defaults.

## Example package and ordinary commands

These examples are accepted by the input readers and drawing commands. The
[presentation record](/docs/project/development/milestones/05/scene-presentation.md) records the
camera and colour implementation and its verification.
In `scene.toml`, a single 64-particle lattice uses numerical spacing without repeating it:

```toml
schema_version = 2
name = "water"
description = "An editable fluid block"
randomness = "none"

[configuration]
source = "file"
path = "config.toml"

[run]
duration_s = 1.0

[particles]
construction = "lattice"
first_identity = 0
origin_m = [0.2, 0.4, 0.2]
counts = [4, 4, 4]
endpoint_rule = "counted_half_open"
order = "x_then_y_then_z"
initial_velocity_m_s = [0.0, 0.0, 0.0]

[[planes]]
normal = [0.0, 1.0, 0.0]
offset_m = 0.0
```

`config.toml` owns spacing and the reusable refinement selection; omitted primaries inherit defaults:

```toml
schema_version = 2
name = "water-model"
description = "Numerical settings for the editable block"

[numerical]
particle_spacing_m = 0.05
refine_timestep = 4
```

`render.toml` selects energy colours and fitting without launch flags:

```toml
schema_version = 2
camera_mode = "fit"
width = 1280
height = 720
step_stride = 4

[particles]
colour_mode = "kinetic_energy"
min_energy_j = 0.0
max_energy_j = 1.0
```

`scenes create water --from builtin:falling-block-04` creates an editable
package; the example above illustrates subsequent edits. `inspect water` explains the selected
values and `validate water` checks them. `run water`, `view water` and `compile water` each start a
fresh simulation using its saved limit and physics; the latter two discover `render.toml`.
The energy-colour example works for viewing and compilation. `play <run-id>` reads compiled images.
Existing temporary flags remain available, and help remains
free of examples. Output destinations are never saved as implicit overwrite permissions.

## Design review and implementation boundary

Review of the current
[numerical resolver](https://github.com/Mahkrab/Maelstrom/blob/4a9675b5f9e3b7aa90335f5a77bdb3e82093a1b5/src/config/resolved.rs),
[scene creation](https://github.com/Mahkrab/Maelstrom/blob/4a9675b5f9e3b7aa90335f5a77bdb3e82093a1b5/src/cli/scenes.rs)
and [CLI declarations](https://github.com/Mahkrab/Maelstrom/blob/4a9675b5f9e3b7aa90335f5a77bdb3e82093a1b5/src/cli/arguments.rs)
grounds the compatibility choices. At that baseline, scene creation flattened numerical overlays,
but still copied lattice spacing. Limit flags were required, rendering was explicitly selected, and
the parser accepted schema 1 only. The resolution record describes the subsequent implementation.

The ownership, precedence, example and migration decisions are complete. Executable resolution and
its checks are covered by the resolution record; full-domain camera fitting, camera saving and colour
mapping are covered by the presentation record. No performance result is claimed here.

Design-step verification parsed all three TOML examples and checked their spacing, particle count, limit,
camera and colour consistency. Repository links and whitespace checks passed, as did the three
existing Markdown tests. That initial check established document consistency; executable acceptance
and its original drawing limitation are covered by the resolution record.
