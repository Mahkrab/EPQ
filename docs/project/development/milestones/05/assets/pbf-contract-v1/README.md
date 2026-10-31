# PBF contract calibration evidence

The [assessment](/docs/project/development/milestones/05/performance-pbf-contract.md) owns the interpretation. `response240` in the raw
case names is the shipped `experimental` policy: 240 Hz, eight passes, correction 0.25, relaxation 20.
`four240` was rejected after the large-scene audit found hundreds of particles with coincident neighbours.
Reference remains the default; fast retains its previous values. The raw primary root is
`/home/oliver/.local/share/maelstrom-experiments/pbf-contract-v1` on `ssh pc`; the local mirror is
`/home/mahkrab/.local/share/maelstrom-experiments/pbf-contract-v1`. The isolated primary executable is
`target/release/maelstrom` inside that root. No installed binary or existing PC checkout was replaced.

## Inputs, source and collection

Maelstrom base: `f170e9c952c815e2a9e87158c4932bb42ddb465b`.
EPQ base: `4fb191deddbd70d130c13ffc50a66abf93b6a7e4`.
`implementation.patch` and `source-manifest.json` identify the local revision; `environment.json`
identifies the measured primary executable, GPU and toolchain. `native-preservation.json` checks all
13 native production files against the initial tree. No CUDA optimisation or kernel was edited.

The scene/configuration/render inputs are retained under `inputs/` in the raw seal. They are the
current built-in slope-slide, falling-block-20, two-blocks, shallow-tank and large-impact scenes.
Counts are 1,680 / 8,000 / 3,456 / 3,360 / 110,592 respectively. These are current built-in workloads;
do not silently combine their clocks with older frontier fixtures or earlier baseline measurements.

`screen3/` contains the seven one-variable controls. `pressure-control/` adds two artificial-pressure
off controls. `validation/` contains the twelve five-second reference/candidate/fast rendered
holdouts. The renders use the application's hardware renderer, identical initial states and cameras,
480×360 pixels and 30 Hz matched simulated observations. The first two attempted screens used a
retained older executable: one could not resolve the new built-in name; the explicit-path attempt
then exposed its missing inclined-plane repair. Both failures remain recorded. All admitted renders
use a fresh build of the current source with its existing contact repair.

`render-summary.json` verifies **25 complete bundles and 3,235 PNG hashes**, matching presentation,
initial image and initial snapshot within each scene. Contact sheets and GIFs load these actual PNGs;
they do not resimulate or reconstruct a surface. GIF playback is approximately real simulated time,
not a live viewer FPS measurement. The slope sheet exposes all seven controls. In the final holdout sheets,
rows are reference, experimental (`response240`), fast. The seal preserves the rejected four-pass frames. See the [falling-water animation](/docs/project/development/milestones/05/assets/pbf-contract-v1/falling-block-20-comparison.gif),
[collision](/docs/project/development/milestones/05/assets/pbf-contract-v1/two-blocks-comparison.gif), [settling](/docs/project/development/milestones/05/assets/pbf-contract-v1/shallow-tank-comparison.gif),
[large impact](/docs/project/development/milestones/05/assets/pbf-contract-v1/large-impact-comparison.gif) and [slope controls](/docs/project/development/milestones/05/assets/pbf-contract-v1/slope-slide-comparison.gif).

`quality/` contains production checkpoint states and independent binary64/current-neighbour audits
at 0, 0.3, 0.6, 1, 2, 3 and 5 seconds for the four smaller scenes. The large brute-force checkpoint
attempt was deliberately terminated and remains a failed attempt. `large-replay/` instead uses the
existing native recorder and independent auditor, with half-second samples and exact endpoint-byte
agreement against the ordinary production warmup. Its verification files hash both retained tools.
Their timings are never throughput evidence. Axis-aligned large-scene contacts are unaffected by
the old recorder's missing inclined-plane repair. No new accuracy threshold decides visual adoption.

`eight-timing/` contains the final eight-pass mode measurements. The earlier `timing/` contains one warmup and five alternating reference/four-pass pairs per requested size,
each running five simulated seconds. No build, test, rendering or independent audit runs alongside
these admitted measurements. The summary files distinguish the rejected four-pass and final eight-pass results and retain individual ordinary solver and complete
CLI clocks; `performance-summary.json` adds paired ratios. Whole CLI timings include startup,
construction, final JSON and teardown. Solver timings sum complete accepted solver calls. The
rendered screen clocks are single observations collected during qualification, with possible test
contention, and cannot support a sustained rendering speedup claim.

## Verification and reproduction

`tests.log` records **405 baseline all-feature tests passed**, including explicitly enabled CUDA and
graphics tests and doctests. `eight-tests.log` records **26 changed-surface tests passed** after
adding the mode, including CLI explicit-policy/replay equivalence, viewer draft resolution and every
CUDA cancellation poll/rollback/retry. `eight-clippy.log` and `eight-build.log` record the final all-feature
release build and strict all-target Clippy. Eight local frontier control/auditor tests also passed.
These are local/primary-PC observations; no hosted checks or publication are claimed.

These commands start new simulations. Use a fresh evidence destination and a release build with
CUDA/render features on the primary PC; keep its exact source and binary identities. From EPQ:

```sh
python3 -m tools.performance.pbf_contract ROOT BINARY compile \
  --scene-root Maelstrom/scenes --backend cuda --duration 3 \
  --policies reference dt-only response240 four240 fast-epsilon20 fast four240-epsilon2
python3 -m tools.performance.pbf_contract TIMING_ROOT BINARY run \
  --scene-root Maelstrom/scenes --backend cuda --duration 5 --pairs 5 \
  --scenes falling-block-20 large-impact --policies reference response240
uv run tools/performance/pbf_contract_visual.py ROOT slope-slide \
  reference dt-only response240 four240 fast-epsilon20 fast four240-epsilon2
```

For smaller-scene diagnostics use the collector's `audit` operation and `--auditor` pointing to the
retained `pbf-frontier-v1/frontier-quality`. For large diagnostics run
`python3 -m tools.performance.pbf_contract_replay CAMPAIGN_ROOT RECORDER AUDITOR` after timing,
where `CAMPAIGN_ROOT/timing` contains the exploratory production controls. Pass `--policies response240`
for the final candidate. Its endpoint is also verified against the final timing repetitions. Use `compile` separately for five-second
holdouts and the two pressure-off controls. The exact executed commands accompany every raw case.

`retained/manifest.json` inventories bounded raw archives with per-file SHA-256 hashes. Verify the
mirrored seal using:

```sh
python3 tools/performance/frontier_retain.py \
  docs/project/development/milestones/05/assets/pbf-contract-v1/retained --verify
```

Build trees, executables and complete source exports stay outside the seal. Source identity, patch,
exact inputs, collection scripts, failed attempts, logs, observations and measured samples remain.

The additional `eight-render/` and `eight-quality/` roots retain the final candidate holdouts and
small-scene audits. `large-replay/response240` reports seven peak particles with coincident neighbours, versus six for
reference and 397 for the rejected four-pass variant. These rare overlaps and severe transient
compression in the densest built-in remain limitations of both reference and the retained option.
The final mode is admitted as reference-like, not as a collapse-free or physically accurate solver.

`initial-seal-verification.json` records an early verification attempt before transfer completed.
The completed-copy readback is recorded separately in `local-seal-verification.json`.

The completed local seal verified all **39 archives / 3,934 files**, with **370,867,020 compressed bytes**.
All 24 final timing endpoints repeated exactly; the large endpoints matched the admitted diagnostic
replays. `endpoint-verification.json` retains the per-run hashes. The final source manifest contains
261 files and was checked against the primary source export.
