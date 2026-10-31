# Published-equation PBF comparison evidence

The [numerical contract and assessment](/docs/project/development/milestones/05/performance-paper-baseline.md)
owns the equations, assumptions and decision. This campaign adds `paper-baseline` independently of
reference, fast and experimental; their existing behaviour and the earlier PBF calibration record
remain intact. Source, timings and diagnostics are local/primary-PC evidence, without commits,
remote publication or hosted verification.

The durable primary root is `/home/oliver/.local/share/maelstrom-experiments/paper-baseline-v1` on
`ssh pc`; its local analysis root is `/home/mahkrab/.local/share/maelstrom-experiments/paper-baseline-v1`.
The sealed local raw copy is in `retained/` beside this index. The isolated executable is `target/release/maelstrom` under the primary root. The installed binary,
existing PC checkout, Git histories and system settings were not replaced.

## Inputs, controls and rendering

`initial-*-state.txt`, `initial-*.patch` and `initial-source-hashes.json` identify the already dirty
starting workspace. `implementation.patch`, `source-manifest.json` and `environment.json` identify
the final assessed input source and executable. `native-preservation.json` checks all 13 native
production files against the initial workspace; `infrastructure-preservation.json` also checks the
CUDA host, renderer, export and application sources. Complete source/build trees remain outside
these repository evidence archives.

The five built-in workloads are slope-slide (1,680 particles), falling-block-20 (8,000), two-blocks
(3,456), shallow-tank (3,360) and large-impact (110,592). All final comparisons run five simulated
seconds and sample at 30 Hz, with identical initial particle snapshots and camera/presentation
settings within each scene.

`screen2/` retains the initial three-mode slope screen. Its `paper-baseline` label identifies the
**initial** `epsilon_hat=1` configuration, as recorded in its inputs. `controls/` retains the two
single-mechanism controls: `paper-epsilon20` changes only regularisation, while `paper-pressure001`
changes only artificial pressure from 0.1 to 0.001. The selected mode uses regularisation 20 and full
position corrections. The initial mode and pressure control are rejected; their observations remain.
`screen/` records the first failed provenance-integration attempt.

`validation/` retains all fifteen original kinetic-energy-coloured rendered bundles. The two moving
initial scenes exposed a presentation confound: nominal mass changes kinetic energy in joules even
when initial velocities match. `validation-fixed/` supplies the final fifteen comparisons using
one explicit fixed water-blue colour. Geometry, lighting, renderer and cameras are unchanged;
initial PNGs must now also match exactly. Per-frame snapshot hashes check that recolouring did not
change a trajectory. The final GIFs and contact sheets are composed from these application PNGs.
Animation playback represents simulated time and does not measure live viewer FPS.

## Diagnostics and timing boundaries

`quality/` contains ordinary production checkpoints and independent binary64/current-neighbour
audits for all four smaller scenes, sampled at 0, 0.3, 0.6, 1, 2, 3 and 5 seconds. Separation,
coincident-particle count, density/compression, energy and containment are reported separately.
Binary64 checks of inclined planes may expose rounding-scale residuals even when the binary32
projection satisfies its own contract. No physical-accuracy cutoff selects a numerical mode.

`timing/` runs the ordinary CUDA application at device zero, block size 128, for five simulated
seconds at both requested sizes. Each mode has one complete warmup followed by five samples;
mode order reverses on alternate rounds. Rendering, builds, tests, diagnostic replay and audits
finish or wait outside admitted timing. Solver clocks sum complete accepted calls; process clocks
include startup, output and teardown. The baseline includes XSPH at rest-volume coefficient 0.01;
reference and experimental retain their scene effects. Work counts therefore describe different
numerical policies, not a claim of identical equations per step.

`large-replay/` uses the retained native recorder only for diagnostic samples after ordinary timing.
Its scalar inputs include nominal mass, the omitted unit correction and active effects. Production
endpoint equality is mandatory before admitting any replay diagnostics. Recorder time is never a
production throughput sample. Tool identities and verification readbacks accompany the observations.

The attempted live viewer is retained under `live-viewer/`: it selected the RTX 4070 through Mesa
D3D12, then failed with an X11 connection error before the existing redraw counter could be captured.
There is **no live FPS measurement**. This environment failure was not turned into a solver failure,
and no driver, display service or system setting was changed to work around it.

## Reproduction

These commands start new simulations; use a fresh destination. Build the exact assessed source on
the primary PC with `cargo build --release --all-features` and `MAELSTROM_CUDA_ARCH=89`. From EPQ:

```sh
python3 -m tools.performance.paper_baseline RENDER_ROOT BINARY compile \
  --scene-root Maelstrom/scenes --backend cuda --duration 5 --fixed-colour \
  --scenes slope-slide falling-block-20 two-blocks shallow-tank large-impact
python3 -m tools.performance.paper_baseline TIMING_ROOT BINARY run \
  --scene-root Maelstrom/scenes --backend cuda --duration 5 --pairs 5 \
  --scenes falling-block-20 large-impact
uv run tools/performance/pbf_contract_visual.py RENDER_ROOT slope-slide \
  reference experimental paper-baseline
```

For small-scene diagnostics use the collector's `audit` operation with `--auditor` pointing to the
retained `pbf-frontier-v1/frontier-quality`. For large diagnostics use
`python3 -m tools.performance.paper_baseline_replay CAMPAIGN_ROOT RECORDER AUDITOR` where
`CAMPAIGN_ROOT/timing` contains the ordinary warmup outputs. This reruns recorded inputs for a
checked diagnostic trajectory; it is not simulation resumption.

The raw seal inventories bounded gzip archives by member SHA-256. Verify it with
`python3 tools/performance/frontier_retain.py RETAINED_ROOT --verify`. Build trees, executables,
complete repository exports and Git data are excluded. The retained source patch, file identities,
exact inputs, commands, failed attempts, logs, timings, PNGs and diagnostic observations distinguish
what was actually assessed from the original published method and later calibration.


## Results and verification

The calibrated baseline used 240 Hz, three full passes, regularisation 20 and XSPH 0.01.
Measured paired solver speedups were **3.185× / 2.876×** against reference and
**1.587× / 1.432×** against experimental at 8,000 / 110,592 particles. The
[performance summary](/docs/project/development/milestones/05/assets/paper-baseline-v1/performance-summary.json)
retains all five samples, ranges, paired ratios, process costs, effective inputs and work counts.
All 36 ordinary timing endpoints repeat exactly within their mode/size; reference and experimental
also match the previous campaign's corresponding endpoints byte for byte.

The [quality summary](/docs/project/development/milestones/05/assets/paper-baseline-v1/quality-summary.json)
retains the separate geometry, mean density error, compression and energy observations. All small
scene samples are coincidence-free. Large impact gives peak coincident-particle counts 6 / 7 / 89,
with 4 / 2 / 87 remaining at five seconds. The baseline's full accepted-step maximum speed is
74.800 m/s, against 17.136 / 16.174 for reference / experimental. Its improved bulk compression
does not compensate for the persistent local overlap and high-speed outliers. The selected
calibration is not recommended as the general practical candidate; experimental remains preferred.
No additional parameter search follows this result.

Final animations put reference, experimental and paper baseline left to right:

- [Slope slide](/docs/project/development/milestones/05/assets/paper-baseline-v1/slope-slide-comparison.gif)
- [Falling water](/docs/project/development/milestones/05/assets/paper-baseline-v1/falling-block-20-comparison.gif)
- [Two-block collision](/docs/project/development/milestones/05/assets/paper-baseline-v1/two-blocks-comparison.gif)
- [Shallow settling](/docs/project/development/milestones/05/assets/paper-baseline-v1/shallow-tank-comparison.gif)
- [Large impact](/docs/project/development/milestones/05/assets/paper-baseline-v1/large-impact-comparison.gif)

All fifteen fixed-colour bundles and **2,265 PNG hashes** verified. Initial snapshots, initial images,
cameras and presentation match within each scene. Every corresponding snapshot hash also matches
the earlier energy-coloured run, proving that recolouring did not alter the trajectories.
The native large diagnostic replay matches the production endpoint in all three modes and the
production-rendered snapshot hashes at all **33 half-second observations**. The recorder also
retains a first-step diagnostic sample between the initial and first half-second observation.

The primary-PC full all-feature suite passed **411 tests**, with no ignored cases; the final
CUDA integration suite passed **8 tests**, including the new full-correction/contact oracle and
paper-mode cancellation/rollback/retry. Strict all-feature/all-target release Clippy passed.
The local viewer-feature suite passed **351 tests**, with 16 hardware/platform cases ignored;
a final changed-surface run passed 22 tests with one graphics case ignored.
Ten focused parent Python tests passed, followed by a final two-test replay-input check.
The initial contact-oracle failure and its correction are retained: the old oracle assumed
lattice-calibrated rest density and now derives nominal volume independently for this formulation.
No numerical tolerance was relaxed. The viewer route-equivalence fixture now selects the same
explicit policy on both saved and bundled inputs before comparing provenance.

The assessed Maelstrom base is `f170e9c952c815e2a9e87158c4932bb42ddb465b`; EPQ is
`4fb191deddbd70d130c13ffc50a66abf93b6a7e4`. Neither commit nor the parent gitlink changed.
The measured executable SHA-256 is
`9c258cb80d63eaee1190e07f8cf5c1cb9d1b167b68e0839132c35149142429aa`.
All 13 native production files and all 30 checked CUDA-host/render/export/application files remain
identical to the starting workspace. Source, executable and successful checks are local/primary-PC
evidence; no installed binary replacement, remote publication or hosted validation is claimed.


The completed local raw-seal readback verified **34 archives / 5,644 files**, containing
**1,972,043,466 uncompressed bytes** and **397,033,128 compressed bytes**. The result is retained in
[seal-verification.json](/docs/project/development/milestones/05/assets/paper-baseline-v1/seal-verification.json).
The 220 enumerated source/test input files match the current local checkout; the manifest and
starting-workspace hashes distinguish the new work from pre-existing changes.
