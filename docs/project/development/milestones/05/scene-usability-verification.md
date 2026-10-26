# Scene usability verification

## Starting point and outcome

This completes the local implementation and functional verification of Phase 02's
[scene-usability plan](/docs/project/development/milestones/05/scene-usability-plan.md).
The starting commits remain EPQ `812dea60d8527b8ed977c6bd5d865199397aa374` and Maelstrom
[`4a9675b5f9e3b7aa90335f5a77bdb3e82093a1b5`](https://github.com/Mahkrab/Maelstrom/tree/4a9675b5f9e3b7aa90335f5a77bdb3e82093a1b5).
They do not contain this work. The assessed implementation is Maelstrom
[`87145510a9e5d812066138c35f1fac82e4f593b0`](https://github.com/Mahkrab/Maelstrom/tree/87145510a9e5d812066138c35f1fac82e4f593b0),
which EPQ now pins through its gitlink. Verification ran before that commit; the retained
[source hashes](/docs/project/development/milestones/05/assets/scene-usability-validation-v1/source-sha256.json)
match its committed files. Recorded binary identities distinguish the executables actually tested.

An editable package now carries its geometry, numerical controls, run limit and presentation choices
through inspection, headless execution, viewing and compilation. Saved images play independently of
the source package and simulation backend. The preceding records own the
[settings contract](/docs/project/development/milestones/05/scene-settings-contract.md),
[resolution](/docs/project/development/milestones/05/scene-settings-resolution.md),
[authoring](/docs/project/development/milestones/05/scene-authoring.md),
[presentation](/docs/project/development/milestones/05/scene-presentation.md),
[XSPH](/docs/project/development/milestones/05/xsph-viscosity.md) and
[confinement](/docs/project/development/milestones/05/vorticity-confinement.md) decisions.

## What the complete journey found

A translated lattice with 0.025 m spacing resolved on its own but failed when placed in a group.
The extra overlap check compared rounded binary32 world coordinates with nominal spacing and
incorrectly rejected particles 420 and 440. The regression reproduced this before the correction.

Lattices now use their existing construction and strictly increasing-axis validation internally.
The spatial check still validates explicit particles and every cross-group pair. No coordinates,
solver equations, existing separation margin or numerical reference outputs changed. Tests compare
complete standalone/grouped particle vectors and still reject cross-group overlaps, explicit overlaps,
coordinate collapse and accidental extension of a lattice exemption into another source.

The combined viewer/CUDA test build also exposed missing colour and mass values in a rendering
fixture. These now come from the default palette and resolved scene mass before ownership transfers
to the worker. The actual CUDA-to-rendering check passed. The input and usage guides were corrected
where they still described particle-only fitting or required repeated run-limit flags.

## Verification

The primary PC ran an isolated source copy: Ryzen 9 7900X, RTX 4070, driver 610.88, CUDA 13.3.73,
Rust 1.96.0 and WSL2. All 175 source/input hashes matched the laptop; the compiled source identity
also matched the current implementation. Graphics used hardware OpenGL/D3D12 and software Vulkan.
[Commands and checks](/docs/project/development/milestones/05/assets/scene-usability-validation-v1/checks.json),
[environment](/docs/project/development/milestones/05/assets/scene-usability-validation-v1/environment.json),
[exact inputs](/docs/project/development/milestones/05/assets/scene-usability-validation-v1/inputs.json) and
[results](/docs/project/development/milestones/05/assets/scene-usability-validation-v1/summary.json) are retained.

| Journey | Observed result |
| --- | --- |
| Create, edit and relocate | CLI-created package accepted saved numerical/run/render edits; relocation preserved effective values without repeated physics or camera flags |
| Small and large execution | 128, 20,000 and 110,592 particles each completed six CUDA steps with both fluid effects enabled and no CFL warnings |
| Compile | Each workload produced four validated images at steps 0, 2, 4 and 6; final snapshot hashes matched separate headless execution |
| Native viewing | The 20,000-particle scene opened paused, stepped, orbited, saved/restored its camera, completed and closed; physical input files stayed unchanged |
| Camera reuse | Inspection and compilation reloaded the camera saved by S, preserving energy colours and unrelated presentation settings |
| Portable playback | After deleting the source packages, a CPU-only executable played the copied CUDA-produced bundle through hardware and software graphics; controls worked and bundle hashes stayed unchanged |
| Invalid and legacy inputs | Geometry/schema rejection, failed-publication preservation, historical numerical references and saved-format compatibility passed; a deliberately corrupted image was rejected |
| Rust regression suite | 334 passed across 35 targets with viewer/CUDA enabled; 42 device checks remained opt-in |
| Explicit integration | 44 scene/settings checks and eight graphics/export checks passed when selected, including the combined CUDA/rendering fixture |
| Local checks | 36 headless checks passed on Rust 1.98.1; strict Clippy, Rustdoc, formatting and local documentation checks passed |

Native [screenshots](/docs/project/development/milestones/05/assets/scene-usability-validation-v1/native-viewer/completed.png)
show the complete box and both blocks; the saved/restored-camera images were byte-identical. The diagnostic panel was hidden for the
particle captures using its existing H control. Playback ran at 0.01× because the six-step sequence
lasts only 0.0125 simulated seconds: the first 1× probe finished before it could observe a playing
state. Slowing playback changed neither saved timestamps nor images. Earlier failed probes and the
pre-correction lattice failures are retained; no failed attempt has been relabelled as a pass.

These are short functional checks. Solver, graphics/readback and encoding durations are retained
separately, but qualification work could overlap. They are not controlled performance comparisons,
long-running stability results or a new permanent benchmark family.

## Limits and checkpoint status

The six planned steps are implemented and verified within the stated environment. Hardware Vulkan,
native Wayland, other operating systems, hosted checks and new physical-accuracy claims remain
unqualified. Particle-frame archives, distinct materials and a full scene editor remain outside scope.

The implementation and this record are committed on `phase/05-02-scene-usability` in their respective
repositories, with Maelstrom committed first and the EPQ gitlink pinned afterwards. No branch merge,
new tag or milestone-wide gate decision is included. Git publication does not establish hosted
verification; the checks above ran on the named local devices.
