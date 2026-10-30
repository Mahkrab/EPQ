# Built-in scene catalogue overhaul

The application now embeds 17 self-contained scene directories. Each contains
`scene.toml`, `config.toml` and `render.toml`, matching the editable user-scene
layout. The [catalogue](/Maelstrom/scenes/README.md) describes the particle counts
and geometry. New examples cover two and four blocks, a released dam, finite
opposing jets, an inclined plane, a two-plane channel, a shallow basin and the
110,592-particle impact workload. The opposing jets enable XSPH viscosity and
vorticity confinement; the other examples retain the default disabled effects.

Every package uses schema 2, inherited particle spacing, deterministic group
identities, a finite container, kinetic-energy colouring in joules and a fitted
camera. Reference is the application's default numerical mode, and every package
saves its 480 Hz, eight-iteration schedule with correction 0.0625 and relaxation 20.
Each scene requests three simulated seconds and a stride of eight, giving 60 Hz
output. Fast remains opt-in through `--numerical-mode fast`; stride four gives
60 Hz at its 240 Hz step rate. The render ranges are fixed display choices, not
physical acceptance thresholds. A scene's editable numerical values remain
available with `--numerical-mode scene`; the two presets override their scheduling
fields unless an explicit `--set` overrides the preset.

The build discovers and embeds all three documents. Inspection, compilation,
viewer setup/reset and `scenes create --from builtin:NAME` resolve the same
presentation. Installed binaries require no source checkout. Tests cover missing
package members, invalid names, duplicate selectors, unsafe references and exact
effective input/presentation agreement between built-in, file and copied forms.

The inclined examples exposed residual floating-point penetration after plane
projection. CPU and CUDA now repair only an outside result, moving the dominant
normal coordinate inward with directed rounding. Strict containment remains in
force. Axis-aligned projection, already-contained results, timestep policies and
solver parameters are unchanged. Independent containment/idempotence tests and
bitwise CPU/CUDA tests cover both normal signs and four CUDA block sizes. The
original flat scenes and companion configurations remain byte-preserved under
`reference/`; frozen manifests and golden hashes are unchanged. Evidence readers
resolve their recorded historical scene paths to those fixtures. An older host
coordination overlay is tested against its frozen pre-optimisation source and
continues to reject the current source rather than silently instrumenting it.

The catalogue originally shipped with fast defaults and stride four. The user-requested
revision on 30 October 2026 selects reference in the application and every package,
including the saved relaxation value in opposing jets. Its velocity effects remain enabled.
The verification and installed-executable identities below describe the earlier catalogue;
they do not verify this default revision.

The default revision passed local `cargo test --locked --offline`, the seven viewer
CLI unit tests with `--features viewer --bin maelstrom`, a viewer-enabled binary
build check and formatting checks. Catalogue tests check every package's saved
numerical values, output stride and copied configuration. CUDA and rendered-runtime
checks were not repeated, and installed executables were not replaced.

Verification is retained in [assets/builtin-scenes-v2](/docs/project/development/milestones/05/assets/builtin-scenes-v2).
The PC runs compile every scene for three seconds at 640×480, 60 Hz in both modes,
validate every completed bundle, and compare the initial two fast frames against
file-loaded inputs with exact frame records (snapshot, PNG and decoded RGBA hashes).
The [contact sheet](/docs/project/development/milestones/05/assets/builtin-scenes-v2/contact-sheet.png)
contains actual application frames at 0.5 seconds. These are catalogue and rendering
checks, not a new physical-quality or performance qualification. Full output bundles
remain in the durable `builtin-scenes-v2` experiment directory on the PC; the receipt
retains frame hashes and command wall times. No speedup is inferred from these runs.

The parallel encoding pipeline, canonical streaming snapshot hashing, both
numerical modes and the ten retained CUDA optimisations remain present. Publication
also includes the previously pending implementation, research records, tooling and
retained experiment evidence requested by the user. Large new binary evidence uses
Git LFS without rewriting earlier history or changing archived measurements.

Verified Maelstrom source: `cf6f3cc883b5c5359ea2e5e67b5af56510ef5977`. The final
all-feature PC suite passed 405 tests with no ignored tests; strict Clippy and
format checks passed. Parent verification passed 16 general and 202 performance
and evidence tests. Both inclined examples also completed their full 720/1,440-step
fast/reference requests on the serial CPU backend. These runs retained the existing
CFL warnings without changing the timestep or acceptance rules.

The installed all-feature executable on the PC and this device has identical
SHA-256 `2bf4d40e040345daea6e97837e4566f51fc48ce4ab27be45f3c99dfba55d6058`,
built from that commit. An installed-PC compile also validates the untouched
1280×720 package defaults. The command-line version remains `0.1.0`; the source
commit and executable hash identify this update.
