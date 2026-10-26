# Initial particle groups and container authoring

## Scope and state

This records the scene-construction work for Phase 02, following the
[scene-usability plan](/docs/project/development/milestones/05/scene-usability-plan.md) and
[settings resolution](/docs/project/development/milestones/05/scene-settings-resolution.md).
It extends the uncommitted implementation on `phase/05-02-scene-usability`.
Maelstrom's committed baseline is
[`4a9675b5f9e3b7aa90335f5a77bdb3e82093a1b5`](https://github.com/Mahkrab/Maelstrom/tree/4a9675b5f9e3b7aa90335f5a77bdb3e82093a1b5);
EPQ remains at `812dea60d8527b8ed977c6bd5d865199397aa374`. Neither commit contains this work,
and no completion checkpoint is claimed.

## Authoring decisions and implementation

Schema 2 now accepts named groups of initial particles and an enclosing box. Existing single-source
scenes retain their construction rules. Groups share one fluid model; they are an easier way to
specify initial state, not separate materials or a change to the timestep solver.

| Decision | Behaviour |
| --- | --- |
| Group format | `construction = "groups"` with `[[particles.groups]]`; each named table is a flat lattice or explicit source |
| Order | Preserve document order, including the established X/Y/Z lattice order; never sort by group name |
| Identity | Omitted lattice starts continue after the preceding particle, beginning at zero; explicit identities and starts remain authoritative and globally ascending |
| Limits | At most 256 groups and one million total particles; empty explicit groups consume no identities |
| Validation | Reject duplicate/blank names, nested groups, non-finite state, identity conflicts, overlaps and invalid geometry before solver setup |
| Box | Select `min_m`/`max_m` or `origin_m`/`dimensions_m`; reject mixed forms, invalid extents, overflow and rounding collapse |

Standalone schema-2 lattices can also omit their initial identity and start at zero. Schema 1 still
requires an explicit start and spacing, and rejects group and container fields. Newly created copies
retain their authoring groups and box while removing validated spacing assertions from every lattice.
Inspection reports group names and the expanded planes. Recorded inputs remain the existing flattened
particle and plane representation, independent of the original files.

The box generates six inward half-spaces in X-minimum, X-maximum, Y-minimum, Y-maximum,
Z-minimum, Z-maximum order. Explicit planes follow and intersect that domain, counting towards the
same 32-plane limit. Bounds refer to particle centres, preserving the existing projection model.
This is an enclosing container, not a finite solid obstacle.

Grouped sources use fixed spatial cells to validate separation within and across groups. Neighbouring
cells and stored particle indices are visited in fixed order; the hash table is never iterated.
An error identifies the first overlapping particle in flattened order and its lowest earlier partner.
Exactly coincident points require the explicit coincidence option; retaining their first representative
avoids repeatedly checking identical positions. Signed 64-bit cell coordinates are checked before
conversion. Legacy standalone explicit validation remains unchanged, including its 4,096-particle cap;
grouped explicit inputs use the new check and share the aggregate limit.

## Editable example and equivalence

The bundled `two-blocks` scene contains two 4×4×4 lattices, with initial X velocities of +0.25 and
−0.25 m/s. They start at `[0.1, 0.25, 0.1]` and `[0.55, 0.25, 0.1]` m, use 0.05 m spacing and
occupy a box from `[0, 0, 0]` to `[0.8, 0.7, 0.6]` m. Identities are 0–63 and 64–127.
Its shared configuration selects refinement four and its saved limit is one simulated second.
`scenes create NAME --from builtin:two-blocks` makes an editable package.

The example's initial particles, planes and comparison key match an independently written schema-1
scene. A 480-step serial-grid run completes and brings particles from the two blocks into kernel
support. The example is a usability fixture, not a replacement benchmark or new reference scene.

## Verification

Local WSL2 verification with Rust 1.98.1 passed 298 tests across 32 viewer-enabled targets.
This includes the established numerical and golden regressions. Thirteen device checks were ignored
in that run; the new grouped-scene compilation check and four existing export checks were then run
explicitly and passed using software Vulkan, llvmpipe LLVM 20.1.2. The new image bundle validates
after its source scene files are removed. These results do not qualify a native window or CUDA hardware.

Headless integration checks passed 40 tests. Strict Clippy passed with and without viewer support;
Rustdoc passed with broken internal links denied. The parent Markdown tests, document links and
whitespace review also passed. Independent checks list expected positions and planes, compare overlap
decisions with an all-pairs calculation, exercise identity and count limits, and construct 100,000
particles. That construction check is not a simulation-capacity or performance benchmark.

## Boundary

Numerical equations, solver ordering, CPU/CUDA kernels and historical benchmark inputs are unchanged.
No performance result or CUDA hardware qualification is claimed. Full-domain camera fitting, camera
saving and colour rendering remain the presentation work. Distinct materials, emitters, mesh geometry
and moving colliders remain outside this change.

The subsequent [presentation record](/docs/project/development/milestones/05/scene-presentation.md)
covers the implemented camera persistence, domain fitting and particle colours.
