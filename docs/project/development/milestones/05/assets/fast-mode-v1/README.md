# Fast-mode integration evidence

The [application assessment](/docs/project/development/milestones/05/performance-fast-mode.md) retains selectable fast/reference modes and recommends keeping the existing default selection. The 5% compression target is diagnostic, not a product veto. The decision weighs sustained application timings and matched physical/rendered improvements and regressions.

## Source and measurement identities

The source base is Maelstrom `250932784790ba26cdc55fc38a877ccefacbf054`. `environment.json` identifies the tested all-features release executable, toolchain, primary RTX 4070 and source-manifest hash. `source-manifest.json` inside the seal inventories the exact isolated source export, including pre-existing test relocation. The implementation patch records application selection, viewer controls and tests; no production solver/native kernel was changed. Documentation can postdate the tested source export without changing its Rust build inputs.

`native-preservation.json` verifies all 13 production native files against the measured baseline. `experimental-policy-identity.json` verifies that **all twelve fresh mode trajectories have identical resolved binary inputs and final states to their corresponding validated experimental policies**. Thus this integrates the demonstrated policy without a new parameter study.

The raw primary root is `/home/oliver/.local/share/maelstrom-experiments/fast-mode-v1` on `ssh pc`. Its `target/release/maelstrom` is the tested CUDA/render/viewer executable; the existing installed executable and PC checkout were not replaced. Local checks and derived images are under `/home/mahkrab/.local/share/maelstrom-experiments/fast-mode-v1-local`. Both repositories' original histories and unrelated work were preserved.

## Reading the evidence

- `performance-summary.json` keeps each same-scene comparison separate, with all individual measured samples, paired ratios and medians. Headless has one warmup plus five alternating pairs per size; compilation has one warmup plus three pairs. Warmups and slow samples remain in the raw seal.
- `physical-comparison.json` joins the six matched physical pairs. Five gravity-driven scenes ran for five seconds; unforced shear ran for 0.2 s. Independent current-neighbour audits and exact native recorder endpoints accompany every fresh production trajectory.
- The original audit's `sampled_gates` and `sampled_practical_pass` fields retain the earlier target descriptions. They are not application adoption decisions. No legacy threshold was weakened to manufacture a pass.
- `render-verification.json` records hardware adapter details, matched camera settings, identical initial images and complete per-frame PNG hashes. All **24 bundles / 5,148 PNGs** passed hash/application validation; every same-mode repeated image sequence matched its warmup exactly.
- PNG contact sheets and GIF comparisons show actual production-renderer output for all six scenes. The two modes share geometry, cameras and simulated observation times. GIFs are playback of saved images, not live viewer performance measurements. Shear plays at approximately quarter speed; other animations approximately match simulated time.
- The raw export profiles separate coordinated solver calls, graphics/readback, hashing, PNG encoding, publication, progress and other work. Their component clocks do not isolate hardware causes. Whole-command wall time also includes work outside the pre-manifest export boundary.
- `parent-baseline-failure.json` reproduces the one legacy profiler-overlay failure against both HEAD and the unchanged working CUDA solver. Full managed parent tests passed 244/245; the error was neither suppressed nor caused by mode integration. The earlier bare-Python missing-SciPy errors are retained separately.

The seal contains **6,635 files**, **1,301,110,346 uncompressed bytes**, and **21 archives totalling 814,198,763 bytes**. The largest archive is 59,018,329 bytes. It contains exact scene/configuration inputs, requests, CLI JSON and stderr, process timers, native states, independent audits, every compiled frame and manifest, all timing profiles, validation results, test/build/lint logs, implementation/source identities and executed campaign modules. Executables, build trees, complete source trees and external links are excluded. The source export remains in the primary durable root; its base commit, patch and per-file manifest distinguish the measured tree.

## Reproduction and verification

These commands start new simulations. Extracting, plotting or playing the stored images loads saved observations and does not continue a simulation. Use a fresh durable root, the current implementation or retained patch, and the previous frontier recorder/audit tools. Do not overwrite either retained campaign or modify repository history.

1. Export the source into `ROOT/source` without `.git` or build outputs. Build there with `CUDA_HOME=/usr/local/cuda CARGO_TARGET_DIR=ROOT/target cargo build --locked --release --all-features`. Keep the source identity and build log. The raw logs record the full all-features release regression with `--include-ignored`, strict Clippy, native ASan/UBSan and exhaustive CUDA power checks before measurement.
2. From the parent checkout run `python3 -m tools.performance.fast_mode ROOT prepare --previous OLD`, where OLD is the intact `pbf-frontier-v1` primary root. This copies immutable scene/configuration inputs and only references the old exact native recorder/audit binaries. `protocol.json` declares the paired collection and practical assessment before timing.
3. Run the `physical` phase, then `headless`, `compiled` and `controls`, with no other campaign GPU work, tests, builds or audits alongside admitted timings. The physical phase invokes the application mode selectors and retains exact quality replays. The timing phases retain ordinary solver and complete application wall clocks separately.
4. Run `audit`, then `assess` using `tools.performance.fast_mode`. Run `python3 -m tools.performance.fast_mode_assessment ROOT` to join matched cases and validate every image/bundle, camera, initial image and repeated same-mode sequence. No timing threshold or physical target automatically chooses adoption.
5. Restore the retained `compiled/` paths and run `uv run tools/performance/fast_mode_visual.py ROOT` for contact sheets, animations and the throughput figure. The executed collection modules are retained under `campaign/tools/performance/`; the root-level early script copy is preparation history, not the collection entry point.

For a new application run, use [the numerical-mode guide](/Maelstrom/docs/usage.md#numerical-modes). To inspect stored compiled output, `maelstrom play BUNDLE` plays its saved PNGs without simulation. Direct CLI/compiled timings are not live-window FPS results.

Verify the mirrored raw seal before reusing it:

```sh
python3 tools/performance/frontier_retain.py \
  docs/project/development/milestones/05/assets/fast-mode-v1/retained --verify
```

`local-seal-verification.json` records archive and member readback after transfer. `tools/performance/fast_mode_retain.py` reconstructs the seal while excluding build artefacts. No hosted verification or publication is claimed.
