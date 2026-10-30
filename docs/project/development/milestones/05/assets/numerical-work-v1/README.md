# Numerical-work comparison evidence

This directory supports the [bounded assessment](/docs/project/development/milestones/05/performance-numerical-work.md). The decision is **NO-GO for practical adoption**, despite a measured 2.28× sustained large-scene speedup for the fastest retained control. No production solver code, defaults, system settings or repository history changed.

## Identities and contents

The measured Maelstrom source is `250932784790ba26cdc55fc38a877ccefacbf054`. The local parent remains `814f88a7f4122b1b24ea645b210d89e1200a0c44`; the PC has a separate parent checkout, identified in `environment.json`. Neither was moved. All 641 inventoried local files matched their initial hashes, including unrelated test relocation and earlier investigations. The inventory was taken after creating the first campaign script. `workspace-preservation.json` retains both local repository states and distinguishes that new script from pre-existing files.

- `matrix-plan.json` names the five previously covered combinations per size and every reused raw trajectory, with production-record and metadata hashes. The [previous frontier seal](/docs/project/development/milestones/05/assets/pbf-frontier-v1/README.md) owns those original observations; they are not duplicated or counted as fresh repeats.
- `protocol.json` and `protocol-amendment.json` record the fixed axes, quality budgets, bounded candidate selection and prospective residual rule. The amendment preceded residual collection.
- `matrix.csv` contains all 24 size/configuration rows. Fresh work counters and production traces cover the complete matrix; original ordinary clocks are reused where available. Device execution under tracing is not an ordinary solver timing.
- `sustained-results.json` retains eight warmup runs and forty measured runs: five alternating pairs for each size/candidate comparison. `assessment.json` contains the four independent paired summaries without pooling their control series.
- `frontier.json` records the 25 fresh physical trajectories, including rejected explosive policies. `workload-results.json`, `trace-results.json` and `residual-results.json` distinguish counted work, traced kernel execution, ordinary solver costs and ideal residual-stopping opportunities.
- `cross-campaign-invariants.json` verifies that all unrelated numerical/derived values and initial particle/plane bytes match the prior campaign for all six scenes.
- `environment.json` records current GPU/toolchain/source identities, executable hashes and byte equality of all 13 production native files. The production CLI and the normal-mode `Simulation` harness are separate identified executables.
- `config-checks.json` and `all-tool-tests.log` retain local CLI-resolution checks and fifteen passing deterministic tooling/oracle/retention tests. Neither is hosted verification or a fresh full Rust/CUDA regression run.
- The PNG/SVG plots are derived locally from the retained data. Particle slices use the same fixed central 0.075 m slab at 0.25, 1 and 5 simulated seconds; they are not a rendering benchmark or proof of physical acceptance.

The raw seal contains **2,036 files**, **1,118,261,853 uncompressed bytes**, and **18 archives totalling 677,180,880 bytes**. The largest archive is 50,194,253 bytes. It includes exact inputs, production JSON, sampled states, independent audits, process records, every timing sample, generated diagnostic source, CUDA reports/SQLite exports, counters, residual CSVs and rejected candidates. Executables, build trees and external directory links are excluded; their identities and governing source commit are recorded instead.

The primary raw/build root is `/home/oliver/.local/share/maelstrom-experiments/numerical-work-v1` on `ssh pc`. Its sealed dependency is the prior `pbf-frontier-v1` root beside it. Local working checks and plot inputs are under `/home/mahkrab/.local/share/maelstrom-experiments/numerical-work-v1-local`. The complete new raw seal is mirrored here; `local-seal-verification.json` records member-by-member verification after transfer.

## Reproduction

These tools start **new simulations**. Extraction and plotting load saved observations and do not continue a simulation. Use a fresh durable root and the pinned source/old evidence; never modify the existing checkout or previous experiment root.

1. Run `python3 -m tools.performance.numerical_work ROOT prepare --previous OLD`, then the `screen` phase. Preparation creates independent scene/configuration files and a reuse plan; it only references the old executable and audit tools.
2. The `candidates` phase reproduces the two explicitly rejected 240 Hz, correction-1/relaxation-0.02 controls. `numerical_work_measure ROOT extend` reproduces five-second half-iteration trajectories and the half-rate large case. The half-rate small-scene five-second trajectories are reused. The additional `shear--half-iterations` request uses the same 480 Hz/four-iteration policy for 0.2 s; its exact production command is retained in the raw process record.
3. Run the `sustained` phase of `tools.performance.numerical_work_measure` with the prior identified `frontier_resident` normal-mode harness available. Finish all builds/audits first. The phase uses the production host-snapshot API, retains all five alternating pairs and checks every endpoint. It does not use the experimental device-owned mode.
4. Build the counter probe from the retained `numerical_work_probe.cu`, or regenerate it with `tools/performance/numerical_work_probe.py` and the existing frontier driver. Include the pinned `production-source/native` directory. Use the retained `nvcc --std=c++17 --ftz=false --prec-div=true --prec-sqrt=true -O3 --gpu-architecture=compute_89 --fmad=false` settings and save the executable as `ROOT/workload-probe`. Only the diagnostic driver changes; production CUDA files are included unchanged.
5. Run `workload`, `residuals` and `traces` phases separately from ordinary timings. The residual phase explicitly labels its oracle estimates; it does not run an adaptive solver. The trace phase runs the production CLI under Nsight Systems and verifies every launch count and endpoint.
6. Run the `audit` phase of `tools.performance.numerical_work`, then `python3 -m tools.performance.numerical_work_assessment ROOT`. The existing binary64/current-neighbour audit supplies physical measurements independently of production kernels. Generate the standalone figures with `uv run tools/performance/numerical_work_plot.py ROOT` after restoring the retained visual inputs.

For direct selectable runs, follow [the controls' instructions](/Maelstrom/experiments/numerical-work/README.md). The files replace the configuration layer and are intended for the declared generated scenes with default physics. On a different scene, preserve its owning physical configuration and use the explicit four numerical overrides from the retained request instead. Keep refinement one and do not interpret CFL warnings as automatic refinement.

Verify a copied seal before using its records:

```sh
python3 tools/performance/frontier_retain.py \
  docs/project/development/milestones/05/assets/numerical-work-v1/retained --verify
```

That checks archive bytes and every decompressed member against `retained/manifest.json`. Extract into a fresh empty directory. The stored normal-mode timing source is already in the previous frontier seal; all new orchestration and generated probe sources are in this one. `tools/performance/numerical_work_retain.py` recreates a seal while excluding binaries and build trees.
