# Maelstrom scene, settings and fluid-control plan

## Aim and starting point

Make an editable scene the reliable starting point for running, viewing and compiling a simulation.
Users should be able to change its settings once, arrange more than one fluid block and keep a useful
camera without rebuilding Maelstrom or repeating a long command. Then implement the fluid effects
whose names are already exposed but whose enabled behaviour is currently unsupported.

This is the Phase 02 plan on `phase/05-02-scene-usability`. Planning starts from EPQ
`812dea60d8527b8ed977c6bd5d865199397aa374` and Maelstrom
[`4a9675b5f9e3b7aa90335f5a77bdb3e82093a1b5`](https://github.com/Mahkrab/Maelstrom/tree/4a9675b5f9e3b7aa90335f5a77bdb3e82093a1b5).
The [performance investigation](/docs/project/development/milestones/05/performance-plan.md) remains
open, but further speculative optimisation is paused while these usability problems are addressed.
This decision does not establish competitive performance or readiness for final evaluation.

## What needs changing

The current [input resolver](https://github.com/Mahkrab/Maelstrom/blob/4a9675b5f9e3b7aa90335f5a77bdb3e82093a1b5/src/cli/inputs.rs)
applies scene overlays after the selected numerical configuration, then CLI overrides. That explains
some apparently ignored edits; there is no evidence here that precedence itself is broken. Bundled
scenes are embedded at build time, whereas user-library scenes are editable files.
The [scene format](https://github.com/Mahkrab/Maelstrom/blob/4a9675b5f9e3b7aa90335f5a77bdb3e82093a1b5/src/scene/document.rs)
accepts one explicit particle list or one lattice. Lattice spacing must also match a separate numerical
field. Boundaries are ordered infinite half-spaces, so constructing a container requires plane maths.

The [camera](https://github.com/Mahkrab/Maelstrom/blob/4a9675b5f9e3b7aa90335f5a77bdb3e82093a1b5/src/render/camera.rs)
has fixed defaults; fitting covers the initial particles, not the complete trajectory. Presentation
settings need a separate launch argument, and the viewer offers no action to save the current camera.
The [configuration validator](https://github.com/Mahkrab/Maelstrom/blob/4a9675b5f9e3b7aa90335f5a77bdb3e82093a1b5/src/config/validation.rs)
rejects enabled XSPH viscosity and vorticity confinement. These are missing implementations, not
working material controls. This starting assessment is a source review, not a new benchmark.

## 1. Settle settings ownership and the ordinary user journey

Define one clear home for each setting: numerical model, scene geometry, run defaults, presentation
or machine preferences. Keep shared numerical files useful, but remove accidental duplication from
newly created scene packages. Give particle spacing one authoritative editable value; old explicit
spacing assertions must still be checked rather than silently discarded.

Specify how scene-local run and presentation defaults are discovered automatically. Store presentation
settings in `render.toml` beside `scene.toml` and load it without requiring `--render-config`.
Cover timestep refinement, run length, camera, particle colours, image size and observation cadence
without making machine-specific backend preferences override scene physics. Explicit command-line
choices remain temporary overrides.
Retain `compile` for producing saved output, `run` for fresh headless execution, `view` for fresh live
viewing and `play` for saved playback. Extend existing commands only where a real operation is missing.

**Done when:** a short ownership and precedence table explains each layer, path base and conflict;
an example package can express the intended run without repeated numerical or camera flags; schema
compatibility and migration decisions are explicit. Do not design the complete file layout in this plan.

**Design complete:** the [settings and launch contract](/docs/project/development/milestones/05/scene-settings-contract.md)
records ownership, exact precedence, schema compatibility and an example package.

## 2. Make saved settings work consistently

Implement the agreed resolution across inspection, validation, running, viewing and compilation.
Show effective values and their origins, including which file or override wins. Explain named bundled
versus editable user scenes in diagnostics and guides. A changed user file must be read on the next
launch; commands must never silently persist temporary overrides or modify installed examples.

**Done when:** independent tests cover saved edits, shared configuration, scene overrides, explicit
CLI selection, refinement applied once, package relocation and invocation from another directory.
Equivalent launches resolve identical physics. Existing supported documents retain their meaning
or receive a clear, tested migration path; invalid combinations fail before simulation or output.

**Implemented locally:** the [resolution record](/docs/project/development/milestones/05/scene-settings-resolution.md)
records executable resolution, migration and verification. Scene construction and the remaining
camera and colour rendering work retain their boundaries below.

## 3. Make scenes straightforward to construct

Support multiple named initial particle groups sharing one fluid model. Start with lattices and
explicit particles, then flatten them deterministically for the existing solver. Define identity
assignment, group order, endpoint rules and initial velocities; validate collisions and overlaps
across groups as well as within them. Keep large-scene construction practical.

Add a container-box description using bounds or dimensions and origin, expanded into deterministic
inward-facing planes. Retain explicit planes for advanced inputs. This convenience describes an
enclosing domain; arbitrary solid obstacles need a different collision representation.

**Done when:** one editable example contains two interacting fluid blocks with distinct initial
velocities in a box, without hand-written plane normals. Independently derived tests check counts,
positions, identities, cross-group errors and plane expansion. Equivalent legacy geometry produces
the same resolved solver inputs. Distinct materials, emitters, meshes and moving colliders are deferred.

**Implemented locally:** the [scene-authoring record](/docs/project/development/milestones/05/scene-authoring.md)
records named sources, automatic identities, container expansion, the editable two-block example and
independent verification. The solver still consumes one flattened fluid state.

## 4. Make camera and colour choices persistent and predictable

Automatically load the scene's `render.toml` and provide an explicit action to save the current
interactive camera there. Retain `--render-config` as an optional replacement and define precedence
against CLI overrides. Resolve the scene-local file independently of the invocation directory.
Make `--fit-camera` behaviour the default when no saved or explicitly selected fixed camera takes
precedence, with an explicit way to disable fitting. An explicit fit request must override a saved
camera. Use declared finite scene bounds where available, with safe behaviour for empty or unbounded
scenes. Keep reset, refit, aspect ratio and clipping behaviour understandable; do not continually move
a user's camera without an explicit mode.

Add a presentation setting in `render.toml` for colouring particles by kinetic energy, with a blue
to red gradient from low to high energy. Define the quantity as per-particle kinetic energy
(`½m|v|²`, in joules), using accepted velocities and particle mass. Specify configurable range bounds,
normalisation and clamping so colours remain comparable across frames; retain a fixed-colour option.
This is a visualisation of motion, not temperature, and must not alter solver state or timing.

**Done when:** a camera chosen in the viewer can be saved and reused by viewing and compilation;
small and large scenes start in a usable view without `--fit-camera`; scene-local settings work
without extra flags and survive package relocation. Independent cases check the colour gradient's
endpoints, intermediate energy and clamping, and viewing and compilation use the same mapping.
Presentation changes leave accepted particle state unchanged. Test the supported display paths and
record unavailable hardware checks separately. Existing image-only compilations remain playable;
changing their viewpoint or particle colours would require saved particle frames and new rendering,
so that archive feature is outside this work.

**Implemented locally:** the [presentation record](/docs/project/development/milestones/05/scene-presentation.md)
records domain fitting, explicit camera saves, fixed and energy colours, compatibility and verification.
Viewing and compilation share the accepted-state mapping; existing image-only playback is unchanged.

## 5. Implement meaningful fluid controls

Complete the authoring work first. Then add XSPH velocity smoothing and vorticity confinement as
separate, independently reviewed changes, starting with XSPH. Read the
[registered PBF source](/docs/research/sources/004-macklin-muller-position-based-fluids.md) before
choosing equations, coefficients, units, stage order, neighbour use and timestep dependence. Record
the numerical revision before implementation and verify the serial calculation independently before
qualifying threaded and CUDA execution. Preserve immutable-stage and accepted-state semantics.

Keep both effects disabled by default for existing inputs. Specify useful coefficient domains and
zero/disabled behaviour; adding an accepted boolean alone is not implementation. Explain what each
working control changes, including limits: smoothing is not automatically calibrated physical
viscosity, and artificial pressure must not be presented as a surface-tension material model.

**Done when:** small analytical cases and deterministic interaction scenes demonstrate each effect,
disabled cases preserve the existing numerical results, enabled CPU/CUDA paths agree under the
declared contract, and failures preserve accepted state. Document which controls affect dynamics,
derived/reporting quantities or diagnostics, with usable examples and no unsupported material claims.

**Fluid controls implemented locally:** the [XSPH record](/docs/project/development/milestones/05/xsph-viscosity.md)
and [confinement record](/docs/project/development/milestones/05/vorticity-confinement.md) record the
separate numerical revisions, saved controls and serial/threaded/CUDA verification. Disabled defaults
preserve the historical results. The remaining work is the complete user-journey verification below.

## 6. Verify the journeys and record the result

Exercise creating and editing a scene, inspecting its effective settings, running headlessly, viewing,
saving a camera, compiling and playing saved output. Include relocated packages, malformed inputs,
cross-group geometry failures and legacy scenes and bundles. Playback must not rerun the solver.
Update the maintained Maelstrom guides alongside implementation rather than launching another broad
documentation rewrite.

Retain proportionate small and large workload checks. Run important CUDA, compilation and performance
measurements on the primary PC through `ssh pc`; keep solver, rendering and output costs separate.
New fluid effects do different work and need new comparison identities, not claims of backend speedup.

**Done when:** a concise implementation record links the assessed source, decisions, actual checks,
remaining limitations and any unverified platform paths. Numerical and measurement contracts may
change with evidence, while earlier results remain identifiable and affected comparisons are renewed.
Final evaluation, broad optimisation, particle-frame archives and a full scene editor remain separate.

**Verified locally and on the primary PC:** the [journey record](/docs/project/development/milestones/05/scene-usability-verification.md)
records package creation and relocation, saved fluid controls and camera, native viewing, compilation
and source-independent playback. It also records the decimal-lattice validation correction, tested
feature combinations and remaining platform limits. All six steps are complete within that scope;
The record pins the committed Maelstrom implementation; no phase-completion tag is included.

Follow the applicable `AGENTS.md` and complete one step through verification before moving on.
Choose source organisation and verification commands from the actual change. This plan does not
authorise commits, pushes, tags, branch changes or advancement of the EPQ gitlink.
