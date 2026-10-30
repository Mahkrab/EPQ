# DFSPH prototype evidence

This directory supports the [bounded assessment](/docs/project/development/milestones/05/dfsph-prototype.md). The decision is NO-GO for production integration of the tested model. It is not a claim that every DFSPH implementation fails.

## Identities and durable storage

Production Maelstrom remained at `250932784790ba26cdc55fc38a877ccefacbf054`; EPQ remained at `814f88a7f4122b1b24ea645b210d89e1200a0c44`. `initial-state.json` records the unrelated work already present. The prototype resides under `Maelstrom/experiments/dfsph`; no production interface, Cargo dependency, numerical default or native optimisation was changed. `native-preservation.json` inventories the 14 unchanged native files.

The complete primary root is `/home/oliver/.local/share/maelstrom-experiments/dfsph-prototype-v1`. Independent reference builds/runs remain at `/home/mahkrab/.local/share/maelstrom-experiments/dfsph-prototype-v1`, using the privately built pinned SPlisHSPlasH dependencies from the preceding frontier study. Neither is temporary storage.

The main seal contains **18,467 files**, **2,893,403,959 uncompressed bytes**, in **44 gzip archives** totalling **2,258,852,644 bytes**. The largest archive is **59,350,803 bytes**. `retained/manifest.json` records every member and archive by size and SHA-256. It includes inputs, raw particle/velocity states, boundary volumes, every step trace and benchmark result, unsuccessful controls, interrupted-run diagnostics, build logs, reference patches and experiment source versions. Build trees and executables remain outside the documentation archive, with their identities and recipes retained.

`reproduction-sources.tar.gz` and its manifest supply the final repository-relative experiment, tooling, test and documentation sources, including the inherited audit/driver templates. The supplement also retains the appended free-domain compression correction under `evidence/`. It complements the numerical-version sources in the main seal. The native implementation is recovered from the pinned Maelstrom commit rather than copied as a repository snapshot.

## What was collected

- `protocol.json`, `policy-design.json`, `wendland-control.json` and `bounded-repair.json` preserve the prospective limits and the single justified extra Jacobi-weight control. No physical criterion changed.
- `quality-results.json` and `physical-results.csv` describe 62 physical CUDA trajectories. Complete per-observation audits and states remain in the main seal.
- `benchmark-results.json` preserves all 24 timing executions: a warmup and five alternating PBF/DFSPH pairs at each of 8,000 and 110,592 particles. These are workload comparisons between physically unqualified policies.
- `pbf-workload-results.json` records source-level row work from a separate native replay whose endpoints match production. Native replay timings are not production throughput evidence.
- `assessment.json` summarises cost, pressure/divergence iterations, logical sweeps, row-entry visits and timestep controls. It does not automatically decide integration.
- `environment.json`, per-run `metrics.json`, `process.json` and build logs identify the primary RTX 4070, tools, binaries, commands and return codes. The reference's CPU clocks are local exploratory observations, not GPU comparators.
- `validation-results.json`, `tool-tests.log` and `combined-tool-tests.log` record five live input rejections, the original six tooling/quadrature tests and the final sixteen combined tests including unbounded-volume and coordinate-range fixtures. Reference/GPU first-step comparisons and the rejected full reference tank are retained under `reference/` in the seal.

The cubic 240 Hz large candidate completed all 1,200 steps. Its exact actual timestep was approximately 0.004166666884 s. The repaired Wendland candidate completed 600 steps at approximately 0.008333333768 s but missed tolerance on 537 steps. The bare Wendland runaway was terminated after its failure was established; its partial final JSONL record is retained and explicitly flagged by the reader. Such records never become physical passes.

Small-scene audits inspect all stored 60 Hz states. For rejected large cases, the audit selects available states within the first ten steps, states aligned to a 0.125-second grid and the final state. The intersection with stored observation cadence gives 0.25-second spacing for the regular 120/240 Hz large runs. These are worst sampled densities, not certified continuous transient maxima. Kinetic energy, residuals, iterations, impulses, contacts and maximum speed are recorded every step.

## Reproduce or inspect

Verify a completed copied seal before reading it:

```sh
python3 tools/performance/frontier_retain.py ROOT/retained --verify
```

The verifier checks archive bytes and every decompressed member. `local-seal-verification.json` records the independent local verification after transfer completion. Extract verified archives only into a new empty directory. This loads saved evidence; it does not continue a simulation.

To start a new run, use the build and invocation in [the prototype README](/Maelstrom/experiments/dfsph/README.md). The seal already supplies ready-to-run `inputs/`, `scenes.json` and `policies.json`; it does not require recovering a temporary input generator. From the parent checkout, the campaign scripts can create fresh runs in a new durable root. Existing output folders are not overwritten.

For an independent audit, build `quality-cubic.cpp` and `quality-wendland.cpp` with C++17/O3. The source supplement also contains their generators and inherited independent reader. Run `python3 dfsph_audit.py ROOT` only after timed work finishes. It retains malformed or truncated trace diagnostics and cannot interpret them as a completed pass. The support-cube volume is a geometric proxy; true mass loss is not inferred from it.

The original free-compression volume was mistakenly clipped to an observation window despite having no physical walls. Preserve those historical diagnostics. Build the two `quality-*-unbounded.cpp` readers supplied in the supplement, run `python3 dfsph_audit.py ROOT --correct-compression`, then `python3 dfsph_assessment.py ROOT --corrected`. They write separate `quality-results-corrected.json`, per-case `quality-corrected.json`, `assessment-corrected.json` and `physical-results-corrected.csv`. No solver state, physical criterion or failed policy outcome is changed. The original window excursions are not physical boundary violations. The source supplement retains both the corrected measurements and the explanation. The exploded bare-Wendland free case exceeds the meaningful volume/grid diagnostic range; those volume values are not interpreted. Its energy failure independently rejects it.

Run the deterministic tool checks with:

```sh
python3 -m unittest tests.performance.test_dfsph -v
```

The standalone figure is reproducible with `uv run tools/performance/dfsph_plot.py ROOT`. It declares its plotting dependency; numerical collection/auditing uses Python's standard library and C++/CUDA.

Reference recipes pin SPlisHSPlasH `7586ffa25948c6ce3bc6c238cda30ad8d35f60a0`, dependency commits, private Eigen 3.3.7, precise harness source and include-only portability repairs. The repaired library changes only the two pressure Jacobi update weights; warmstarts remain unchanged. No global dependency or system setting is required.

## Timing and physical interpretation

Production PBF timings cover its unchanged complete solver calls and compulsory host snapshots. DFSPH covers complete computation, diagnostics, dynamic neighbour storage and 60 Hz host-observation copies. Recording, file output, construction, teardown and independent audits are separate. Timing repeats retain initial/first/final states plus fingerprints of every downloaded observation; qualification retains every sampled state. No performance gain is inferred from a single kernel or from enqueued work.

The paired comparisons ran without concurrent builds, audits or GPU jobs. Some initial exploratory measurements, including the repaired Wendland large run, overlapped independent CPU auditing; they are explicitly excluded from the admitted paired comparison. Their numerical work counts and physical observations remain retained. There was no resampling to make a failed candidate pass.

The benchmark uses identical fluid geometry/count and initial velocities. PBF retains its implicit approximately 0.97% mass-calibration difference and its own pressure formulation; DFSPH uses geometric mass, explicit solid samples and the stated reference conventions. References use actual mass. No accepted configuration of either model exists for an equivalent-physical-accuracy speedup claim. The historical PBF physical data remain in the separately verified [frontier evidence](/docs/project/development/milestones/05/assets/pbf-frontier-v1/README.md); current replay endpoints establish their association with the current PBF benchmark.
