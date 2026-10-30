# Particle-PBF performance and quality evidence

This is the durable evidence for [the frontier assessment](/docs/project/development/milestones/05/performance-frontier.md). It does not change a production default or qualify the experimental solver for adoption.

## Identities and contents

The production source is Maelstrom `250932784790ba26cdc55fc38a877ccefacbf054`; the parent remains `814f88a7f4122b1b24ea645b210d89e1200a0c44`. The initial workspace contained unrelated test relocation and earlier investigations. `initial-state.json` and `preservation.json` record that boundary. The fresh PC build, native replay and experimental device-owner binaries have separate SHA-256 identities in `environment.json`.

- `protocol.json` predates collection. `protocol-amendments.json` records recorder fixes and the existing five-repeat requirement; no physical threshold was relaxed.
- `policies.json`, `scenes.json` and `policy-frontier.csv` expose all four independently controlled quantities and all 18 screen policies.
- `convergence.json` records adjacent timestep controls, iteration controls and empirical cost/density nondominance; it does not promote a Pareto point to physical acceptance.
- `frontier.json` contains 121 independent physical trajectory summaries. Each full observation sequence and production execution record is retained in the archives.
- `residency-results.json` and `sustained-residency-results.json` retain warmups, all five alternating repeats, complete step times, observation costs and endpoint checks.
- `residency-source.patch` is the concrete, isolated Rust experiment. `native-preservation.json` verifies that all 14 native source files match its control. `device-edges.json` records the extra failure/capacity checks.
- `dfsph-summary.json` distinguishes successful unforced-shear probes from the rejected sampled-wall setup. The archives include the failed builds, initial harness failures, corrected source, independent audits and pinned upstream identities. The word `admitted` in those raw filenames refers to executable startup after fixing the harness; it does not mean physical qualification.
- `retained/manifest.json` inventories every raw file and archive by size and SHA-256. The seal has 7,198 files, 1,579,358,820 uncompressed bytes and 26 archives totalling 975,233,705 bytes. No archive exceeds 54,432,093 bytes. `local-seal-verification.json` records verification after copying from the PC.

The raw root remains independently available at `/home/oliver/.local/share/maelstrom-experiments/pbf-frontier-v1` on the primary PC. Its build trees and isolated source exports remain there, outside both repositories. The local exploratory DFSPH root is `/home/mahkrab/.local/share/maelstrom-experiments/pbf-frontier-upstream`. Neither root is temporary storage.

## Reproduce the PBF study

These commands start new isolated simulations. They do not resume any previous simulation. Use a new durable directory on the primary PC, with no concurrent benchmark or build. Obtain the source through `git archive` at the named commit; do not change the existing checkout or parent gitlink.

1. Run `python3 tools/performance/frontier_inputs.py ROOT` from the parent checkout to generate the immutable scene/configuration inputs. Copy those inputs and the frontier campaign/audit scripts to the PC root. Copy `protocol.json` before collection.
2. Export the pinned Maelstrom source into `ROOT/production-source`. Build it with `CARGO_TARGET_DIR=ROOT/target cargo build --locked --release --features cuda`. Preserve stdout/stderr and executable hashes.
3. Copy `frontier_driver.cu` beside the exported `native/kernels.cu`. Build with `nvcc --std=c++17 --ftz=false --prec-div=true --prec-sqrt=true -O3 --gpu-architecture=compute_89 --fmad=false native/frontier_driver.cu -o ROOT/frontier-driver`. Build the independent audit with `c++ -std=c++17 -O3 -Wall -Wextra -Werror frontier_quality.cpp -o ROOT/frontier-quality`.
4. Run `python3 frontier_campaign.py ROOT pilot`, then `screen`. Run `python3 frontier_audit.py ROOT repair`, then `audit` after timing finishes. The repair phase only fills absent warning-completed native trajectories; it does not repeat or replace production timing. Every quality replay must match its corresponding production endpoint.
5. Use `large-selection.json` with the campaign's `large` phase. `python3 frontier_extend.py ROOT extend` creates the named five-second trajectories. The additional `long-large--strong480` uses `run_case` with the existing `dt-0.0020833333333333333` policy and duration 5 seconds. Re-run the independent audit after collection.
6. Copy the pristine source export to `ROOT/residency-source`. Run `python3 frontier_residency.py ROOT/residency-source`; its guard refuses Git checkouts. Build the `frontier_resident` example with the same release/CUDA settings. Run the `resident` and `sustained` phases of `frontier_extend.py`, with all CPU audits/builds finished. The source patch is sufficient to review or reconstruct the exact experiment without modifying production.
7. Copy `frontier_device_edges.rs` into the isolated export's examples, build that example, and supply a decompressed retained production JSON record as its argument. This is a separate validation run, outside the timing campaign.

The CLI always uses schema 2, `--refine-timestep 1` and explicit overrides for timestep, iterations, correction scale and regularisation. The physical-input audit rejects changes to every other resolved numerical/derived value or the initial particle/plane bytes within a scene. The native driver's bounded scratch allocation is only a recorder; its clock is never used as production throughput evidence. The production-derived residency experiment keeps dynamically growing neighbour storage.

## Independent checks and evidence recovery

Run the tool fixtures with `python3 -m unittest tests.performance.test_frontier -v`. Generate the standalone plot with `uv run tools/performance/frontier_plot.py ROOT`; the script declares its plotting dependency. The pressure/volume/energy audits themselves use only Python's standard library and C++17.

Verify a copied seal before using it:

```sh
python3 tools/performance/frontier_retain.py ROOT/retained --verify
```

That command checks both archive bytes and every decompressed member against the manifest. To inspect or re-audit observations, extract the verified archives into a new empty directory. It restores `runs/`, exact inputs, full production JSON gzip files, all sampled particle/velocity states, independent audits, failures, commands, source patches and campaign sources. Extraction loads saved evidence; it does not continue a simulation. Re-audit using the retained scene definitions and `frontier-quality`; the complete reproduction and executable identities remain in the seal.

The DFSPH probe is a separate source-pinned author implementation, using cubic kernels, geometric mass and sampled boundaries. Its build metadata records private Eigen 3.3.7, all dependency commits, compilation commands and two include-only portability repairs. It is not a GPU comparator or a qualified boundary model. Do not use its local four-worker CPU clocks to infer RTX 4070 throughput.
