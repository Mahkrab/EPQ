# Application evaluation and final-comparison handoff

## Outcome and assessment boundary

The application makes accepted particle states inspectable during a run and produces saved PNG
sequences that can be watched without repeating the simulation. Its contribution is an interaction
and reproducibility workflow. It changes neither the fluid model nor the meaning of the existing
backend measurements. The [application contract](/docs/project/development/milestones/04/application-contract.md)
owns the behaviour; the [verification inventory](/docs/project/development/milestones/04/assets/evaluation-v1/README.md)
identifies fresh commands, source hashes, device context and results.

The assessed implementation is Maelstrom
[`a881145a373fe2a4c9a25b0ca10f3b89c2b1db9e`](https://github.com/Mahkrab/Maelstrom/tree/a881145a373fe2a4c9a25b0ca10f3b89c2b1db9e).
Local guide corrections remove an obsolete claim that export is unavailable and clarify existing
camera, feature-build and size limits. No solver,
renderer, dependency, fixture, numerical policy or benchmark changed during this assessment.
The checks were collected against `9336ee42104badb1b5e439edc1df5e8488c32987`; only the three
reviewed guides changed in the completion commit. The source links below retain that tested code.
Local annotated completion checkpoints now retain the guides, exact EPQ gitlink and evidence;
the original collection inventories remain unchanged. Publication is separate.

## Contract assessment

| Responsibility | Evidence and judgement | Qualification limit |
| --- | --- | --- |
| Interaction and usability | The real-window journey exercises paused launch, stepping, warnings, camera/audit, run/pause, reset, draft editing, completion, invalid selection, CPU mode changes, failed CUDA selection, prior-outcome inspection, surface recreation, resize/minimise and close during work. The separate saved-player journey checks seeking, speed, pause/resume, endpoints and resize. | Scripted native events and captured windows establish these journeys, not a user study, accessibility assessment or response-time bound. |
| Lifecycle and failure retention | [Controller tests](https://github.com/Mahkrab/Maelstrom/blob/9336ee42104badb1b5e439edc1df5e8488c32987/tests/application_lifecycle.rs) cover receipts, exact step counts, stale generations, bounded admission, latched cancellation, setup failure, rollback and teardown. Fresh PC tests construct, step, restart and destroy CUDA on its owning worker. | Cooperative cancellation waits for synchronous stages. Process abort and hung drivers cannot promise retained output or a shutdown deadline. |
| Numerical independence | [Viewer checks](https://github.com/Mahkrab/Maelstrom/blob/9336ee42104badb1b5e439edc1df5e8488c32987/src/viewer/tests.rs) vary cadence, camera, draft, reset and audits against direct headless results. CPU modes preserve accepted bits; PC checks compare worker-owned CUDA observations with direct execution. | Tested inputs and devices establish independence; pixels do not prove physical accuracy or qualify a different compiler/device. |
| Offline reproducibility | [Export integration checks](https://github.com/Mahkrab/Maelstrom/blob/9336ee42104badb1b5e439edc1df5e8488c32987/tests/export_device.rs) compare direct, saved and rerun observation hashes and independently decoded pixels. They include the frozen small lattice and refined 480-step falling block, sparse/partial histories, empty/single-particle inputs and known projection geometry. | Repeatable decoded RGBA is qualified for the same binary, adapter/driver, observations and settings. Cross-driver pixel equality is not promised. |
| Publication and recovery | Exclusive destinations and no-replacement frame/manifest publication retain prior data. Fault tests exercise cancellation, encoding/readback failure, output/progress errors, mismatch evidence and process interruption after initial publication. Only the final manifest claims completion. | Hard links are required. Injected device destruction is not actual hardware loss; crash durability, automatic cleanup and resumption are not provided. |
| Saved-image independence | [Playback checks](https://github.com/Mahkrab/Maelstrom/blob/9336ee42104badb1b5e439edc1df5e8488c32987/src/playback/tests.rs) load synthetic pixels even with unusable physical inputs and an unavailable recorded CUDA ordinal. Missing/altered images, invalid schedules and unsafe names fail without reconstruction or writes. Real playback leaves every input file unchanged. | Decoding is on demand. Late display may skip recorded images; full frame coverage is available by seeking, rather than guaranteed at every playback speed. |

### Decisions and actual findings

The [lifecycle record](/docs/project/development/milestones/04/phases/phase-00-application-lifecycle.md)
explains the worker boundary. The latest-observation slot lets a slow viewer release intermediate
states without backpressuring the solver. Generations isolate replacements and old handles retain
outcomes. That slot cannot support lossless export: the exporter instead acknowledges each selected
frame synchronously before advancing. This simple ownership choice keeps CUDA construction and
destruction together and bounds particle-state storage, at the cost of delaying export for every
draw, readback and publication. It adds no zero-copy graphics interoperability claim.

The completion manifest makes the output reconstructable: it retains physical inputs, resources,
accepted-step mapping, observation/image hashes, render settings, camera, source/lock/shader identities
and independent graphics context. A partial prefix can form a complete image sequence while retaining
the original run's failure. It must never be described as completion of that original request.

Earlier implementation work diagnosed a Linux X11 native-library requirement and retained the initial
failed launch. The playback record also retains an unexplained initial key-seek timeout and a launch
of a binary built without playback. Those attempts remain failures, with later successful evidence
identified separately. This review corrected the stale no-export sentence in the controller guide.
A fresh live-window attempt also timed out on its first step key and closed cleanly; its raw failure
is retained. Inspection of the locked winit X11 event path showed that core key delivery requires an
active focused window, which the native harness had not established. The harness now requests and
verifies focus on its own process window before sending keys, matching the documented click-to-focus
journey. Unit checks cover refusal when focus is unavailable and addressed press/release delivery
when it is. The application itself still leaves existing keyboard focus alone. No production-code
change was needed.

The [offline evidence](/docs/project/development/milestones/04/assets/offline-v1/README.md) exposes a
useful presentation limitation: fitting the initial falling block can clip its later motion. A wider
explicit fixed camera addresses that journey without modifying physics. Plane outlines depict infinite
constraints clipped to a display box, and blue spheres with fixed lighting are particle markers.
They are neither a reconstructed fluid surface nor a measurement of pressure or density. Empty scenes,
very large dynamic ranges, clipping and display precision still need deliberate camera choices.

## Supported use and recovery

Use the [assessed usage guide](https://github.com/Mahkrab/Maelstrom/blob/9336ee42104badb1b5e439edc1df5e8488c32987/docs/usage.md),
[viewer guide](https://github.com/Mahkrab/Maelstrom/blob/9336ee42104badb1b5e439edc1df5e8488c32987/docs/viewer.md)
and [export/playback guide](https://github.com/Mahkrab/Maelstrom/blob/9336ee42104badb1b5e439edc1df5e8488c32987/docs/export.md)
for complete settings and controls. From the EPQ root, these locked builds select distinct capabilities:

| Build | Capability and requirements |
| --- | --- |
| `cargo build --release --locked --manifest-path Maelstrom/Cargo.toml` | CPU solver, ordinary CLI and non-visual controller; no graphics initialisation, display or CUDA toolkit. |
| Same command with `--features render` | Windowless PNG export; Vulkan loader and selected compatible graphics device still required. No winit window dependency. |
| Same command with `--features viewer` | Live viewer, PNG export and saved-image playback; qualified on x86_64 WSL2 Linux with WSLg and explicit llvmpipe software Vulkan. Linux X11 also needs the documented keyboard libraries. |
| Same command with `--features cuda,viewer` | Adds new CUDA simulations; requires the documented CUDA/host build tools and supported runtime device, independently of graphics. Set `CUDA_HOME=/usr/local/cuda` when needed. |

The following **starts a fresh simulation**, paused at zero. Space runs/pauses, N steps, R resets,
C cancels, F fits and Escape closes. Tab/Enter edit a draft and A validates/applies it as a new run.

```sh
Maelstrom/target/release/maelstrom view falling-block-04 \
  --refine-timestep 4 --steps 480 --mode serial-grid --software
```

The following **loads saved observations**, with no numerical rerun. Its sparse stride selects the
stored steps 0, 240 and 480 rather than inventing intermediate states. Choose a new output directory.

```sh
Maelstrom/target/release/maelstrom export saved Maelstrom/reference/falling-block-v1.json \
  --step-stride 240 --render-config docs/project/development/milestones/04/assets/offline-v1/wide-camera.toml \
  --software --output frames-saved
```

With the viewer build, this **loads already rendered images**. Space pauses/resumes, Left/Right seek
and pause, Home/End select endpoints, +/- change speed, R restarts and Escape closes.

```sh
Maelstrom/target/release/maelstrom play frames-saved --software --paused
```

`replay` and `export rerun` start again from recorded initial inputs and execution resources; neither
resumes a final snapshot. Saved observations can be drawn without their original CUDA device, and a
copied PNG sequence can be played without a solver. Hardware Vulkan is the default graphics class;
`--software` explicitly selects the qualified software class. There is no silent simulation fallback.
Cargo feature builds share the target executable name, so a later headless/render-only build can
replace a viewer binary; rebuild with `viewer` if `view` or `play` is absent.

After invalid draft validation the selected run remains inspectable. After resource setup failure,
O shows the labelled prior accepted outcome; correct the draft and apply a new generation. For an
incomplete export inspect `progress.json` and retained comparison evidence, preserve the directory,
then retry to a new destination. Do not rename progress into a completion manifest. For corrupt
playback restore the original hashed sequence or explicitly export again from available observations.
Sparse results need an explicitly selected rerun to obtain missing states. Render settings are strict
schema 1, independently merged as defaults, explicit file, then CLI overrides; they do not change
physical input identity. Export allows at most one million frames, while playback also imposes a
64 MiB manifest limit: the frame-count ceiling alone does not qualify that many playable frames.

## Costs and evidence limits

No new performance samples were collected. The retained check durations measure verification jobs
and must not supply application throughput claims. The existing solver campaigns remain owned by
their original protocols and machines.

| Cost | Current boundary | Interpretation |
| --- | --- | --- |
| Solver construction and steps | Headless measurements separate construction/destruction from completed transactional steps. CUDA step calls include the synchronous transfers and host checks they perform. Export's `solver_steps` wraps stepping only. | The export diagnostic is not a new matched benchmark. Saved-only export performs no numerical steps. |
| Snapshot transport and conversion | The live worker clones accepted host snapshots. Export captures portable observations, including on unsampled steps during direct/rerun execution. Rendering creates display buffers without changing source particles. | Copies, packing, hashing, comparisons and transport are not individually timed. They cannot be inferred from the solver total. |
| Independent audits | Headless checkpoint density audits and the viewer's requested audit operate outside solver measurement. The viewer labels audit generation and step. | Audit completion must not be attributed to the latest displayed state after a restart. |
| Graphics and encoding | Export `graphics_readback` covers drawing/readback; `encoding` covers PNG encoding. Both are synchronous local diagnostics. | Snapshot conversion before drawing, hashing, file sync/link publication and progress/manifest work are outside those two fields. Their sum is not total application time. |
| Total application and display | The viewer displays redraw FPS. Export completion also includes setup, copies, comparisons, files and teardown. | No total application benchmark, copy profile, memory peak, input-latency study or real-time guarantee was obtained. Solver steps/s is not display FPS. |

Fresh local checks qualify software Vulkan and real WSLg Xwayland windows. Fresh primary-PC checks
qualify the RTX 4070 CUDA worker plus independent software Vulkan drawing/export, without a PC
interactive display journey. The earlier [8,000-particle capture](/docs/project/development/milestones/04/assets/pc-export-v1/README.md)
retains 480 accepted CUDA steps, 481 images and laptop transfer/playback evidence; it is not an
independent numerical comparison or benchmark. Hardware Vulkan presentation/export, native Windows,
macOS, browsers, alternate graphics APIs, other CUDA devices and zero-copy CUDA/graphics sharing
remain unqualified. Previously unavailable Compute Sanitizer checks remain unavailable; successful
application tests do not turn them into passes. Hosted CI/rendering was not performed here.

## Final comparative-evaluation handoff

The next evaluation should retain the following controls and evidence rather than turn attractive
images into a new acceptance test:

| Item to retain | Authority and use |
| --- | --- |
| Four numerical controls | Keep serial brute force, serial grid, threaded grid and CUDA independently selectable. Preserve recorded workers, ordinal, block size and arithmetic identity; a display's adapter is a separate resource. |
| Exact frozen requests | The [reference manifest](https://github.com/Mahkrab/Maelstrom/blob/9336ee42104badb1b5e439edc1df5e8488c32987/reference/manifest.json) identifies `falling-block-refined-v1`: axis counts 4/6/8/10/12/16/20, hence 64/216/512/1,000/1,728/4,096/8,000 particles; defaults-v4, factor-four refinement, eight Jacobi iterations, 480 steps, checkpoints 0/1/120/240/480. The separate 27-particle unforced lattice uses 12 unrefined steps and checkpoints 0/1/4/12. The editable playground's experimental pressure setting is outside this family. |
| Numerical acceptance | Preserve the [numerical contract](/docs/project/development/milestones/00/phases/phase-00-design-contract.md) and [comparison policy](/docs/project/development/milestones/00/reference-verification.md): binary32 state, stable identities/order, strict support, immutable Jacobi stages, ordered planes, atomic acceptance and rollback. Serial/grid comparisons remain exact including signed zero. Parallel budgets and exact structural/status/warning requirements remain owned by that policy; prior exact results do not authorise changing tolerances. |
| Paired historical campaigns | Retain the [brute-force/grid campaign](/docs/project/development/milestones/01/assets/performance-comparison-pc-v1/README.md), [worker scaling campaign](/docs/project/development/milestones/02/assets/performance-scaling-pc-v1/README.md), [CUDA qualification](/docs/project/development/milestones/03/assets/solver-v1/README.md) and [matched CUDA/CPU campaign](/docs/project/development/milestones/03/assets/performance-comparison-pc-v1/README.md), including raw failures, profiles, hashes and verifier outputs. Do not multiply ratios from different campaigns or present the fixed twelve-worker CUDA control as each input's best CPU setting. |
| Timing and provenance | Use the primary PC for important new measurements and declare workload/timer boundaries before collection. Preserve compiler, flags, hardware/driver, input hashes, source identities, warm-ups, repetitions, spread and accepted warnings/status. Rendering, audits, output and copies need their own measured scope for application claims. |
| Application evidence | Preserve the accepted-state/output contract, initial/final frame mapping, saved/rerun distinction, physical/render identities and partial/completion manifests. Re-rendering on a new driver requires image qualification separately from numerical acceptance. |

The [handoff integrity report](/docs/project/development/milestones/04/assets/evaluation-v1/handoff-integrity.json)
checks 55 existing numerical/input/timing files byte for byte against the CUDA campaign revision,
all 431 files named by its two evidence integrity manifests, and all 11 frozen input/golden hashes.
It establishes retention, not a fresh re-analysis of all historical numerical observations or statistics.

The genuine remaining research gap is a final synthesis under the research question, including an
explicit decision about whether historical paired campaigns suffice or a new common-build four-way
campaign is needed. Existing campaigns use separate historical builds and controls, one PC, one main
scene family, fixed collection order and limited repetitions. Scheduling, thermals and shared host
activity limit generalisation; larger/adversarial families, working-set limits and physical validation
remain unmeasured. Those limitations must remain visible. This handoff starts no new optimisation,
numerical variant or unrestricted comparison campaign.
