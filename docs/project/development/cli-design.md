# Maelstrom CLI and storage direction

## Agreed direction

This records the interface for the [usability revision](/docs/project/development/usability-plan.md).
The [implementation record](/docs/project/development/usability-revision.md) owns current verification
and checkpoint limitations. The user specified `compile`, headless `run`, saved
`play`, named user scenes, standard output storage, `doctor cuda` and help without examples.
The supporting commands, flags and storage rules below are project decisions. They do not
change the numerical model or require a new geometry type.

| Command | Responsibility |
| --- | --- |
| `maelstrom compile <scene>` | Simulate once and publish a portable, pre-rendered playback bundle |
| `maelstrom run <scene>` | Execute a live headless simulation, without producing a playback bundle by default |
| `maelstrom play <run>` | Display a compiled bundle by run ID or explicit path; never rerun physics or render particles |
| `maelstrom view <scene>` | Start a fresh simulation with live visualisation; never imply saved playback |
| `maelstrom rerun <result-or-run>` | Explicitly recompute recorded inputs from step zero; not resume or playback |
| `maelstrom scenes list` | List bundled and user scenes with origin and particle count |
| `maelstrom scenes create <name>` | Create an editable user-scene package; `--from <scene>` copies a starting scene |
| `maelstrom inspect <scene>` | Show resolved geometry, configuration, provenance and execution selection without stepping |
| `maelstrom validate <scene>` | Validate a scene and its referenced inputs without simulation |
| `maelstrom runs list` | List compiled runs, their locations and completion status |
| `maelstrom runs show <run>` | Show recorded inputs, execution, duration, frame schedule and outcome |
| `maelstrom runs validate <run>` | Check bundle schema, referenced files and integrity without simulation |
| `maelstrom doctor [cuda\|graphics]` | Diagnose installed capabilities; no fluid simulation or implicit installation |
| `maelstrom config show` | Show effective application preferences and their origin, not silently override scene physics |
| `maelstrom paths` | Print resolved scene, run and application-configuration locations |
| `maelstrom completions <shell>` | Print shell completion definitions without modifying shell configuration |

Keep `--help`, `help <command>` and `--version`. Help at every level contains purpose, arguments,
options, defaults and subcommands, but **no examples**. Examples belong in the guides. A CPU-only
installation must still explain missing CUDA/graphics capabilities through `doctor` and actionable
errors, rather than making feature discovery depend on guessing build flags.

## Execution and flags

Use the same flag names and meanings wherever applicable; do not expose separate `--mode` versus
`--backend` or `--workers` versus `--threads` dialects.

| Commands | Flags |
| --- | --- |
| Global presentation | `--format text\|json`, `-q/--quiet`, `-v/--verbose`, `--color auto\|always\|never` |
| Storage lookup | `--scenes-dir <path>`, `--runs-dir <path>` |
| Fresh simulation and input inspection | `--config <file>`, repeatable `--set <field=value>`, `--refine-timestep <N>` |
| Execution selection | `--backend auto\|brute-force\|serial-grid\|threaded-grid\|cuda`, `--threads <N>`, `--device <N>`, `--block-size <N>` |
| Simulation limits | Exactly one of `--steps <N>` or `--duration <simulated-seconds>` |
| Headless run | `--unpaced`, `--output <result.json>`, `--checkpoints <steps>`, `--snapshot <file>` |
| Compilation | `-o/--output <directory>`, `--name <label>`, `--frame-stride <steps>`, `--render-config <file>`, `--width <pixels>`, `--height <pixels>` |
| Viewing and playback | `--paused`; playback also has `--speed <factor>` and `--repeat` |
| Graphics selection | `--graphics-adapter <N>`, `--software`; independent of the CUDA simulation device |
| Headless measurement | Retain `--measure` and `--stage-profile`; require `--unpaced`, and keep correctness audits outside the solver timer |
| CUDA diagnostics | `doctor cuda --device <N> --repetitions <N>` retains explicit device selection and repeated resource checks |

Default ordinary execution to `auto`, with the selected backend/resources reported and recorded.
The initial policy honours resource constraints, otherwise preferring available CUDA and then serial
grid. It uses no tuned workload threshold and does not claim to find the fastest backend.
Explicit resource flags constrain automatic selection and must not be
ignored. Explicit CUDA cannot silently fall back after failure. Benchmarks name their backend and
resources explicitly; reruns restore recorded execution, never resolve `auto` afresh.

Interpret the requested real-time headless `run` as paced to simulated time at 1x by default.
`--unpaced` runs as fast as possible; compilation is unpaced. Pacing must not change fixed timesteps,
solver iterations or accepted states. If computation falls behind, report lag without dropping solver
steps or promising real-time throughput. Keep pacing waits outside solver measurements.
Finite runs require an explicit limit. Preserve cooperative interruption, meaningful non-zero failure
exits and labelled partial outcomes; quiet output must not hide errors.

`run --output` saves numerical results, not a playable compiled bundle. `compile` guarantees the
opposite journey: later `play` needs neither simulation nor particle rendering. Preserve an explicit
saved-observation export route, `export saved`, so existing results can be rendered without
recomputation rather than disguising a rerun as conversion. No deletion, overwrite
or automatic post-compilation launch is implied by these commands.

## Scene and application storage

Use XDG user data and configuration roots on supported Linux/WSL systems. Their unset/empty defaults
are `~/.local/share` and `~/.config` respectively.<sup><a href="#ref-s058">S058</a></sup>
The following Maelstrom subdirectories and overrides are project choices:

| Purpose | Environment override | Default |
| --- | --- | --- |
| User scenes | `MAELSTROM_SCENES_DIR` | `$XDG_DATA_HOME/maelstrom/scenes` |
| Compiled runs | `MAELSTROM_RUNS_DIR` | `$XDG_DATA_HOME/maelstrom/runs` |
| Application preferences | None required initially | `$XDG_CONFIG_HOME/maelstrom/config.toml` |

Root selection is explicit directory flag, then non-empty Maelstrom environment override, then XDG
location. Require absolute environment overrides; resolve relative CLI paths once against the
invocation directory. Environment variables locate libraries, not hidden numerical settings. The
preferences file stores execution choices but must not silently retune scene physics. Presentation
settings remain explicit through `--render-config`.

Store each user scene as `<scenes-root>/<name>/scene.toml` with its numerical `config.toml` and any
supported geometry/assets alongside it. Keep existing plane and particle representations; add no
mesh formats merely to create a folder convention. Resolve scene-owned references relative to the
scene document, not the shell's working directory. Scene creation copies bundled inputs rather than
editing installed defaults. Creating names or packages must reject traversal and existing targets.

Accept explicit scene paths independently of the library. Named lookup searches user and bundled
scenes deterministically; duplicate names produce an ambiguity error with explicit `user:<name>`
and `builtin:<name>` choices rather than silent shadowing. List origins and resolved paths. Discovery
does not create directories or depend on filesystem iteration order.

## Compiled-run storage and compatibility

Publish each compilation to a new `<runs-root>/<unique-id>/` directory unless `--output` is given.
The optional name is a label, not permission to overwrite. Resolve IDs exactly; duplicate labels
require an ID/path. Print the resulting ID/path and completion status, keeping structured stdout
parseable and progress on stderr. Do not use a cache directory for durable user output.

The versioned bundle contains a manifest, rendered frames and sufficient resolved scene/configuration
and source-asset provenance to identify and rerun the request. Copy required inputs or embed their
resolved values so moving the bundle does not depend on the original scene library. Record numerical
outcome separately from image-publication completeness, effective execution, simulated timestamps,
frame mapping and integrity hashes. Partial/cancelled output stays labelled; it cannot masquerade as
a completed compilation. Do not store absolute source-machine paths as required playback references.

Retain existing result and image-manifest readers. Decide migration/deprecation for `cuda-check`,
the old `scenes`, `replay`, execution flags and export commands before removal; compatibility aliases
must not clutter primary help. Legacy `--execution` requests retain unpaced behaviour; new commands
use the declared pacing/measurement rules. Keep numerical and publication guarantees, test malformed and moved
bundles, and verify saved playback without a CUDA device or access to the original scene directory.
These are acceptance requirements; the implementation record distinguishes verified paths from
unavailable environments and uncommitted work.

## References used

<a name="ref-s058"></a> **S058** — Bastian et al. (2021), *XDG Base Directory Specification*, version 0.8.
[Source record](/docs/research/sources/058-xdg-base-directory-specification.md).
