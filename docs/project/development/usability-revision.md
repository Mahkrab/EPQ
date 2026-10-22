# Maelstrom usability revision

## Starting point and outcome

The [pre-evaluation review](/docs/project/development/pre-evaluation-review.md) identified confusing
documentation, inconsistent execution flags and a brute-force default that did not suit ordinary
use. This revision implements the [CLI direction](/docs/project/development/cli-design.md) and
[usability plan](/docs/project/development/usability-plan.md), without starting the performance work.

Work began from EPQ `068c0f5597636f8533a7de1e8ce1574d78080eb2` and Maelstrom
[`a881145a373fe2a4c9a25b0ca10f3b89c2b1db9e`](https://github.com/Mahkrab/Maelstrom/tree/a881145a373fe2a4c9a25b0ca10f3b89c2b1db9e).
The earlier planning edits were retained. Implementation and evidence remain uncommitted; the
[verification inventory](/docs/project/development/assets/usability-v1/verification.json) identifies
the assessed working files. Those hashes are not a replacement for an authorised Git checkpoint.

## Decisions that changed the application

`compile` now computes a scene and publishes images once; `run` executes headlessly;
`play` reads completed images. `view` explicitly starts a fresh live simulation and `rerun`
recomputes recorded inputs from zero. Saved-observation export remains `export saved`, because
conversion must never conceal recomputation. CUDA diagnostics sit under `doctor cuda`.
Help contains arguments/options rather than examples. The README and all maintained guides,
including fixture instructions, were reorganised around these journeys; accurate field tables remain.

Fresh commands share one execution selector. The initial `auto` policy honours explicit resources,
otherwise preferring an available CUDA device and falling back to serial grid only before selection.
It does not try to infer hardware-specific crossover thresholds from one historical scene family.
Brute force and threaded grid remain explicit choices. Once selected, CUDA runtime failure does not
silently become CPU work. Records keep concrete execution; reruns do not reselect resources.

Headless execution targets 1x simulated time unless `--unpaced` is requested. An accepted-step callback
places waiting after numerical work and observation, outside solver measurements. It never changes
the timestep or skips work to catch up. Legacy `--execution` requests retain their previous unpaced
behaviour; new measurement requests require `--unpaced`. Parent benchmark tooling now requests it
explicitly. Legacy command/flag spellings remain usable but hidden from the primary help.

User scenes use editable packages with scene-local configuration. Directory flags override
application-specific environment variables, then XDG locations. Duplicate bundled/user names require
an explicit namespace; creation cannot overwrite an existing package. Application preferences select
execution resources, not hidden numerical overrides. Compiled runs occupy a separate durable library.

The existing image manifest already embeds resolved initial geometry, configuration and execution.
Reusing it avoids a competing playback format or a second simulation. Each compilation has a new ID,
an optional label and additive catalogue metadata. Moving a bundle leaves playback and rerun usable
without its original scene library. Partial publication remains explicit and cannot claim completion.

Completion scripts are generated from the actual clap declarations through the stable
`clap_complete` API, avoiding separate command inventories for each shell.<sup><a href="#ref-s059">S059</a></sup>
This adds a narrowly scoped dependency; existing clap colour and TOML writing features are enabled
for diagnostics and editable packages. Unstable dynamic completion is disabled and the lockfile
records the added transitive packages. Default builds still acquire no graphics or CUDA dependency.

## Verification and problems found

Local x86_64 WSL2 checks used Rust/Cargo 1.98.1 and Python 3.12.3. The release headless suite passed
**233 tests**. The viewer suite passed **265**, with its nine opt-in checks run separately rather
than treated as passes while ignored. Formatting, strict Clippy and warning-denying Rustdoc passed.
The parent suites passed **50 tests**, including the new unpaced-collection argument check.
Final preference-domain hardening was followed by focused CLI/bundle tests and strict Clippy;
the inventory distinguishes the native-installation source from those final working files.

New public-command tests cover storage precedence, naming collisions, deterministic discovery,
scene creation, working-directory independence, execution preferences, pacing/result invariance,
resource errors, old-record rerun and example-free help. The software-Vulkan bundle check covers
creation, relocation, removal of original scene inputs, rerun, image hashes and corruption rejection.

The first scene-package test rejected an inspection-only derived field: canonical inspection is not
an input document. Creation was corrected to serialise resolved primary values only. An ID test also
caught OS-string JSON representation rather than a plain ID string. Both now pass. Old assertions
requiring obsolete help/defaults were updated deliberately; numerical and publication checks remain.

An isolated installation exercised scene creation/inspection, explicit execution, exact numerical
rerun and compilation through the installed command. Native WSLg/Xwayland viewer and saved-player
journeys passed, including controls, failures, resize and shutdown; playback left all bundle files
unchanged. The first window attempt used a headless target binary left by another feature build and
failed explicitly. Repeating through the isolated viewer installation removed that build ambiguity.

## Limits and handoff

No solver kernel, numerical default, fixture or golden changed. Pacing and these verification-job
durations are not performance measurements. CUDA hardware execution, hardware Vulkan, other
platforms and hosted checks were not freshly qualified. The separate scaling concerns remain open.

No commit, tag, branch change, push, global installation or parent-gitlink advancement was performed.
An authorised implementation-first checkpoint is still needed before these working files become
immutable source evidence. Final comparative evaluation has not begun.

## References used

<a name="ref-s059"></a> **S059** — clap contributors, *clap_complete*, version 4.6.11.
[Source record](/docs/research/sources/059-clap-completion-generation.md).
